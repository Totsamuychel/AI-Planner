import logging
from datetime import datetime

import structlog

from app.config import get_settings

log = structlog.get_logger("worker.notifications")


async def run_notifications_dispatch() -> None:
    """Cron-job every minute sends ready reminders, marks sent/failed."""
    settings = get_settings()
    log.info("notifications.dispatch.start", at=datetime.utcnow().isoformat())
    
    # In a real implementation:
    # 1. Fetch pending reminders from db where remind_at <= now
    # 2. For each reminder:
    #    - If channel is telegram: send via bot.send_message
    #    - If channel is desktop: post to Redis pub-sub (which api /sse reads) or API webhook
    # 3. Mark status as SENT or FAILED
    
    log.info("notifications.dispatch.done", at=datetime.utcnow().isoformat())
