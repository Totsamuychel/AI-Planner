"""Worker job — triggers /api/v1/notes/sync periodically.

The worker keeps its own scheduler thin: it calls into the API
instead of duplicating ingest logic. This keeps a single source
of truth and avoids competing DB sessions.
"""

from __future__ import annotations

import os

import httpx
import structlog

log = structlog.get_logger("worker.notes_sync")


async def run_notes_sync() -> None:
    base = os.getenv("API_INTERNAL_URL", "http://api:8000")
    url = f"{base}/api/v1/notes/sync"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(url)
            r.raise_for_status()
            log.info("notes_sync.ok", sources=r.json().get("sources", {}))
    except Exception as e:  # noqa: BLE001
        log.warning("notes_sync.failed", error=str(e))
