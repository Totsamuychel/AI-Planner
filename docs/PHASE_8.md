# Phase 8 — Polish & Analytics

## Что сделано

### Backend
- В `apps/api/app/api/v1/analytics.py` реализован полноценный подсчет метрик (aggregations):
  - `totals`: количество всех задач, открытых (open), просроченных (overdue), завершенных сегодня (completed_today) и за последние 7 дней (completed_7d).
  - `completion_7d`: временной ряд, показывающий количество закрытых задач по дням (для построения графиков).

### Frontend
- **Onboarding Modal**: Создан красивый приветственный экран (`apps/web/components/shell/Onboarding.tsx`) для новых пользователей. Он использует `localStorage` и `framer-motion` для плавного появления при первом входе.
- **Analytics Page**:
  - Создана новая страница `/analytics` (`apps/web/app/analytics/page.tsx`).
  - Подключена библиотека `recharts` для рендеринга профессиональных графиков (AreaChart для Task Completion Trend).
  - Сверстаны KPI-карточки (Stat Cards) с декоративными свечениями (Glows), отображающие статусы задач, просрочки и завершенные планы.
- **Dashboard Polish**: 
  - Главная страница (`/`) теперь берет реальные данные с `analyticsApi`.
  - Модернизированы счетчики (Stat) и виджет `Sparkline`, который теперь корректно отображает недельный прогресс по задачам.
  - Sidebar обновлен, чтобы указывать, что активна Phase 8 (Polish).
- Исправлены проблемы с `date-fns` и `recharts`, которые добавлены в `package.json`.

## Файлы
- `apps/api/app/api/v1/analytics.py` (завершено)
- `apps/web/package.json` (добавлены `recharts`, `date-fns`)
- `apps/web/app/analytics/page.tsx` (создан)
- `apps/web/app/layout.tsx` (интегрирован Onboarding)
- `apps/web/components/shell/Onboarding.tsx` (создан)
- `apps/web/components/shell/Sidebar.tsx` (изменён)
- `docs/PHASE_8.md` (создан)

## Как пользоваться
1. Перезапустите контейнеры, чтобы обновить зависимости фронтенда (recharts, date-fns):
   ```bash
   docker compose -f infra/docker/docker-compose.yml --env-file .env up -d --build
   ```
2. При первом открытии веб-версии вы увидите **Onboarding Modal**.
3. На главной странице (`/`) виджеты теперь показывают ваши настоящие данные о задачах.
4. Перейдите во вкладку `/analytics`, чтобы посмотреть агрегированную статистику и интерактивный график за неделю.

## Definition of Done
- [x] Полноценная статистика и Analytics Charts.
- [x] Onboarding для новых пользователей.
- [x] Motion polish & UI upgrades.
- [x] Отполированный Dashboard.

---

**Поздравляю! Все 8 фаз из спецификации `WORK.md` успешно реализованы.** 🎉
Проект NeuroPlan построен и готов к полноценному использованию.