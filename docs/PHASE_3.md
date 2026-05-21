# Phase 3 — AI extraction

## Что сделано

### Backend
- **AIProvider abstraction** (`app/services/ai/provider.py`):
  - `ExtractedItem` (Pydantic) — строгая JSON-схема: `type`, `title`,
    `description`, `due_at`, `importance`, `confidence`, `tags`, `source_excerpt`.
  - `AIExtractionResponse` — `items[] + model + used_ai`.
  - `OpenAIProvider` — chat-completions с `response_format=json_object`,
    жёсткий system-prompt («не выдумывай дедлайны», «emit только actionable
    items», «be conservative»). Все ошибки сети/JSON отлавливаются → no-op,
    логируется через structlog.
  - `NullProvider` — graceful fallback при отсутствии `OPENAI_API_KEY`.
  - `get_provider()` выбирает реализацию по `AI_PROVIDER` + `OPENAI_API_KEY`.
- **Hybrid extraction service** (`app/services/ai/extraction.py`):
  1. Heuristic-парсер из Phase 2 даёт draft-кандидатов,
  2. AI получает текст + drafts как `context_hints` и работает как
     re-ranker + enricher,
  3. Merge по нормализованному title (case-insensitive) — AI overrides
     heuristic для пересечений; heuristic-only items сохраняются,
  4. AI-кандидаты помечаются `normalized_data.ai_meta.ai=true` (для audit).
- **Ingest integration**: `sync_source` при изменении файла теперь вызывает
  `extract_for_document(provider=get_provider())`, если provider != null.
  Иначе работает чистая эвристика — никаких регрессий без ключа.
- **REST**:
  - `GET /api/v1/notes/ai/status` — `{provider, enabled}` для UI-индикатора.
  - `POST /api/v1/notes/documents/{id}/extract` — ручной триггер для
    повторной AI-обработки документа.

### Frontend
- **AI status badge** на странице `/inbox`: показывает текущего провайдера
  или подсказку «set OPENAI_API_KEY to enable».
- На карточке inbox entity рядом с confidence/due/line отображается
  бейдж **AI** для кандидатов, которые прошли через LLM.

### Tests
- `tests/test_ai_extraction.py` — `NullProvider` молчит, `ExtractedItem`
  валидирует диапазоны, stub-provider round-trip.

## Созданные / изменённые файлы

- `apps/api/app/services/ai/{__init__,provider,extraction}.py`
- `apps/api/app/services/notes_ingest.py` — интеграция provider
- `apps/api/app/api/v1/notes.py` — endpoints `ai/status` + `documents/{id}/extract`
- `apps/api/tests/test_ai_extraction.py`
- `apps/web/lib/api.ts` — `aiStatus` + типы
- `apps/web/app/inbox/page.tsx` — AI-бейдж и status indicator

## Как включить AI

```
# .env
OPENAI_API_KEY=sk-...
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini   # или gpt-4o
```

После `make up` бейдж в `/inbox` станет зелёным `AI extraction: openai`,
а свежие entities получат бейдж `AI` и обогащённые поля (`due_at`,
`importance`, более чистые `title`).

Без ключа всё работает на heuristic-парсере из Phase 2 — ingest не падает.

## Definition of Done

- [x] AI correctly предлагает задачи/события из заметок при включённом ключе.
- [x] Пользователь может accept/reject в UI (наследуется из Phase 2).
- [x] Guardrails: persisted source_excerpt, ai_meta, structured-output schema,
      conservative system prompt, fail-soft на network/JSON errors.
- [x] Tests на provider abstraction.

## Что дальше — Phase 4: Scheduling

1. Модель/таблица `Event` (если ещё нет дедлайнов в Task — ок, расширим scope).
2. Backend: `POST /schedule/generate` — строит план дня по
   `priority_score + energy_type + estimated_minutes + work_hours`.
3. `POST /schedule/rebalance` — после срыва переноса.
4. Frontend: страница `/calendar` с day-view timeline, slots по часам,
   draggable блоки задач (drag-and-drop через `framer-motion` reorder
   или `dnd-kit`), conflicts highlight, preview напоминаний.
5. Dashboard: schedule timeline widget.
6. Tests на алгоритм планирования (corner cases: переполнение дня, пустой
   план, обязательные fixed events).
