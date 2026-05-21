# Phase 4 — Scheduling

## Что сделано

### Backend
- **Day planner** (`app/services/scheduler.py`):
  - Greedy packing: задачи отсортированы по `priority_score DESC`,
    при равных — по `due_date`.
  - Длительность блока = clamp(`estimated_minutes`, 15…120; дефолт 30).
  - Зазор `MIN_BREAK_MIN=5` между блоками.
  - Поле `overflow=True` для блоков, выходящих за `work_hours_end`.
  - Guard `DAY_OVERFLOW_GUARD=14` ч — отказ планировать дальше +14 ч от
    начала работы.
- **Persistence**: `generate_for_user` пишет `scheduled_start/_end` в `Task`
  и поднимает `status` с `inbox → planned`.
- **REST `/api/v1/schedule`**:
  - `GET /today` — текущий план (без перестроения).
  - `POST /generate?target_day=YYYY-MM-DD` — собрать план на день.
  - `POST /rebalance` — стереть сегодняшний schedule и пересобрать.
- Возвращаемая модель `DayPlan = {date, blocks[], overflow_count}`.

### Frontend
- **Timeline component** (`components/schedule/Timeline.tsx`):
  - Сетка 6:00 → 23:00 по 56px на час, метки часов слева.
  - Цветовая палитра блоков по приоритету (P0=danger gradient, …).
  - Анимированное появление (Framer Motion, staggered).
  - **Now indicator** — точка + горизонтальная линия на текущем времени.
  - Подсветка overflow-блоков `ring-1 ring-danger/60` + лейбл.
  - Empty state с подсказкой.
- **Страница `/calendar`** (Sidebar активирован):
  - Заголовок с количеством блоков и overflow_count.
  - Кнопки **Generate plan** и **Rebalance** (с инвалидацией `tasks` и
    `schedule`).
- **Dashboard widget** «Today's schedule»: тот же timeline компонент
  в compact-режиме, со ссылкой на полный календарь.

### Tests
- `tests/test_scheduler.py`:
  - empty input → empty plan,
  - сортировка по `priority_score DESC`,
  - последовательная упаковка с 5-минутным break'ом,
  - overflow при коротком work-window,
  - skip для done/archived,
  - default-длительность 30м при отсутствии estimate.

## Файлы

- `apps/api/app/services/scheduler.py`
- `apps/api/app/schemas/schedule.py`
- `apps/api/app/api/v1/schedule.py` + обновлён `api/v1/__init__.py`
- `apps/api/tests/test_scheduler.py`
- `apps/web/lib/api.ts` — `scheduleApi` + типы
- `apps/web/components/schedule/Timeline.tsx`
- `apps/web/app/calendar/page.tsx`
- `apps/web/app/page.tsx` — добавлена секция «Today's schedule»
- `apps/web/components/shell/Sidebar.tsx` — Calendar активирован

## Как пользоваться

```
make up
# Открыть http://localhost:3000/calendar → нажать «Generate plan»
# На /tasks задайте estimated_minutes у задач — это улучшит укладку
```

API:
```
POST /api/v1/schedule/generate           # план на сегодня
POST /api/v1/schedule/generate?target_day=2026-05-23
GET  /api/v1/schedule/today
POST /api/v1/schedule/rebalance
```

## Definition of Done

- [x] Приложение умеет строить реалистичный план дня.
- [x] Frontend показывает timeline с цветами по приоритету и now-indicator.
- [x] Overflow подсвечивается, чтобы пользователь видел перегруз.
- [x] Tests на алгоритм планирования.

## Что дальше — Phase 5: Notifications

1. `Reminder` модель (`entity_type`, `entity_id`, `channel`, `remind_at`,
   `payload_json`, `status`).
2. Telegram bot endpoint (aiogram или raw long-polling) с командами
   `/today /tasks /focus /done /snooze /plan /help`.
3. Notifications scheduler в worker'е: cron-job `every minute` шлёт
   готовые reminders, помечает `sent`/`failed`.
4. Desktop notifications: WebSocket / SSE из API → web push (или просто
   browser Notification API при открытой вкладке).
5. Settings UI: добавление Telegram chat_id, тест-уведомление.
6. Tests: формирование напоминаний, retry-логика.
