from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en")
    work_hours_start: Mapped[str] = mapped_column(String(5), nullable=False, default="09:00")
    work_hours_end: Mapped[str] = mapped_column(String(5), nullable=False, default="18:00")
    telegram_chat_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    projects: Mapped[list["Project"]] = relationship(  # noqa: F821
        "Project", back_populates="owner", cascade="all,delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa: F821
        "Task", back_populates="owner", cascade="all,delete-orphan"
    )
    learning_items: Mapped[list["LearningItem"]] = relationship(  # noqa: F821
        "LearningItem", back_populates="owner", cascade="all,delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
