from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class NoteSourceType(StrEnum):
    OBSIDIAN = "obsidian"
    MARKDOWN_DIR = "markdown_dir"
    TXT_DIR = "txt_dir"


class EntityType(StrEnum):
    TASK = "task"
    EVENT = "event"
    IDEA = "idea"
    LEARNING = "learning"
    REFERENCE = "reference"
    INFO = "info"
    REFLECTION = "reflection"


class EntityStatus(StrEnum):
    PENDING = "pending"      # awaits user review
    ACCEPTED = "accepted"    # promoted to Task/Event
    REJECTED = "rejected"
    AUTO = "auto"            # auto-accepted (high confidence)


class NoteSource(Base, TimestampMixin):
    __tablename__ = "note_sources"

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    type: Mapped[NoteSourceType] = mapped_column(
        Enum(NoteSourceType, name="note_source_type", native_enum=False),
        nullable=False,
        default=NoteSourceType.OBSIDIAN,
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    enabled: Mapped[bool] = mapped_column(default=True, nullable=False)
    sync_interval_seconds: Mapped[int] = mapped_column(Integer, default=300, nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents: Mapped[list["NoteDocument"]] = relationship(
        "NoteDocument", back_populates="source", cascade="all,delete-orphan"
    )


class NoteDocument(Base, TimestampMixin):
    __tablename__ = "note_documents"
    __table_args__ = (Index("ix_note_docs_source_path", "source_id", "file_path", unique=True),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("note_sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    raw_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    frontmatter: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    source: Mapped["NoteSource"] = relationship("NoteSource", back_populates="documents")
    entities: Mapped[list["ExtractedEntity"]] = relationship(
        "ExtractedEntity", back_populates="document", cascade="all,delete-orphan"
    )


class ExtractedEntity(Base, TimestampMixin):
    __tablename__ = "extracted_entities"
    __table_args__ = (
        Index("ix_entities_doc_kind", "document_id", "entity_type"),
        Index("ix_entities_dedupe", "owner_id", "dedupe_key", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("note_documents.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(EntityType, name="entity_type", native_enum=False), nullable=False, default=EntityType.INFO
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    normalized_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    status: Mapped[EntityStatus] = mapped_column(
        Enum(EntityStatus, name="entity_status", native_enum=False),
        nullable=False,
        default=EntityStatus.PENDING,
        index=True,
    )
    promoted_task_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)

    document: Mapped["NoteDocument"] = relationship("NoteDocument", back_populates="entities")
