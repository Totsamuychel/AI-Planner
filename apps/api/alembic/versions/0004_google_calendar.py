"""Google Calendar OAuth fields on User.

Revision ID: 0004_google_calendar
Revises: 0003_subscriptions
Create Date: 2026-05-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_google_calendar"
down_revision: str | None = "0003_subscriptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("google_access_token", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("google_refresh_token", sa.Text(), nullable=True))
    op.add_column(
        "users", sa.Column("google_token_expiry", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users",
        sa.Column(
            "google_calendar_id",
            sa.String(255),
            nullable=False,
            server_default="primary",
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "google_calendar_id")
    op.drop_column("users", "google_token_expiry")
    op.drop_column("users", "google_refresh_token")
    op.drop_column("users", "google_access_token")
