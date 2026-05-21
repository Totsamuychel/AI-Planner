from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func, select

from fastapi import APIRouter

from app.api.deps import CurrentUser, SessionDep
from app.models.enums import TaskStatus
from app.models.task import Task

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(user: CurrentUser, session: SessionDep) -> dict[str, Any]:
    now = datetime.now(tz=UTC)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=7)

    async def count(where) -> int:
        stmt = select(func.count()).select_from(Task).where(Task.owner_id == user.id, where)
        return int((await session.execute(stmt)).scalar_one())

    total = await count(Task.id.is_not(None))
    open_count = await count(Task.status.in_([TaskStatus.INBOX, TaskStatus.PLANNED, TaskStatus.ACTIVE]))
    overdue = await count(
        (Task.due_date.is_not(None))
        & (Task.due_date < now)
        & (Task.status != TaskStatus.DONE)
        & (Task.status != TaskStatus.ARCHIVED)
    )
    completed_7d = await count(
        (Task.status == TaskStatus.DONE) & (Task.completed_at >= week_ago)
    )
    completed_today = await count(
        (Task.status == TaskStatus.DONE) & (Task.completed_at >= today_start)
    )

    # 7-day completion histogram
    rows = (
        await session.execute(
            select(
                func.date_trunc("day", Task.completed_at).label("day"),
                func.count().label("c"),
            )
            .where(
                Task.owner_id == user.id,
                Task.status == TaskStatus.DONE,
                Task.completed_at >= week_ago,
            )
            .group_by("day")
            .order_by("day")
        )
    ).all()
    series = [{"day": r.day.date().isoformat(), "count": int(r.c)} for r in rows]

    return {
        "totals": {
            "all": total,
            "open": open_count,
            "overdue": overdue,
            "completed_today": completed_today,
            "completed_7d": completed_7d,
        },
        "completion_7d": series,
        "as_of": now.isoformat(),
    }
