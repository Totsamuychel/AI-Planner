"""Block until Postgres is reachable, then exit."""

from __future__ import annotations

import sys
import time

import psycopg

from app.core.config import get_settings


def main() -> int:
    settings = get_settings()
    deadline = time.time() + 60
    last_err: Exception | None = None
    
    # psycopg.connect needs 'postgresql://' not 'postgresql+psycopg://'
    url = settings.sync_database_url.replace("+psycopg", "")
    
    while time.time() < deadline:
        try:
            with psycopg.connect(url, connect_timeout=3) as conn:
                conn.execute("SELECT 1")
            print("db ready", flush=True)
            return 0
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1)
    print(f"db not ready: {last_err}", file=sys.stderr, flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
