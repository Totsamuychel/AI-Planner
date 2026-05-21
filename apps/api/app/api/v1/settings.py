from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, SessionDep
from app.models.user import User

router = APIRouter(prefix="/settings", tags=["settings"])


class TelegramSettingsUpdate(BaseModel):
    telegram_chat_id: str | None


@router.patch("/telegram")
async def update_telegram_settings(
    settings_in: TelegramSettingsUpdate,
    db: SessionDep,
    user: CurrentUser,
) -> dict[str, Any]:
    user.telegram_chat_id = settings_in.telegram_chat_id
    await db.flush()

    return {"status": "ok", "telegram_chat_id": user.telegram_chat_id}
