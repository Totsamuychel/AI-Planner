from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.notes import EntityStatus, EntityType, NoteSourceType


class NoteSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    path: str = Field(min_length=1, max_length=1024)
    type: NoteSourceType = NoteSourceType.OBSIDIAN
    sync_interval_seconds: int = Field(default=300, ge=30, le=86400)


class NoteSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    path: str
    type: NoteSourceType
    enabled: bool
    sync_interval_seconds: int
    last_synced_at: datetime | None
    last_error: str | None


class NoteDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    source_id: uuid.UUID
    file_path: str
    title: str
    word_count: int
    indexed_at: datetime | None
    updated_at: datetime


class EntityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    document_id: uuid.UUID
    entity_type: EntityType
    title: str
    content: str
    source_excerpt: str
    source_line: int | None
    normalized_data: dict[str, Any]
    confidence: float
    status: EntityStatus
    promoted_task_id: uuid.UUID | None
    created_at: datetime


class IngestStatsOut(BaseModel):
    files_seen: int
    files_indexed: int
    files_skipped: int
    entities_created: int
    errors: int


class SyncResult(BaseModel):
    sources: dict[str, IngestStatsOut]
