from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import EnergyType, PriorityBucket, TaskSourceType, TaskStatus
from app.models.tag import task_tags


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", native_enum=False),
        nullable=False,
        default=TaskStatus.INBOX,
        index=True,
    )
    priority: Mapped[PriorityBucket] = mapped_column(
        Enum(PriorityBucket, name="priority_bucket", native_enum=False),
        nullable=False,
        default=PriorityBucket.P3,
        index=True,
    )
    source_type: Mapped[TaskSourceType] = mapped_column(
        Enum(TaskSourceType, name="task_source", native_enum=False),
        nullable=False,
        default=TaskSourceType.MANUAL,
    )
    source_note_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), nullable=True, index=True
    )

    energy_type: Mapped[EnergyType | None] = mapped_column(
        Enum(EnergyType, name="energy_type", native_enum=False), nullable=True
    )

    priority_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, index=True)
    urgency_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    effort_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    procrastination_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    snooze_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    due_date: Mapped[datetime | None] = mapped_column(nullable=True, index=True)
    scheduled_start: Mapped[datetime | None] = mapped_column(nullable=True)
    scheduled_end: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    snoozed_until: Mapped[datetime | None] = mapped_column(nullable=True)

    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    recurrence_rule: Mapped[str | None] = mapped_column(String(256), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    owner: Mapped["User"] = relationship("User", back_populates="tasks")  # noqa: F821
    project: Mapped["Project | None"] = relationship("Project", back_populates="tasks")  # noqa: F821
    parent: Mapped["Task | None"] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks"
    )
    subtasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="parent", cascade="all,delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(  # noqa: F821
        "Tag", secondary=task_tags, back_populates="tasks"
    )

    def __repr__(self) -> str:
        return f"<Task {self.title!r} status={self.status}>"
