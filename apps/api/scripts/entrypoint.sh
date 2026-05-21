#!/usr/bin/env bash
set -euo pipefail

python -m scripts.wait_for_db
alembic upgrade head

if [[ "${SEED_ON_START:-0}" == "1" ]]; then
    python -m scripts.seed || true
fi

exec uvicorn app.main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}" --reload
