from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class BillingPeriod(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"
    WEEKLY = "weekly"
    QUARTERLY = "quarterly"


PERIOD_DAYS: dict[BillingPeriod, int] = {
    BillingPeriod.WEEKLY: 7,
    BillingPeriod.MONTHLY: 30,
    BillingPeriod.QUARTERLY: 91,
    BillingPeriod.YEARLY: 365,
}


class Subscription(Base, TimestampMixin):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    billing_period: Mapped[BillingPeriod] = mapped_column(
        Enum(BillingPeriod, name="billing_period", native_enum=False),
        nullable=False,
        default=BillingPeriod.MONTHLY,
    )
    next_billing_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    notify_days_before: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    last_notified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Subscription {self.name!r} next={self.next_billing_date}>"
