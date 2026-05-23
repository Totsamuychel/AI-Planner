"""Subscriptions tracker.

Revision ID: 0003_subscriptions
Revises: 7ae2a4590a37
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_subscriptions"
down_revision: str | None = "7ae2a4590a37"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PERIOD = sa.Enum(
    "monthly", "yearly", "weekly", "quarterly",
    name="billing_period", native_enum=False,
)


def upgrade() -> None:
    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(8), nullable=False, server_default="USD"),
        sa.Column("billing_period", PERIOD, nullable=False, server_default="monthly"),
        sa.Column("next_billing_date", sa.Date(), nullable=False),
        sa.Column("notify_days_before", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.String(500), nullable=False, server_default=""),
        sa.Column("last_notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_subscriptions_owner_id", "subscriptions", ["owner_id"])
    op.create_index("ix_subscriptions_next_billing_date", "subscriptions", ["next_billing_date"])


def downgrade() -> None:
    op.drop_table("subscriptions")
