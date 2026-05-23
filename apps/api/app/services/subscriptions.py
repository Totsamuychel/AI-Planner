"""Subscription helpers — billing-date math + monthly normalization."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, timedelta

from app.models.subscription import PERIOD_DAYS, BillingPeriod, Subscription


def monthly_cost(sub: Subscription) -> float:
    """Normalize the subscription cost to a monthly figure."""
    amount = float(sub.amount or 0)
    period = sub.billing_period
    if period == BillingPeriod.MONTHLY:
        return amount
    if period == BillingPeriod.YEARLY:
        return amount / 12
    if period == BillingPeriod.QUARTERLY:
        return amount / 3
    if period == BillingPeriod.WEEKLY:
        return amount * 52 / 12
    return amount


def advance_next_billing(sub: Subscription, today: date | None = None) -> bool:
    """Push `next_billing_date` past today if it is in the past.

    Returns True if the date was advanced. The billing period is added
    repeatedly until the next date is in the future, so subscriptions
    that missed a few cycles don't generate stale "today" notifications.
    """
    today = today or date.today()
    step = timedelta(days=PERIOD_DAYS[sub.billing_period])
    moved = False
    while sub.next_billing_date <= today:
        sub.next_billing_date = sub.next_billing_date + step
        moved = True
    return moved


def total_monthly(subs: Sequence[Subscription]) -> float:
    return round(sum(monthly_cost(s) for s in subs if s.active), 2)
