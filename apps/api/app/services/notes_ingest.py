"""Filesystem → DB ingest pipeline for note sources.

For each enabled source, walks the directory, parses every markdown file,
upserts `NoteDocument` rows by `(source_id, file_path)` and pushes
heuristic candidates into `ExtractedEntity` (dedup by `(owner_id, dedupe_key)`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notes import (
    EntityStatus,
    ExtractedEntity,
    NoteDocument,
    NoteSource,
)
from app.services.ai import get_provider
from app.services.ai.extraction import extract_for_document
from app.services.notes_parser import file_checksum, parse_markdown

log = structlog.get_logger("notes.ingest")

ALLOWED_EXT = {".md", ".markdown"}
MAX_FILE_BYTES = 2 * 1024 * 1024  # skip files > 2 MiB


@dataclass
class IngestStats:
    files_seen: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    entities_created: int = 0
    errors: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "files_seen": self.files_seen,
            "files_indexed": self.files_indexed,
            "files_skipped": self.files_skipped,
            "entities_created": self.entities_created,
            "errors": self.errors,
        }


def _is_safe_path(root: Path, p: Path) -> bool:
    try:
        p.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _iter_markdown(root: Path):
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if Path(name).suffix.lower() not in ALLOWED_EXT:
                continue
            yield Path(dirpath) / name


async def _upsert_document(
    session: AsyncSession,
    source: NoteSource,
    file_path: str,
    text: str,
) -> tuple[NoteDocument, bool]:
    checksum = file_checksum(text)
    existing = (
        await session.execute(
            select(NoteDocument).where(
                NoteDocument.source_id == source.id, NoteDocument.file_path == file_path
            )
        )
    ).scalar_one_or_none()

    parsed = parse_markdown(text, file_path=file_path)

    if existing is None:
        doc = NoteDocument(
            source_id=source.id,
            owner_id=source.owner_id,
            file_path=file_path,
            title=parsed.title or file_path.rsplit("/", 1)[-1],
            raw_text=text,
            checksum=checksum,
            frontmatter=parsed.frontmatter,
            word_count=parsed.word_count,
            indexed_at=datetime.now(tz=UTC),
        )
        session.add(doc)
        await session.flush()
        return doc, True

    if existing.checksum == checksum:
        return existing, False

    existing.raw_text = text
    existing.checksum = checksum
    existing.title = parsed.title or existing.title
    existing.frontmatter = parsed.frontmatter
    existing.word_count = parsed.word_count
    existing.indexed_at = datetime.now(tz=UTC)
    await session.flush()
    return existing, True


async def _materialize_entities(
    session: AsyncSession,
    document: NoteDocument,
    text: str,
) -> int:
    parsed = parse_markdown(text, file_path=document.file_path)
    if not parsed.candidates:
        return 0

    existing_keys = {
        k
        for (k,) in (
            await session.execute(
                select(ExtractedEntity.dedupe_key).where(
                    ExtractedEntity.owner_id == document.owner_id,
                    ExtractedEntity.document_id == document.id,
                )
            )
        )
    }
    created = 0
    for cand in parsed.candidates:
        key = cand.dedupe_key(document.file_path)
        if key in existing_keys:
            continue
        ent = ExtractedEntity(
            owner_id=document.owner_id,
            document_id=document.id,
            entity_type=cand.entity_type,
            title=cand.title,
            content=cand.content,
            source_excerpt=cand.source_excerpt,
            source_line=cand.source_line,
            normalized_data=cand.normalized,
            confidence=cand.confidence,
            status=EntityStatus.PENDING,
            dedupe_key=key,
        )
        session.add(ent)
        existing_keys.add(key)
        created += 1
    await session.flush()
    return created


async def sync_source(session: AsyncSession, source: NoteSource) -> IngestStats:
    stats = IngestStats()
    root = Path(source.path)
    if not root.exists() or not root.is_dir():
        source.last_error = f"path not found: {source.path}"
        source.last_synced_at = datetime.now(tz=UTC)
        return stats

    for fp in _iter_markdown(root):
        stats.files_seen += 1
        if not _is_safe_path(root, fp):
            stats.files_skipped += 1
            continue
        try:
            if fp.stat().st_size > MAX_FILE_BYTES:
                stats.files_skipped += 1
                continue
            text = fp.read_text(encoding="utf-8", errors="replace")
            rel = str(fp.relative_to(root)).replace("\\", "/")
            doc, changed = await _upsert_document(session, source, rel, text)
            if changed:
                stats.files_indexed += 1
                provider = get_provider()
                if provider.name == "null":
                    stats.entities_created += await _materialize_entities(session, doc, text)
                else:
                    res = await extract_for_document(session, doc, provider=provider)
                    stats.entities_created += res.created
        except Exception as exc:  # noqa: BLE001
            log.warning("ingest.file_error", path=str(fp), error=str(exc))
            stats.errors += 1

    source.last_synced_at = datetime.now(tz=UTC)
    source.last_error = None
    log.info("ingest.source_done", source=source.name, **stats.as_dict())
    return stats


async def sync_all_for_owner(session: AsyncSession, owner_id) -> dict[str, IngestStats]:
    rows = (
        await session.execute(
            select(NoteSource).where(NoteSource.owner_id == owner_id, NoteSource.enabled.is_(True))
        )
    ).scalars().all()
    out: dict[str, IngestStats] = {}
    for src in rows:
        out[src.name] = await sync_source(session, src)
    return out


async def accept_entity(session: AsyncSession, entity: ExtractedEntity) -> "Task":  # noqa: F821
    """Promote a pending entity into a real Task and link them."""
    from app.models.enums import TaskSourceType, TaskStatus
    from app.models.task import Task
    from app.services import prioritization

    due_iso = entity.normalized_data.get("due_at") if isinstance(entity.normalized_data, dict) else None
    due_dt: datetime | None = None
    if isinstance(due_iso, str):
        try:
            due_dt = datetime.fromisoformat(due_iso)
        except ValueError:
            due_dt = None

    task = Task(
        owner_id=entity.owner_id,
        title=entity.title,
        description=entity.content or entity.source_excerpt,
        status=TaskStatus.INBOX,
        source_type=TaskSourceType.NOTE,
        source_note_id=entity.document_id,
        due_date=due_dt,
        importance_score=max(0.4, min(1.0, entity.confidence)),
        effort_score=0.5,
    )
    prioritization.recompute(task)
    session.add(task)
    await session.flush()

    entity.status = EntityStatus.ACCEPTED
    entity.promoted_task_id = task.id
    await session.flush()
    return task
