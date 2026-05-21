# Phase 1 — Core Task Manager

## Что сделано

### Backend (`apps/api`)

- **ORM-модели** (SQLAlchemy 2): `User`, `Project`, `Tag`, `Task` + ассоциация
  `task_tags`. Самореференс `parent_id` для subtasks, FK на проект/владельца.
  ENUM статусов (`TaskStatus`), приоритетов (`PriorityBucket`),
  типов источников (`TaskSourceType`) и энергии (`EnergyType`) — все nominal,
  без native PG enum (проще миграции).
- **Alembic-миграция `0001_phase1_core`** создаёт все таблицы Phase 1 с
  индексами на статус/приоритет/owner/project/due_date.
- **Авто-запуск миграций** при старте контейнера (`scripts/entrypoint.sh` ждёт
  Postgres, делает `alembic upgrade head`, опционально сидит данные при
  `SEED_ON_START=1`).
- **Pydantic v2 schemas**: `TaskCreate/Update/Read`, `ProjectCreate/Update/Read`,
  `TagRead/Create`, `Page<T>`, `TaskSnoozeIn`.
- **Repository слой**: `TaskRepository` (CRUD + `complete`/`snooze`/
  `reprioritize_all`, фильтры по статусу, приоритету, проекту, поиску, дедлайну,
  пагинация) и `ProjectRepository`.
- **Prioritization engine** (`app/services/prioritization.py`):
  `priority_score = 0.35*urgency + 0.30*importance + 0.10*(1-effort) +
  0.10*strategic + 0.15*procrastination_recovery`. Маппинг score → bucket
  P0–P4. Перерасчёт через `recompute(task)` дергается при create/update/snooze.
- **Demo user**: single-tenant локальный режим — все запросы атрибутятся
  виртуальному пользователю `you@neuroplan.local` (`get_or_create_default_user`).
  Полная авторизация запланирована позже.
- **REST API v1**:
  - `GET/POST /api/v1/tasks`, `GET/PATCH/DELETE /api/v1/tasks/{id}`,
    `POST /api/v1/tasks/{id}/complete`, `/snooze`, `POST /api/v1/tasks/reprioritize`.
    Фильтры: `status[]`, `priority[]`, `project_id`, `search`, пагинация.
  - `GET/POST /api/v1/projects`, `PATCH/DELETE /api/v1/projects/{id}`.
  - `GET /api/v1/analytics/dashboard` — totals (all/open/overdue/done_today/done_7d)
    + 7-дневная серия завершений.
- **Seed-скрипт** `python -m scripts.seed`: создаёт демо-пользователя,
  3 проекта и 5 типовых задач (deep-work, learning, errand, snoozed/overdue).
- **Тесты** на prioritization engine (`tests/test_prioritization.py`):
  overdue → urgency=1.0, no-due → low, snooze boosts score, bucket assignment.

### Frontend (`apps/web`)

- **AppShell**: `Sidebar` со всей навигацией (Dashboard/Tasks включены,
  остальное помечено фазой), `Topbar` со строкой поиска и live API/DB бейджами.
- **React Query Provider** на `staleTime: 15s`, single shared client.
- **Типизированный API-клиент** `lib/api.ts` (mirrors backend Pydantic) с
  `tasksApi`, `projectsApi`, `analyticsApi`.
- **UI-примитивы**: `Card`/`CardHeader`, анимированный `Stat` с counter-up,
  `Sparkline` (чистый SVG, без recharts на Phase 1).
- **Dashboard** (`/`): 4 KPI карточки (Open / Overdue / Done today / Done 7d),
  блок Top priorities с `NewTaskForm` (быстрый ввод задачи на Enter) и
  7-дневный sparkline по завершениям.
- **Tasks** (`/tasks`): фильтры по статусу (chip-style), быстрый ввод,
  группировка по priority bucket (P0–P4), анимированные строки задач с
  кнопкой complete, due/overdue индикаторами, badge приоритета. Кнопка
  «Recompute priorities» вызывает `POST /tasks/reprioritize`.

## Созданные ключевые файлы

- **Backend models**: `app/models/{enums,user,project,tag,task}.py`,
  `app/models/__init__.py`.
- **Migration**: `alembic/versions/0001_phase1_core.py`.
- **Schemas**: `app/schemas/{common,project,tag,task}.py`.
- **Services**: `app/services/{prioritization,users}.py`.
- **Repositories**: `app/repositories/{tasks,projects}.py`.
- **API**: `app/api/deps.py`, `app/api/v1/{tasks,projects,analytics}.py`,
  обновлён `app/api/v1/__init__.py`.
- **Infra**: `scripts/{wait_for_db,seed}.py`, `scripts/entrypoint.sh`,
  обновлён `Dockerfile`.
- **Tests**: `tests/test_prioritization.py`.
- **Frontend lib**: `lib/api.ts`.
- **Frontend providers/shell**: `components/providers.tsx`,
  `components/shell/{AppShell,Sidebar,Topbar}.tsx`.
- **Frontend UI**: `components/ui/{Card,Stat,Sparkline}.tsx`,
  `components/tasks/{TaskRow,NewTaskForm}.tsx`.
- **Frontend pages**: обновлены `app/layout.tsx`, `app/page.tsx`,
  добавлен `app/tasks/page.tsx`.

## Как запустить

```bash
cd neuroplan
make up                              # build + start
docker compose -f infra/docker/docker-compose.yml exec api \
    python -m scripts.seed           # (опционально) демо-данные
```

Или одним выстрелом с автосидингом:
```bash
SEED_ON_START=1 make up
```

- Web — http://localhost:3000 (Dashboard) и http://localhost:3000/tasks
- API docs — http://localhost:8000/docs
- Тесты backend: `make test`

## Definition of Done — проверка

- [x] Доступен CRUD задач через UI (create/list/complete, фильтры, группировка).
- [x] Есть базовая аналитика (`/api/v1/analytics/dashboard` + 4 KPI + sparkline).
- [x] Prioritization engine реализован и покрыт тестами.
- [x] Миграции и сидинг работают.
- [x] Lint / format проходят (`ruff`, `prettier`).

## Что дальше — Phase 2: Notes ingestion

1. Модели `NoteSource`, `NoteDocument`, `ExtractedEntity` (+ миграция).
2. Local filesystem watcher для Obsidian vault (markdown папка), индексация по
   `checksum`, инкрементальный sync.
3. Markdown-парсер: headings, чекбоксы `- [ ]` / `- [x]`, теги `#tag`,
   wikilinks `[[note]]`, inline-даты, frontmatter YAML.
4. Notes inbox UI: список извлечённых фрагментов, accept/reject (преобразование
   в Task с `source_type=note`).
5. Worker-задача на регулярную синхронизацию vault'а.
6. Тесты парсера на golden-fixtures.
