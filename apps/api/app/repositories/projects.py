from __future__ import annotations

import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list(self, owner_id: uuid.UUID) -> Sequence[Project]:
        stmt = select(Project).where(Project.owner_id == owner_id).order_by(Project.created_at.asc())
        return (await self.session.execute(stmt)).scalars().all()

    async def get(self, project_id: uuid.UUID, owner_id: uuid.UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def create(self, owner_id: uuid.UUID, data: ProjectCreate) -> Project:
        project = Project(owner_id=owner_id, **data.model_dump())
        self.session.add(project)
        await self.session.flush()
        return project

    async def update(self, project: Project, data: ProjectUpdate) -> Project:
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(project, k, v)
        await self.session.flush()
        return project

    async def delete(self, project: Project) -> None:
        await self.session.delete(project)
        await self.session.flush()
