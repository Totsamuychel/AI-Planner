# Phase 7 — Anti-procrastination

## Что сделано

### Backend
- Обновлен алгоритм `PrioritizationService` (`apps/api/app/services/prioritization.py`).
- Добавлена функция `compute_procrastination_score`, которая:
  - Увеличивает `procrastination_score` (от 0.0 до 1.0) на основе `snooze_count` (счетчика откладываний).
  - Увеличивает скор на основе времени, прошедшего с создания задачи (чем дольше висит в бэклоге, тем выше риск).
- Создан AI-сервис `decompose_task` (`apps/api/app/services/ai/decomposition.py`).
- В `tasks.py` добавлен endpoint `POST /tasks/{id}/decompose`, который:
  - Принимает ID зависшей задачи.
  - Обращается к LLM с просьбой разбить её на 2-5 маленьких шагов (micro-steps).
  - Автоматически создает эти подзадачи в базе (с `parent_id` исходной задачи) и возвращает их клиенту.

### Frontend
- Обновлен `TaskRow` (`apps/web/components/tasks/TaskRow.tsx`):
  - При `procrastination_score > 0.3` карточка задачи подсвечивается (предупредительный стиль).
  - Появляется значок "Stuck" (застрявшая задача).
  - Появляется текстовая подсказка (Nudge) и кнопка **AI Micro-steps**, которая вызывает эндпоинт разбиения и инвалидирует список.
- Создан **Focus Mode** (`apps/web/app/focus/page.tsx`):
  - Страница центрирует внимание на одной (самой приоритетной) задаче.
  - Содержит таймер (по умолчанию 25 минут, метод Помодоро).
  - Кнопки для старта таймера и завершения задачи.
  - Если задача имеет высокий `procrastination_score`, Focus Mode выводит поддерживающее сообщение (motivational nudge), предлагая продержаться хотя бы 5 минут для старта.
  - По завершению таймера выдает Desktop Notification об окончании сессии.
- Раздел **Focus Mode** активирован в `Sidebar.tsx`.

## Файлы
- `apps/api/app/services/prioritization.py` (изменён)
- `apps/api/app/services/ai/decomposition.py` (создан)
- `apps/api/app/api/v1/tasks.py` (изменён)
- `apps/web/lib/api.ts` (изменён)
- `apps/web/components/tasks/TaskRow.tsx` (изменён)
- `apps/web/app/focus/page.tsx` (создан)
- `apps/web/components/shell/Sidebar.tsx` (изменён)
- `docs/PHASE_7.md` (создан)

## Как пользоваться
1. Запустите или перезапустите проект: `make up` или `docker compose -f infra/docker/docker-compose.yml --env-file .env up -d --build`.
2. Перейдите на `http://localhost:3000/tasks`.
3. Если у вас есть старые задачи или задачи, которые много раз откладывались (можно сэмулировать, увеличив счетчик откладывания, или если `created_at` задачи старше пары дней), они будут подсвечены как "Stuck".
4. Нажмите **AI Micro-steps** в карточке застрявшей задачи. Система создаст вложенные подзадачи для лёгкого старта.
5. Перейдите в **Focus Mode** (боковое меню), чтобы сфокусироваться на главной задаче с использованием встроенного таймера.

## Definition of Done
- [x] Вычисление `procrastination_score` у задач на основе их откладывания.
- [x] Anti-procrastination nudges (предупреждения на UI).
- [x] Micro-step suggestions (разбиение задач через AI).
- [x] Интеграция Focus Mode для возврата состояния "momentum".

## Что дальше — Phase 8: Polish
1. Добавление недостающих анимаций (motion polish) и пустых состояний.
2. Analytics Charts (прогресс, тренды, распределение по приоритетам).
3. Добавление Onboarding.
4. Оптимизация производительности и доступности (Accessibility).
