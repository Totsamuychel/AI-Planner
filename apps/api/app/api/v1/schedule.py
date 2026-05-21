from __future__ import annotations

from datetime import UTC, date, datetime

from fastapi import APIRouter, Query

from app.api.deps import CurrentUser, SessionDep
from app.schemas.schedule import DayPlan, ScheduledBlockOut
from app.services.scheduler import (
    ScheduledBlock,
    generate_for_user,
    rebalance_for_user,
    todays_plan,
)

router = APIRouter(prefix="/schedule", tags=["schedule"])


def _to_dto(blocks: list[ScheduledBlock]) -> DayPlan:
    day_iso = (blocks[0].start.date() if blocks else datetime.now(tz=UTC).date()).isoformat()
    return DayPlan(
        date=day_iso,
        blocks=[ScheduledBlockOut(**b.__dict__) for b in blocks],
        overflow_count=sum(1 for b in blocks if b.overflow),
    )


@router.get("/today", response_model=DayPlan)
async def get_today(user: CurrentUser, session: SessionDep) -> DayPlan:
    blocks = await todays_plan(session, user)
    return _to_dto(blocks)


@router.post("/generate", response_model=DayPlan)
async def generate(
    user: CurrentUser,
    session: SessionDep,
    target_day: date | None = Query(default=None),
) -> DayPlan:
    blocks = await generate_for_user(session, user, target_day=target_day)
    return _to_dto(blocks)


@router.post("/rebalance", response_model=DayPlan)
async def rebalance(user: CurrentUser, session: SessionDep) -> DayPlan:
    blocks = await rebalance_for_user(session, user)
    return _to_dto(blocks)
