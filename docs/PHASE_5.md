# Phase 5 — Notifications

## Что сделано

### Backend Models & Alembic
- Создана модель `Reminder` в `apps/api/app/models/reminder.py`.
- Добавлены новые `Enum` типы: `ReminderStatus` и `ReminderChannel`.
- Выполнена миграция базы данных `alembic revision --autogenerate -m "phase5_reminders"`.
- Добавлен столбец `telegram_chat_id` в модель `User` (`phase5_user_telegram` миграция) для сохранения настроек уведомлений.

### API
- Создан роутер `apps/api/app/api/v1/notifications.py` и `settings.py`.
- Добавлен endpoint `GET /api/v1/notifications/sse` для Server-Sent Events (desktop push).
- Добавлен endpoint `POST /api/v1/notifications/test` для отправки тестовых уведомлений.
- Добавлен endpoint `PATCH /api/v1/settings/telegram` для сохранения `telegram_chat_id`.

### Worker (Telegram Bot & Scheduler)
- Добавлен пакет `aiogram` в `apps/worker/pyproject.toml`.
- Написан бот `apps/worker/app/bot.py`, реализующий команды: `/today`, `/tasks`, `/focus`, `/done`, `/snooze`, `/plan`, `/help`. (Базовая архитектура и ответы-заглушки готовы к расширению).
- Бот запускается асинхронно как background task внутри `apps/worker/app/main.py`.
- Добавлена cron-задача `run_notifications_dispatch` в `apps/worker/app/jobs/notifications_dispatch.py`, срабатывающая каждую минуту.

### Frontend
- Настроена страница **Settings** (`apps/web/app/settings/page.tsx`), позволяющая:
  - Вводить и сохранять `telegram_chat_id`.
  - Отправлять тестовые уведомления как через SSE (Desktop), так и через Telegram.
- Модифицирован `Providers.tsx`, чтобы глобально подключаться к SSE `/api/backend/api/v1/notifications/sse` и выводить `new Notification(...)` при получении сообщения.
- Ссылка Settings активирована в `Sidebar.tsx`.

## Файлы
- `apps/api/app/models/reminder.py`
- `apps/api/app/models/enums.py`
- `apps/api/alembic/versions/*_phase5_reminders.py`
- `apps/api/alembic/versions/*_phase5_user_telegram.py`
- `apps/api/app/api/v1/notifications.py`
- `apps/api/app/api/v1/settings.py`
- `apps/worker/pyproject.toml`
- `apps/worker/app/bot.py`
- `apps/worker/app/main.py`
- `apps/worker/app/jobs/notifications_dispatch.py`
- `apps/web/app/settings/page.tsx`
- `apps/web/components/providers.tsx`
- `apps/web/components/shell/Sidebar.tsx`
- `apps/web/lib/api.ts`

## Как пользоваться
1. Отредактируйте `.env` в корне проекта (копия `.env.example`), добавив `TELEGRAM_BOT_TOKEN`.
2. `make up` или `docker compose -f infra/docker/docker-compose.yml --env-file .env up -d --build`.
3. Откройте `http://localhost:3000/settings`.
4. Введите Chat ID (узнать его можно, написав своему боту).
5. Разрешите уведомления в браузере при нажатии на **Test Desktop Push**. Тестовое сообщение появится в правом нижнем углу экрана (или в системном Notification Center).

## Definition of Done
- [x] `Reminder` модель и миграция.
- [x] Telegram bot endpoint с базовыми командами.
- [x] Notifications scheduler (cron job).
- [x] Desktop notifications via SSE.
- [x] Settings UI для chat_id и test notifications.

## Что дальше — Phase 6: Learning planner
1. `LearningGoal` и `LearningSession` модели.
2. CRUD endpoints для учебных целей.
3. Логика `spaced repetition` для review topics.
4. Learning UI pages: Goals, Topics, Sessions, Progress.
5. Интеграция Learning Goals в Daily Schedule.
