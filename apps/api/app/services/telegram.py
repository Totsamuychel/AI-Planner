"""Thin Telegram sender — direct HTTP, no aiogram dependency.

The worker's bot.py handles incoming messages; outgoing system
notifications (subscription reminders, etc.) go through this helper.
"""

from __future__ import annotations

import httpx
import structlog

from app.core.config import get_settings

log = structlog.get_logger("telegram")


async def send_message(chat_id: str, text: str, *, parse_mode: str = "HTML") -> bool:
    settings = get_settings()
    if not settings.telegram_bot_token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, json=payload)
            r.raise_for_status()
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("telegram.send_failed", error=str(e))
        return False
