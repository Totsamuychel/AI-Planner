from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.subscription import BillingPeriod


class SubscriptionBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    amount: float = Field(ge=0)
    currency: str = Field(default="USD", max_length=8)
    billing_period: BillingPeriod = BillingPeriod.MONTHLY
    next_billing_date: date
    notify_days_before: int = Field(default=1, ge=0, le=30)
    active: bool = True
    notes: str = ""


class SubscriptionCreate(SubscriptionBase):
    pass


class SubscriptionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    amount: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=8)
    billing_period: BillingPeriod | None = None
    next_billing_date: date | None = None
    notify_days_before: int | None = Field(default=None, ge=0, le=30)
    active: bool | None = None
    notes: str | None = None


class SubscriptionRead(SubscriptionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    last_notified_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SubscriptionsSummary(BaseModel):
    total_count: int
    active_count: int
    monthly_total: float            # normalized cost per month
    upcoming: list[SubscriptionRead]   # next 7 days, soonest first
