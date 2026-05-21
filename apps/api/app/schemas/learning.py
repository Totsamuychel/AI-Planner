from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import LearningItemStatus


class LearningSessionBase(BaseModel):
    notes: str | None = None
    duration_minutes: int = 30


class LearningSessionCreate(LearningSessionBase):
    pass


class LearningSessionOut(LearningSessionBase):
    id: UUID
    learning_item_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearningItemBase(BaseModel):
    title: str
    topic: str
    level: str | None = None
    target_date: datetime | None = None
    estimated_sessions: int = 1


class LearningItemCreate(LearningItemBase):
    pass


class LearningItemUpdate(BaseModel):
    title: str | None = None
    topic: str | None = None
    level: str | None = None
    target_date: datetime | None = None
    status: LearningItemStatus | None = None
    estimated_sessions: int | None = None


class LearningItemOut(LearningItemBase):
    id: UUID
    owner_id: UUID
    status: LearningItemStatus
    next_review_at: datetime | None
    completed_sessions: int
    created_at: datetime
    updated_at: datetime
    
    sessions: list[LearningSessionOut] = []

    model_config = ConfigDict(from_attributes=True)
