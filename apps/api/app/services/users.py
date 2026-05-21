"""Phase 1 ships a single demo user (single-tenant local app).
Full auth lands in a later phase; for now the API resolves
the current user via this helper.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

DEMO_EMAIL = "you@neuroplan.local"
DEMO_NAME = "You"


async def get_or_create_default_user(session: AsyncSession) -> User:
    res = await session.execute(select(User).where(User.email == DEMO_EMAIL))
    user = res.scalar_one_or_none()
    if user is not None:
        return user
    user = User(email=DEMO_EMAIL, name=DEMO_NAME)
    session.add(user)
    await session.flush()
    return user
