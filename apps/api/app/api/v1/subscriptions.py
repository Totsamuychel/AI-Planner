from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, SessionDep
from app.db.session import SessionLocal
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionRead,
    SubscriptionsSummary,
    SubscriptionUpdate,
)
from app.services.subscriptions import advance_next_billing, total_monthly
from app.services.telegram import send_message

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("", response_model=list[SubscriptionRead])
async def list_subs(user: CurrentUser, session: SessionDep) -> list[SubscriptionRead]:
    rows = (
        await session.execute(
            select(Subscription)
            .where(Subscription.owner_id == user.id)
            .order_by(Subscription.next_billing_date.asc())
        )
    ).scalars().all()
    return [SubscriptionRead.model_validate(s) for s in rows]


@router.get("/summary", response_model=SubscriptionsSummary)
async def summary(user: CurrentUser, session: SessionDep) -> SubscriptionsSummary:
    rows = (
        await session.execute(
            select(Subscription)
            .where(Subscription.owner_id == user.id)
            .order_by(Subscription.next_billing_date.asc())
        )
    ).scalars().all()
    horizon = date.today() + timedelta(days=7)
    upcoming = [s for s in rows if s.active and s.next_billing_date <= horizon]
    return SubscriptionsSummary(
        total_count=len(rows),
        active_count=sum(1 for s in rows if s.active),
        monthly_total=total_monthly(rows),
        upcoming=[SubscriptionRead.model_validate(s) for s in upcoming],
    )


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
async def create_sub(
    payload: SubscriptionCreate, user: CurrentUser, session: SessionDep
) -> SubscriptionRead:
    sub = Subscription(owner_id=user.id, **payload.model_dump())
    session.add(sub)
    await session.flush()
    return SubscriptionRead.model_validate(sub)


async def _get(session: SessionDep, user_id: uuid.UUID, sub_id: uuid.UUID) -> Subscription:
    sub = (
        await session.execute(
            select(Subscription).where(
                Subscription.id == sub_id, Subscription.owner_id == user_id
            )
        )
    ).scalar_one_or_none()
    if sub is None:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub


@router.patch("/{sub_id}", response_model=SubscriptionRead)
async def update_sub(
    sub_id: uuid.UUID,
    payload: SubscriptionUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> SubscriptionRead:
    sub = await _get(session, user.id, sub_id)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(sub, k, v)
    await session.flush()
    return SubscriptionRead.model_validate(sub)


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sub(sub_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    sub = await _get(session, user.id, sub_id)
    await session.delete(sub)


@router.post("/dispatch-notifications")
async def dispatch_notifications() -> dict[str, int]:
    """Worker-facing endpoint: send Telegram reminders for upcoming renewals.

    For each active subscription whose `next_billing_date` falls within
    `notify_days_before`, send the user's Telegram chat one message —
    but only if we have not already notified in the last 20 hours.
    Past-due dates are advanced after sending.
    """
    today = date.today()
    now = datetime.now(tz=UTC)
    sent = 0
    advanced = 0
    async with SessionLocal() as session:
        async with session.begin():
            rows = (
                await session.execute(
                    select(Subscription, User)
                    .join(User, User.id == Subscription.owner_id)
                    .where(Subscription.active.is_(True))
                )
            ).all()
            for sub, user in rows:
                days_until = (sub.next_billing_date - today).days
                if days_until > sub.notify_days_before:
                    continue
                if days_until < 0:
                    # Bill already passed — advance and skip notification.
                    if advance_next_billing(sub, today):
                        advanced += 1
                    continue
                already = (
                    sub.last_notified_at is not None
                    and (now - sub.last_notified_at) < timedelta(hours=20)
                )
                if already or not getattr(user, "telegram_chat_id", None):
                    continue
                when = "сегодня" if days_until == 0 else f"через {days_until} дн."
                text = (
                    f"💳 <b>Подписка: {sub.name}</b>\n"
                    f"Оплата {when} ({sub.next_billing_date.isoformat()}) "
                    f"— {sub.amount} {sub.currency}."
                )
                ok = await send_message(user.telegram_chat_id, text)
                if ok:
                    sub.last_notified_at = now
                    sent += 1
    return {"sent": sent, "advanced": advanced}
