import uuid
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base
from app.models.enums import ReminderChannel, ReminderStatus


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    channel = Column(String(50), nullable=False)
    remind_at = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50), nullable=False, default=ReminderStatus.PENDING, index=True)
    payload_json = Column(JSONB, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
