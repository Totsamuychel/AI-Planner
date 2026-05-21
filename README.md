# AI Planner

AI-powered personal productivity OS: dashboard, Obsidian/notes ingestion,
AI task extraction, day planner, Telegram + desktop reminders, learning
planner and anti-procrastination engine.

> Status: **Phase 0** — bootstrap complete. See [`docs/PHASE_0.md`](docs/PHASE_0.md)
> for the changelog and roadmap.

## Stack

- **Frontend** — Next.js 15, React 19, TypeScript, Tailwind, shadcn-style UI, Framer Motion.
- **Backend** — Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2.
- **Worker** — APScheduler-based background loop.
- **Data** — PostgreSQL 16, Redis 7, pgvector (added in later phases).
- **Infra** — Docker Compose, GitHub Actions CI.

## Repo layout

```
neuroplan/
  apps/
    api/        FastAPI backend
    web/        Next.js dashboard
    worker/     Background jobs / schedulers
  packages/
    types/      Shared TS types
    config/     Shared config helpers
    ui/         Shared UI primitives
  infra/
    docker/     docker-compose.yml
    nginx/      Reverse proxy (optional, later phase)
  docs/         Phase docs / architecture
  scripts/      Dev scripts
  output/       Local outputs / generated data
```

## Quick start

```bash
cp .env.example .env
make up         # builds and runs api + web + worker + postgres + redis
```

Then:

- Web — http://localhost:3000
- API — http://localhost:8000 (OpenAPI at `/docs`)
- API health — http://localhost:8000/api/v1/health

Stop with `make down`.

## Local dev (without Docker)

```bash
# Backend
cd apps/api
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate
pip install -e .[dev]
uvicorn app.main:app --reload

# Frontend
cd apps/web
pnpm install
pnpm dev
```

## Make targets

| target          | what                                          |
|-----------------|-----------------------------------------------|
| `make up`       | build + start all services                    |
| `make down`     | stop services                                 |
| `make logs`     | tail logs                                     |
| `make api-sh`   | shell into the api container                  |
| `make migrate`  | run Alembic migrations                        |
| `make test`     | run backend tests                             |
| `make lint`     | ruff + mypy + eslint                          |
| `make fmt`      | ruff format + prettier                        |

## Phases

See [`WORK.md`](../WORK.md) for the full spec. Implementation follows the
phase plan strictly — current progress in `docs/`.

- [x] Phase 0 — bootstrap
- [ ] Phase 1 — core task manager
- [ ] Phase 2 — notes ingestion
- [ ] Phase 3 — AI extraction
- [ ] Phase 4 — scheduling
- [ ] Phase 5 — notifications (Telegram + desktop)
- [ ] Phase 6 — learning planner
- [ ] Phase 7 — anti-procrastination
- [ ] Phase 8 — polish
