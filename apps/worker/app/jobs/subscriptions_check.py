"""Worker job — daily subscription reminder dispatch."""

from __future__ import annotations

import os

import httpx
import structlog

log = structlog.get_logger("worker.subscriptions_check")


async def run_subscriptions_check() -> None:
    base = os.getenv("API_INTERNAL_URL", "http://api:8000")
    url = f"{base}/api/v1/subscriptions/dispatch-notifications"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url)
            r.raise_for_status()
            log.info("subscriptions_check.ok", result=r.json())
    except Exception as e:  # noqa: BLE001
        log.warning("subscriptions_check.failed", error=str(e))
