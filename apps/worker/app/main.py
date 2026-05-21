"""Background worker entrypoint.

In Phase 0 the worker just runs a heartbeat job to prove the schedule
loop is wired up. Real jobs (notes sync, reminders dispatch, analytics
snapshots, AI extraction) get registered in later phases.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys
from datetime import datetime

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=False),
        ]
    )


log = structlog.get_logger("worker")


async def heartbeat() -> None:
    log.info("worker.heartbeat", at=datetime.utcnow().isoformat())


async def run() -> None:
    _configure_logging()
    settings = get_settings()
    log.info("worker.startup", env=settings.env)

    scheduler = AsyncIOScheduler(timezone=settings.tz)
    scheduler.add_job(heartbeat, "interval", seconds=30, id="heartbeat", replace_existing=True)
    scheduler.start()

    stop = asyncio.Event()

    def _shutdown(*_: object) -> None:
        log.info("worker.signal", action="shutdown")
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _shutdown)
        except NotImplementedError:
            # Windows fallback
            signal.signal(sig, _shutdown)

    await stop.wait()
    scheduler.shutdown(wait=False)
    log.info("worker.shutdown")


if __name__ == "__main__":
    asyncio.run(run())
