from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReminderChannel, ReminderStatus


class ReminderBase(BaseModel):
    entity_type: str
    entity_id: UUID
    channel: ReminderChannel
    remind_at: datetime
    payload_json: Dict[str, Any] = {}


class ReminderCreate(ReminderBase):
    pass


class ReminderUpdate(BaseModel):
    status: ReminderStatus


class ReminderOut(ReminderBase):
    id: UUID
    status: ReminderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationTestRequest(BaseModel):
    message: str
    channel: ReminderChannel
