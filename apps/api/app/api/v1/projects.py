from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.repositories.projects import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
async def list_projects(user: CurrentUser, session: SessionDep) -> list[ProjectRead]:
    rows = await ProjectRepository(session).list(user.id)
    return [ProjectRead.model_validate(p) for p in rows]


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate, user: CurrentUser, session: SessionDep
) -> ProjectRead:
    project = await ProjectRepository(session).create(user.id, payload)
    return ProjectRead.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    user: CurrentUser,
    session: SessionDep,
) -> ProjectRead:
    repo = ProjectRepository(session)
    project = await repo.get(project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    project = await repo.update(project, payload)
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> None:
    repo = ProjectRepository(session)
    project = await repo.get(project_id, user.id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    await repo.delete(project)
