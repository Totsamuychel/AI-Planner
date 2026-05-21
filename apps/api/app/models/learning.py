import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import LearningItemStatus


class LearningItem(Base):
    __tablename__ = "learning_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    topic = Column(String(100), nullable=False, index=True)
    level = Column(String(50), nullable=True) # e.g. "beginner", "intermediate", "advanced"
    target_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default=LearningItemStatus.BACKLOG, index=True)
    next_review_at = Column(DateTime(timezone=True), nullable=True, index=True)
    estimated_sessions = Column(Integer, nullable=False, default=1)
    completed_sessions = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    owner = relationship("User", back_populates="learning_items")
    sessions = relationship("LearningSession", back_populates="learning_item", cascade="all,delete-orphan")


class LearningSession(Base):
    __tablename__ = "learning_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learning_item_id = Column(UUID(as_uuid=True), ForeignKey("learning_items.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=30)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    learning_item = relationship("LearningItem", back_populates="sessions")
