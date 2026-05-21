from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import PriorityBucket, TaskStatus
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.services import prioritization


class TaskFilter:
    def __init__(
        self,
        *,
        status: list[TaskStatus] | None = None,
        priority: list[PriorityBucket] | None = None,
        project_id: uuid.UUID | None = None,
        search: str | None = None,
        due_before: datetime | None = None,
    ) -> None:
        self.status = status
        self.priority = priority
        self.project_id = project_id
        self.search = search
        self.due_before = due_before


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_query(self):
        return select(Task).options(selectinload(Task.tags))

    async def get(self, task_id: uuid.UUID, owner_id: uuid.UUID) -> Task | None:
        stmt = self._base_query().where(Task.id == task_id, Task.owner_id == owner_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        owner_id: uuid.UUID,
        *,
        filt: TaskFilter,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Task], int]:
        base = select(Task).where(Task.owner_id == owner_id)
        if filt.status:
            base = base.where(Task.status.in_(filt.status))
        if filt.priority:
            base = base.where(Task.priority.in_(filt.priority))
        if filt.project_id:
            base = base.where(Task.project_id == filt.project_id)
        if filt.search:
            like = f"%{filt.search.lower()}%"
            base = base.where(func.lower(Task.title).like(like))
        if filt.due_before:
            base = base.where(Task.due_date.is_not(None)).where(Task.due_date <= filt.due_before)

        total = (await self.session.execute(select(func.count()).select_from(base.subquery()))).scalar_one()

        rows = (
            await self.session.execute(
                base.options(selectinload(Task.tags))
                .order_by(desc(Task.priority_score), Task.due_date.asc().nulls_last(), Task.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).scalars().all()
        return rows, int(total)

    async def create(self, owner_id: uuid.UUID, data: TaskCreate) -> Task:
        task = Task(
            owner_id=owner_id,
            title=data.title,
            description=data.description,
            status=data.status,
            priority=data.priority,
            source_type=data.source_type,
            energy_type=data.energy_type,
            due_date=data.due_date,
            scheduled_start=data.scheduled_start,
            scheduled_end=data.scheduled_end,
            estimated_minutes=data.estimated_minutes,
            project_id=data.project_id,
            parent_id=data.parent_id,
            importance_score=data.importance_score,
            effort_score=data.effort_score,
        )
        prioritization.recompute(task)
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task, attribute_names=["tags"])
        return task

    async def update(self, task: Task, data: TaskUpdate) -> Task:
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(task, k, v)
        prioritization.recompute(task)
        await self.session.flush()
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()

    async def complete(self, task: Task) -> Task:
        task.status = TaskStatus.DONE
        task.completed_at = datetime.now(tz=UTC)
        await self.session.flush()
        return task

    async def snooze(self, task: Task, until: datetime) -> Task:
        task.status = TaskStatus.SNOOZED
        task.snoozed_until = until
        task.snooze_count += 1
        prioritization.recompute(task)
        await self.session.flush()
        return task

    async def reprioritize_all(self, owner_id: uuid.UUID) -> int:
        rows = (
            await self.session.execute(select(Task).where(Task.owner_id == owner_id))
        ).scalars().all()
        for t in rows:
            prioritization.recompute(t)
        await self.session.flush()
        return len(rows)
