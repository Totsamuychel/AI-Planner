"""Day planner.

Greedy algorithm that fills work-hour blocks with tasks ordered by
`priority_score`. The output is a list of `(task, start, end)` triples;
the service writes them back into `Task.scheduled_start/scheduled_end`.

It deliberately avoids treating the planner as an ILP solver — for a
personal productivity tool the priority order + duration packing gives
useful results, and the user always retains the ability to drag blocks
around. Phase 7 (anti-procrastination) tunes the heuristics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from typing import Iterable

import structlog
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import TaskStatus
from app.models.task import Task
from app.models.user import User

log = structlog.get_logger("scheduler")

DEFAULT_BLOCK_MIN = 30
MAX_BLOCK_MIN = 120
MIN_BREAK_MIN = 5
DAY_OVERFLOW_GUARD = 14  # hours we refuse to schedule past


@dataclass
class ScheduledBlock:
    task_id: str
    title: str
    priority: str
    priority_score: float
    energy_type: str | None
    start: datetime
    end: datetime
    overflow: bool = False


def _parse_hhmm(value: str, fallback: tuple[int, int]) -> time:
    try:
        h, m = value.split(":")
        return time(int(h), int(m))
    except Exception:  # noqa: BLE001
        return time(*fallback)


def _clip_duration(estimated: int | None) -> int:
    if not estimated or estimated <= 0:
        return DEFAULT_BLOCK_MIN
    return min(MAX_BLOCK_MIN, max(15, estimated))


def _candidates(tasks: Iterable[Task]) -> list[Task]:
    out: list[Task] = []
    for t in tasks:
        if t.status in (TaskStatus.DONE, TaskStatus.ARCHIVED, TaskStatus.SNOOZED):
            continue
        out.append(t)
    out.sort(key=lambda t: (-t.priority_score, t.due_date or datetime.max.replace(tzinfo=UTC)))
    return out


def build_plan(
    *,
    tasks: Iterable[Task],
    target_day: date,
    work_start: time,
    work_end: time,
    tz=UTC,
) -> list[ScheduledBlock]:
    candidates = _candidates(tasks)
    if not candidates:
        return []

    cursor = datetime.combine(target_day, work_start, tzinfo=tz)
    end_of_day = datetime.combine(target_day, work_end, tzinfo=tz)
    overflow_limit = cursor + timedelta(hours=DAY_OVERFLOW_GUARD)

    blocks: list[ScheduledBlock] = []
    for t in candidates:
        dur = _clip_duration(t.estimated_minutes)
        # leave at least MIN_BREAK_MIN gap between blocks (cursor already advanced past prev)
        start = cursor
        end = start + timedelta(minutes=dur)
        overflow = end > end_of_day
        if start >= overflow_limit:
            break  # don't plan past 14h of day — refuse to overschedule
        blocks.append(
            ScheduledBlock(
                task_id=str(t.id),
                title=t.title,
                priority=str(t.priority),
                priority_score=float(t.priority_score),
                energy_type=str(t.energy_type) if t.energy_type else None,
                start=start,
                end=end,
                overflow=overflow,
            )
        )
        cursor = end + timedelta(minutes=MIN_BREAK_MIN)
    return blocks


async def generate_for_user(
    session: AsyncSession,
    user: User,
    target_day: date | None = None,
) -> list[ScheduledBlock]:
    target_day = target_day or datetime.now(tz=UTC).date()
    ws = _parse_hhmm(user.work_hours_start, (9, 0))
    we = _parse_hhmm(user.work_hours_end, (18, 0))

    rows = (
        await session.execute(
            select(Task)
            .where(Task.owner_id == user.id)
            .where(Task.status.in_([TaskStatus.INBOX, TaskStatus.PLANNED, TaskStatus.ACTIVE]))
            .order_by(desc(Task.priority_score))
            .limit(40)
        )
    ).scalars().all()

    blocks = build_plan(tasks=rows, target_day=target_day, work_start=ws, work_end=we)

    # persist
    by_id = {str(t.id): t for t in rows}
    for b in blocks:
        t = by_id[b.task_id]
        t.scheduled_start = b.start
        t.scheduled_end = b.end
        if t.status == TaskStatus.INBOX:
            t.status = TaskStatus.PLANNED
    await session.flush()
    log.info(
        "schedule.generated",
        user=str(user.id),
        day=target_day.isoformat(),
        count=len(blocks),
        overflow=sum(1 for b in blocks if b.overflow),
    )
    return blocks


async def todays_plan(session: AsyncSession, user: User) -> list[ScheduledBlock]:
    """Read currently-persisted plan for today (no rewrites)."""
    today = datetime.now(tz=UTC).date()
    start_dt = datetime.combine(today, time(0, 0), tzinfo=UTC)
    end_dt = start_dt + timedelta(days=1)
    rows = (
        await session.execute(
            select(Task)
            .where(Task.owner_id == user.id)
            .where(Task.scheduled_start.is_not(None))
            .where(Task.scheduled_start >= start_dt)
            .where(Task.scheduled_start < end_dt)
            .order_by(Task.scheduled_start.asc())
        )
    ).scalars().all()
    return [
        ScheduledBlock(
            task_id=str(t.id),
            title=t.title,
            priority=str(t.priority),
            priority_score=float(t.priority_score),
            energy_type=str(t.energy_type) if t.energy_type else None,
            start=t.scheduled_start,  # type: ignore[arg-type]
            end=t.scheduled_end or (t.scheduled_start + timedelta(minutes=30)),  # type: ignore[arg-type]
        )
        for t in rows
    ]


async def week_plan(session: AsyncSession, user: User) -> dict[str, list[ScheduledBlock]]:
    """Read persisted scheduled tasks for the next 7 days, grouped by date."""
    today = datetime.now(tz=UTC).date()
    start_dt = datetime.combine(today, time(0, 0), tzinfo=UTC)
    end_dt = start_dt + timedelta(days=7)
    rows = (
        await session.execute(
            select(Task)
            .where(Task.owner_id == user.id)
            .where(Task.scheduled_start.is_not(None))
            .where(Task.scheduled_start >= start_dt)
            .where(Task.scheduled_start < end_dt)
            .order_by(Task.scheduled_start.asc())
        )
    ).scalars().all()

    days: dict[str, list[ScheduledBlock]] = {
        (today + timedelta(days=i)).isoformat(): [] for i in range(7)
    }
    for t in rows:
        if t.scheduled_start is None:
            continue
        key = t.scheduled_start.date().isoformat()
        if key not in days:
            continue
        days[key].append(
            ScheduledBlock(
                task_id=str(t.id),
                title=t.title,
                priority=str(t.priority),
                priority_score=float(t.priority_score),
                energy_type=str(t.energy_type) if t.energy_type else None,
                start=t.scheduled_start,
                end=t.scheduled_end or (t.scheduled_start + timedelta(minutes=30)),
            )
        )
    return days


async def rebalance_for_user(session: AsyncSession, user: User) -> list[ScheduledBlock]:
    """Clear today's schedule and rebuild — used after major changes."""
    today = datetime.now(tz=UTC).date()
    start_dt = datetime.combine(today, time(0, 0), tzinfo=UTC)
    end_dt = start_dt + timedelta(days=1)
    rows = (
        await session.execute(
            select(Task)
            .where(Task.owner_id == user.id)
            .where(Task.scheduled_start.is_not(None))
            .where(Task.scheduled_start >= start_dt)
            .where(Task.scheduled_start < end_dt)
        )
    ).scalars().all()
    for t in rows:
        t.scheduled_start = None
        t.scheduled_end = None
    await session.flush()
    return await generate_for_user(session, user, target_day=today)
