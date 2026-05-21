from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class ScheduledBlockOut(BaseModel):
    task_id: uuid.UUID
    title: str
    priority: str
    priority_score: float
    energy_type: str | None
    start: datetime
    end: datetime
    overflow: bool = False


class DayPlan(BaseModel):
    date: str
    blocks: list[ScheduledBlockOut]
    overflow_count: int
