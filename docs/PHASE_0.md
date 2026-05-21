# Phase 0 — Bootstrap

## Что сделано

- Создана monorepo-структура с apps/web, apps/api, apps/worker и packages/*.
- Поднята общая инфраструктура: PostgreSQL 16, Redis 7, FastAPI, Next.js 15,
  APScheduler-воркер — всё запускается одной командой через
  `docker compose`.
- Базовый FastAPI с `/`, `/api/v1/health` и `/api/v1/health/db` (проверка БД),
  CORS, structlog-логированием, ORJSON-ответами и `lifespan`-инициализацией.
- SQLAlchemy 2 (async) + Alembic-каркас (миграции пока пустые — модели появятся
  в Phase 1).
- Базовый pytest-набор для backend (`/` и `/health`).
- Next.js 15 (React 19, TypeScript strict, Tailwind, dark-first дизайн-токены).
  Главная страница показывает roadmap и live-статус API + DB через
  `StatusBadge`-компонент.
- Worker с APScheduler-heartbeat (готов принимать реальные джобы в Phase 5+).
- Shared packages `@neuroplan/types`, `@neuroplan/config`, `@neuroplan/ui`
  (заглушки для общих контрактов и UI-примитивов).
- DevX: Makefile, `.env.example`, `.editorconfig`, `.prettierrc`,
  pre-commit (ruff + prettier + house-keeping), GitHub Actions CI
  (api: ruff + pytest, web: typecheck + lint + build).

## Структура

```
neuroplan/
├── apps/
│   ├── api/        FastAPI, SQLAlchemy 2, Alembic, pytest
│   ├── web/        Next.js 15 + Tailwind + TS strict
│   └── worker/     APScheduler-loop
├── packages/
│   ├── types/      Cross-package TS types
│   ├── config/     Shared TS config
│   └── ui/         Design-system primitives (stub)
├── infra/
│   ├── docker/     docker-compose.yml
│   └── nginx/      Reverse proxy (optional, не используется в Phase 0)
├── docs/PHASE_0.md
├── .github/workflows/ci.yml
├── Makefile
├── package.json + pnpm-workspace.yaml
├── pyproject.toml внутри apps/api и apps/worker
└── README.md
```

## Созданные ключевые файлы

- `Makefile`, `package.json`, `pnpm-workspace.yaml`, `.env.example`,
  `.gitignore`, `.editorconfig`, `.prettierrc.json`, `.pre-commit-config.yaml`,
  `README.md`
- `apps/api/pyproject.toml`, `apps/api/Dockerfile`, `apps/api/alembic.ini`,
  `apps/api/alembic/env.py`, `apps/api/alembic/script.py.mako`
- `apps/api/app/main.py`, `app/api/v1/health.py`,
  `app/core/config.py`, `app/core/logging.py`,
  `app/db/base.py`, `app/db/session.py`
- `apps/api/tests/conftest.py`, `tests/test_health.py`
- `apps/web/package.json`, `next.config.mjs`, `tailwind.config.ts`,
  `tsconfig.json`, `postcss.config.mjs`, `Dockerfile`,
  `app/layout.tsx`, `app/page.tsx`, `app/globals.css`,
  `components/StatusBadge.tsx`, `lib/cn.ts`
- `apps/worker/pyproject.toml`, `Dockerfile`, `app/main.py`, `app/config.py`
- `packages/{types,config,ui}/src/index.ts` + package.json
- `infra/docker/docker-compose.yml`, `infra/nginx/nginx.conf`
- `.github/workflows/ci.yml`

## Как запустить

```bash
cd neuroplan
cp .env.example .env
make up           # сборка + старт всех сервисов
```

После старта:

- Web — http://localhost:3000 (увидите roadmap + два зелёных бейджа API/DB)
- API — http://localhost:8000  (OpenAPI: http://localhost:8000/docs)
- API health — http://localhost:8000/api/v1/health
- API DB ping — http://localhost:8000/api/v1/health/db
- PostgreSQL — localhost:5432 (neuroplan/neuroplan/neuroplan)
- Redis — localhost:6379

Запустить тесты backend:

```bash
make test
```

## Definition of Done — проверка

- [x] Проект запускается одной командой (`make up`).
- [x] Web и API доступны локально (3000 / 8000).
- [x] База поднимается в Docker и доступна api/worker'у.
- [x] Базовые тесты есть и проходят (`pytest`).
- [x] Lint + CI настроены.

## Что дальше — Phase 1: Core Task Manager

1. Доменные модели и Alembic-миграции: `User`, `Project`, `Task`,
   `Subtask`, `Tag`, ENUM статусов и приоритетов.
2. Repository + service слои для Task / Project.
3. REST API: `/tasks` CRUD, `complete`, `snooze`, `reprioritize`, фильтры,
   `/projects` CRUD.
4. Pydantic-schemas (request/response), пагинация, сортировка.
5. Pytest-coverage для CRUD и базовой логики приоритизации.
6. Frontend: страницы Dashboard / Tasks с list + kanban + priority view,
   React Query, optimistic updates, drag-and-drop, командная палитра (cmd+k),
   skeletons.
7. Базовые dashboard-карточки: today summary, top priorities, KPI.
8. Seed-скрипт с демо-данными.
