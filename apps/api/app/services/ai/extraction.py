"""Merge heuristic parser output with AI provider output.

Strategy:
1. Run the heuristic parser first — it's deterministic, free and offline.
2. If an AI provider is configured, call it with the note text and pass
   heuristic drafts as `context_hints`. The LLM acts as a *re-ranker /
   enricher*: it can fix titles, lower confidence on noise, attach
   reasonable due dates and importance, or surface items the regex missed.
3. Merge: AI items override heuristic ones with the same normalized title
   (case-insensitive); leftover heuristic items survive as-is.
4. Each materialized `ExtractedEntity` stores `normalized_data.ai_meta`
   when the AI touched it — useful for audit / debugging.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notes import EntityStatus, EntityType, ExtractedEntity, NoteDocument
from app.services.ai.provider import AIProvider, ExtractedItem
from app.services.notes_parser import Candidate, parse_markdown

log = structlog.get_logger("ai.extraction")


@dataclass
class ExtractionResult:
    created: int
    updated: int
    used_ai: bool
    model: str


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def _candidate_from_ai(item: ExtractedItem) -> Candidate:
    try:
        etype = EntityType(item.type)
    except ValueError:
        etype = EntityType.INFO
    norm = {
        "due_at": item.due_at,
        "tags": item.tags,
        "importance": item.importance,
        "ai_meta": {"ai": True},
    }
    return Candidate(
        entity_type=etype,
        title=item.title.strip()[:300],
        content=item.description,
        source_excerpt=item.source_excerpt,
        source_line=None,
        confidence=item.confidence,
        normalized=norm,
    )


def _dedupe_key(doc_path: str, cand: Candidate) -> str:
    raw = f"{doc_path}|{cand.entity_type}|{_norm(cand.title)}|{cand.source_line or ''}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:32]


async def extract_for_document(
    session: AsyncSession,
    document: NoteDocument,
    *,
    provider: AIProvider,
) -> ExtractionResult:
    text = document.raw_text
    parsed = parse_markdown(text, file_path=document.file_path)

    hints: list[dict[str, Any]] = [
        {
            "type": c.entity_type.value,
            "title": c.title,
            "due_at": c.normalized.get("due_at"),
            "confidence": c.confidence,
        }
        for c in parsed.candidates[:40]
    ]
    ai_resp = await provider.extract(text=text, context_hints={"drafts": hints})

    # Merge by normalized title
    merged: dict[str, Candidate] = {}
    for c in parsed.candidates:
        merged[_norm(c.title)] = c
    for item in ai_resp.items:
        ai_c = _candidate_from_ai(item)
        key = _norm(ai_c.title)
        merged[key] = ai_c  # AI wins for same-title overlaps

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
    for cand in merged.values():
        key = _dedupe_key(document.file_path, cand)
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
    log.info(
        "ai.extraction_done",
        doc=document.file_path,
        created=created,
        used_ai=ai_resp.used_ai,
        model=ai_resp.model,
    )
    return ExtractionResult(
        created=created,
        updated=0,
        used_ai=ai_resp.used_ai,
        model=ai_resp.model,
    )
