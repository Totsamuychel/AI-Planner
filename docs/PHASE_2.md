# Phase 2 — Notes ingestion

## Что сделано

### Backend
- **Модели** `NoteSource`, `NoteDocument`, `ExtractedEntity` + ENUM-ы
  `NoteSourceType`, `EntityType`, `EntityStatus`. Уникальный индекс
  `(source_id, file_path)` для документов и `(owner_id, dedupe_key)` для
  кандидатов — гарантирует идемпотентность инжеста.
- **Alembic migration `0002_phase2_notes`** добавляет три таблицы и индексы.
- **Markdown / Obsidian parser** (`app/services/notes_parser.py`):
  - YAML frontmatter (через `pyyaml`),
  - headings `# ##`, чекбоксы `- [ ] / - [x]`, теги `#tag`,
    wikilinks `[[note]]`,
  - даты: ISO (`2026-05-25`, `2026-05-25T18:00`), EU (`25.05.2026`),
  - паттерны «due / до / by», эвристическая классификация commitment-фраз
    в TASK / EVENT / LEARNING / IDEA,
  - стабильный `dedupe_key` на основе `path + type + title + line`.
- **Ingest pipeline** (`app/services/notes_ingest.py`):
  - обходит директорию источника, читает `.md/.markdown` ≤ 2 MiB,
  - upsert документов по `(source_id, file_path)` со сравнением SHA-256,
  - материализация кандидатов в `ExtractedEntity` с защитой от дублирования,
  - проверка safe path (защита от path traversal).
- **REST API** `/api/v1/notes`:
  - `GET/POST/DELETE /sources`, `POST /sync`, `POST /sources/{id}/sync`,
  - `GET /documents` (paged),
  - `GET /inbox` с фильтрами по статусу/типу,
  - `POST /inbox/{id}/accept` (промоушн в `Task` с `source_type=note`,
    подтягивание `due_at` из `normalized_data`, recompute приоритета),
  - `POST /inbox/{id}/reject`.
- **Worker job** `notes_sync` — каждые `NOTES_SYNC_SECONDS` (по умолчанию 5 мин)
  дёргает API endpoint `POST /notes/sync` (single source of truth — никаких
  дублей ingest-логики в воркере).
- **Compose**: volume `vault_data:/data/vault` подключен к api и worker.

### Frontend
- Страница **`/inbox`**:
  - управление источниками (add / remove / список с временем последнего
    синка и last_error),
  - кнопка «Sync vault now» (с анимированным spinning icon),
  - чип-фильтр по типу сущности,
  - карточки кандидатов с типом, excerpt, confidence %, due-меткой и
    line number, кнопки **Accept** (промоушн в задачу) и **Reject**
    (с optimistic updates и инвалидацией tasks/analytics),
  - empty state с подсказкой про `/data/vault`.
- Sidebar: пункт «Notes Inbox» активирован.

### Tests
- `tests/test_notes_parser.py`: frontmatter, чекбокс → task с tags + due,
  event-эвристика по headings, learning-классификация, стабильность checksum,
  уникальность dedupe_keys.

## Созданные ключевые файлы

- `apps/api/app/models/notes.py`, обновлён `models/__init__.py`
- `apps/api/alembic/versions/0002_phase2_notes.py`
- `apps/api/app/services/notes_parser.py`, `services/notes_ingest.py`
- `apps/api/app/schemas/notes.py`, `app/api/v1/notes.py`, обновлён `api/v1/__init__.py`
- `apps/api/tests/test_notes_parser.py`
- `apps/api/pyproject.toml` — добавлены `pyyaml`, `watchfiles`
- `apps/worker/app/jobs/notes_sync.py`, обновлён `app/main.py`
- `apps/web/lib/api.ts` (расширен notes API + типы)
- `apps/web/app/inbox/page.tsx`
- `apps/web/components/shell/Sidebar.tsx` — Notes Inbox активирован
- `infra/docker/docker-compose.yml` — volume `vault_data`

## Как запустить

```bash
make up                  # build + start
# скопировать .md в /data/vault через api контейнер
docker compose -f infra/docker/docker-compose.yml exec api bash -c \
    'mkdir -p /data/vault && cat > /data/vault/demo.md <<EOF
---
title: Demo Vault Note
---
# Demo

- [ ] Подготовить план дня #work до 2026-05-22
- [ ] Прочитать главу про LangGraph
- [x] Сделать кофе

## Meeting with PM
Roadmap discussion.
EOF'
```

После этого:
- Открыть http://localhost:3000/inbox
- Добавить source: name=`My Vault`, path=`/data/vault`, type=`obsidian`
- Нажать «Sync vault now»
- В inbox появятся кандидаты — accept нужные

API:
- `POST /api/v1/notes/sources` — добавить источник
- `POST /api/v1/notes/sync` — sync всех
- `GET  /api/v1/notes/inbox` — pending кандидаты
- `POST /api/v1/notes/inbox/{id}/accept` — преобразовать в Task

## Definition of Done

- [x] Заметки индексируются и хранятся (`note_documents`).
- [x] Чекбоксы и ключевые фрагменты попадают в inbox с classifier-эвристикой.
- [x] Accept промотирует кандидата в задачу с правильным `source_type=note`.
- [x] Worker-job делает периодический sync.
- [x] Тесты парсера зелёные.

## Что дальше — Phase 3: AI extraction

1. Подключить AI-провайдер (OpenAI / OpenRouter) через настройки.
2. AI extraction service: structured JSON-схема (см. WORK.md §16) с
   полями `type/title/due_date/importance/confidence/source_excerpt`.
3. Гибрид: heuristic-parser даёт draft → LLM подтверждает/обогащает
   (классификация, дедлайн из NL, теги, importance).
4. Guardrails: log AI output, persist source excerpt, human-in-the-loop
   для confidence < threshold.
5. Background extraction job: при upsert документа поставить в очередь
   запрос на AI-extraction, апдейтнуть `ExtractedEntity` с
   `normalized_data + ai_meta`.
6. Тесты на golden fixtures (note → expected JSON entities).
