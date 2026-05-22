from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EnergyType, PriorityBucket, TaskSourceType, TaskStatus
from app.schemas.tag import TagRead


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str = ""
    status: TaskStatus = TaskStatus.INBOX
    priority: PriorityBucket = PriorityBucket.P3
    source_type: TaskSourceType = TaskSourceType.MANUAL
    energy_type: EnergyType | None = None
    due_date: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=0, le=10_000)
    project_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None


class TaskCreate(TaskBase):
    importance_score: float = Field(default=0.5, ge=0.0, le=1.0)
    effort_score: float = Field(default=0.5, ge=0.0, le=1.0)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    status: TaskStatus | None = None
    priority: PriorityBucket | None = None
    energy_type: EnergyType | None = None
    due_date: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    estimated_minutes: int | None = Field(default=None, ge=0, le=10_000)
    actual_minutes: int | None = Field(default=None, ge=0, le=10_000)
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    effort_score: float | None = Field(default=None, ge=0.0, le=1.0)
    project_id: uuid.UUID | None = None


class TaskSnoozeIn(BaseModel):
    until: datetime


class TaskScoresIn(BaseModel):
    """Manual urgency/importance update — used by the Eisenhower matrix."""

    importance_score: float = Field(ge=0.0, le=1.0)
    urgency_score: float = Field(ge=0.0, le=1.0)


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    project_id: uuid.UUID | None
    parent_id: uuid.UUID | None
    title: str
    description: str
    status: TaskStatus
    priority: PriorityBucket
    source_type: TaskSourceType
    energy_type: EnergyType | None
    priority_score: float
    urgency_score: float
    importance_score: float
    effort_score: float
    procrastination_score: float
    snooze_count: int
    due_date: datetime | None
    scheduled_start: datetime | None
    scheduled_end: datetime | None
    completed_at: datetime | None
    snoozed_until: datetime | None
    estimated_minutes: int | None
    actual_minutes: int | None
    tags: list[TagRead] = []
    created_at: datetime
    updated_at: datetime
