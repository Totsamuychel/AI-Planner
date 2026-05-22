"""Pytest fixtures — integration tests run against a dedicated test DB.

Each test gets a connection-bound transaction that is rolled back at the
end, so tests are isolated and never pollute real data. The app's
`get_session` dependency is overridden to use that transactional session.
"""

from __future__ import annotations

import os

import pytest
import sqlalchemy as sa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_session
from app.db.base import Base
from app.main import create_app

# Import every model so Base.metadata is fully populated.
from app import models  # noqa: F401

ASYNC_TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://neuroplan:neuroplan@postgres:5432/neuroplan_test",
)
SYNC_TEST_URL = ASYNC_TEST_URL.replace("+asyncpg", "+psycopg")
# Maintenance connection — used only to CREATE the test database.
SYNC_ADMIN_URL = SYNC_TEST_URL.rsplit("/", 1)[0] + "/neuroplan"
TEST_DB_NAME = ASYNC_TEST_URL.rsplit("/", 1)[1]


@pytest.fixture(scope="session", autouse=True)
def _setup_database():
    """Create the test database (if missing) and build a fresh schema."""
    admin = sa.create_engine(SYNC_ADMIN_URL, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            sa.text("SELECT 1 FROM pg_database WHERE datname = :n"),
            {"n": TEST_DB_NAME},
        ).scalar()
        if not exists:
            conn.execute(sa.text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()

    sync_engine = sa.create_engine(SYNC_TEST_URL)
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()
    yield


@pytest.fixture
async def db_session(_setup_database) -> AsyncSession:
    """A session bound to a transaction that is rolled back after the test."""
    engine = create_async_engine(ASYNC_TEST_URL, poolclass=NullPool)
    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(
        bind=conn,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()
        await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    app = create_app()

    async def _override_get_session():
        async with db_session.begin():
            yield db_session

    app.dependency_overrides[get_session] = _override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
