"""Phase 2 — notes ingestion schema.

Revision ID: 0002_phase2_notes
Revises: 0001_phase1_core
Create Date: 2026-05-21
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2_notes"
down_revision: str | None = "0001_phase1_core"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SOURCE = sa.Enum("obsidian", "markdown_dir", "txt_dir", name="note_source_type", native_enum=False)
ETYPE = sa.Enum(
    "task", "event", "idea", "learning", "reference", "info", "reflection",
    name="entity_type", native_enum=False,
)
ESTATUS = sa.Enum("pending", "accepted", "rejected", "auto", name="entity_status", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "note_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("type", SOURCE, nullable=False, server_default="obsidian"),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sync_interval_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_note_sources_owner_id", "note_sources", ["owner_id"])

    op.create_table(
        "note_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("note_sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("title", sa.String(500), nullable=False, server_default=""),
        sa.Column("raw_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column("frontmatter", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_note_docs_source_id", "note_documents", ["source_id"])
    op.create_index("ix_note_docs_owner_id", "note_documents", ["owner_id"])
    op.create_index("ix_note_docs_checksum", "note_documents", ["checksum"])
    op.create_index("ix_note_docs_source_path", "note_documents", ["source_id", "file_path"], unique=True)

    op.create_table(
        "extracted_entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("note_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", ETYPE, nullable=False, server_default="info"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_excerpt", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_line", sa.Integer(), nullable=True),
        sa.Column("normalized_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("status", ESTATUS, nullable=False, server_default="pending"),
        sa.Column("promoted_task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("dedupe_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_entities_owner_id", "extracted_entities", ["owner_id"])
    op.create_index("ix_entities_status", "extracted_entities", ["status"])
    op.create_index("ix_entities_doc_kind", "extracted_entities", ["document_id", "entity_type"])
    op.create_index("ix_entities_dedupe", "extracted_entities", ["owner_id", "dedupe_key"], unique=True)


def downgrade() -> None:
    op.drop_table("extracted_entities")
    op.drop_table("note_documents")
    op.drop_table("note_sources")
