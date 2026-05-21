# Phase 6 — Learning Planner

## Что сделано

### Backend Models & Alembic
- Создана модель `LearningItem` для учебных целей (с поддержкой статуса, интервального повторения `next_review_at` и прогресса `completed_sessions` / `estimated_sessions`).
- Создана модель `LearningSession` для логирования факта обучения.
- Добавлен `LearningItemStatus` в `enums.py`.
- Связи добавлены в модель `User` (пользователь владеет `learning_items`).
- Сгенерирована и применена миграция `phase6_learning`.

### API
- Создан роутер `learning.py` с эндпоинтами:
  - `GET /api/v1/learning/goals` — список активных целей.
  - `POST /api/v1/learning/goals` — создание новой цели.
  - `PATCH /api/v1/learning/goals/{id}` — обновление цели.
  - `POST /api/v1/learning/goals/{id}/sessions` — логирование сессии и расчет даты следующего повторения (spaced repetition).
  - `GET /api/v1/learning/review` — список целей, которые требуют повторения на сегодняшний день.

### Frontend
- Обновлен клиент `lib/api.ts`, добавлены функции для `learningApi`.
- Создана страница `Learning` (`/learning`), которая отображает:
  - Форму для создания новой цели (название, тема).
  - Блок **Due for Review Today** (если есть цели, подошедшие по времени spaced repetition).
  - Блок **Active Goals** со списком текущих и завершенных целей, отображением прогресса (например, 2 / 5 sessions) и кнопкой **Log Session**.
- Активирован раздел Learning в `Sidebar.tsx`.

## Файлы
- `apps/api/app/models/learning.py`
- `apps/api/app/models/enums.py`
- `apps/api/alembic/versions/*_phase6_learning.py`
- `apps/api/app/api/v1/learning.py`
- `apps/api/app/api/v1/__init__.py`
- `apps/web/app/learning/page.tsx`
- `apps/web/lib/api.ts`
- `apps/web/components/shell/Sidebar.tsx`
- `docs/PHASE_6.md`

## Как пользоваться
1. Запустите проект через `make up` или `docker compose -f infra/docker/docker-compose.yml --env-file .env up -d --build`.
2. Перейдите на `http://localhost:3000/learning`.
3. Создайте новую цель (например, "Learn LangGraph").
4. Нажмите **Log Session**.
5. Цель обновится: увеличится счетчик пройденных сессий, и рассчитается дата следующего повторения (`next_review_at`).
6. Если дата повторения наступила (или меньше текущей), цель появится в специальном блоке **Due for Review Today**.

## Definition of Done
- [x] Модели `LearningGoal` и `LearningSession`.
- [x] CRUD endpoints для учебных целей.
- [x] Простейшая логика `spaced repetition`.
- [x] Пользовательский интерфейс: страница со списком целей, возможность отметить завершение сессии.

## Что дальше — Phase 7: Anti-procrastination
1. Вычисление `procrastination_score` у задач на основе их откладывания.
2. Anti-procrastination nudges (вывод предупреждений на фронте, если задача висит слишком долго).
3. Micro-step suggestions (разбиение задач).
4. Интеграция с Telegram / Notifications для мягких напоминаний вернуть momentum.
