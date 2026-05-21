from typing import Any

from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": "neuroplan-api"}


@router.get("/health/db")
async def health_db() -> dict[str, Any]:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        ok = result.scalar() == 1
    return {"status": "ok" if ok else "fail", "db": "postgres"}
