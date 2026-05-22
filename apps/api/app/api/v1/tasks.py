from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser, SessionDep
from app.models.enums import PriorityBucket, TaskStatus
from app.repositories.tasks import TaskFilter, TaskRepository
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskRead, TaskScoresIn, TaskSnoozeIn, TaskUpdate
from app.services import prioritization
from app.services.ai.decomposition import decompose_task as ai_decompose_task
from app.services.ai.eisenhower import ai_classify

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _repo(session: SessionDep) -> TaskRepository:
    return TaskRepository(session)


@router.get("", response_model=Page[TaskRead])
async def list_tasks(
    user: CurrentUser,
    session: SessionDep,
    status_in: list[TaskStatus] | None = Query(default=None, alias="status"),
    priority_in: list[PriorityBucket] | None = Query(default=None, alias="priority"),
    project_id: uuid.UUID | None = None,
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[TaskRead]:
    repo = TaskRepository(session)
    rows, total = await repo.list(
        user.id,
        filt=TaskFilter(
            status=status_in,
            priority=priority_in,
            project_id=project_id,
            search=search,
        ),
        limit=limit,
        offset=offset,
    )
    return Page[TaskRead](
        items=[TaskRead.model_validate(t) for t in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate, user: CurrentUser, session: SessionDep
) -> TaskRead:
    task = await TaskRepository(session).create(user.id, payload)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> TaskRead:
    task = await TaskRepository(session).get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: uuid.UUID, payload: TaskUpdate, user: CurrentUser, session: SessionDep
) -> TaskRead:
    repo = TaskRepository(session)
    task = await repo.get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task = await repo.update(task, payload)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    repo = TaskRepository(session)
    task = await repo.get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    await repo.delete(task)


@router.post("/{task_id}/complete", response_model=TaskRead)
async def complete_task(
    task_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> TaskRead:
    repo = TaskRepository(session)
    task = await repo.get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.model_validate(await repo.complete(task))


@router.post("/{task_id}/snooze", response_model=TaskRead)
async def snooze_task(
    task_id: uuid.UUID,
    payload: TaskSnoozeIn,
    user: CurrentUser,
    session: SessionDep,
) -> TaskRead:
    repo = TaskRepository(session)
    task = await repo.get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskRead.model_validate(await repo.snooze(task, payload.until))


@router.post("/{task_id}/decompose", response_model=list[TaskRead])
async def decompose_task_endpoint(
    task_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> list[TaskRead]:
    repo = TaskRepository(session)
    task = await repo.get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
        
    subtasks_data = await ai_decompose_task(task.title, task.description)
    created_subtasks = []
    
    for sub_data in subtasks_data:
        payload = TaskCreate(
            title=sub_data["title"],
            description="",
            estimated_minutes=sub_data.get("estimated_minutes"),
            parent_id=task.id,
            project_id=task.project_id
        )
        new_sub = await repo.create(user.id, payload)
        created_subtasks.append(new_sub)
        
    return [TaskRead.model_validate(t) for t in created_subtasks]


@router.patch("/{task_id}/scores", response_model=TaskRead)
async def set_task_scores(
    task_id: uuid.UUID,
    payload: TaskScoresIn,
    user: CurrentUser,
    session: SessionDep,
) -> TaskRead:
    """Set importance/urgency directly (Eisenhower matrix drag-and-drop).

    Recomputes priority_score and bucket from the supplied axes without
    re-deriving urgency from the due date.
    """
    repo = TaskRepository(session)
    task = await repo.get(task_id, user.id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.importance_score = payload.importance_score
    task.urgency_score = payload.urgency_score
    prioritization.recompute_priority_only(task)
    await session.flush()
    await session.refresh(task, attribute_names=["updated_at", "tags"])
    return TaskRead.model_validate(task)


@router.post("/eisenhower/ai-sort", response_model=dict)
async def ai_sort_eisenhower(user: CurrentUser, session: SessionDep) -> dict[str, Any]:
    """Let the LLM place every open task on the Eisenhower matrix.

    The model assigns importance/urgency for each task; we write the
    scores back and recompute priority. If no AI provider is configured,
    falls back to a deterministic heuristic (urgency from the due date).
    """
    repo = TaskRepository(session)
    rows, _ = await repo.list(
        user.id,
        filt=TaskFilter(status=[TaskStatus.INBOX, TaskStatus.PLANNED, TaskStatus.ACTIVE]),
        limit=200,
    )
    if not rows:
        return {"updated": 0, "used_ai": False}

    classified = await ai_classify(rows)
    used_ai = bool(classified)

    updated = 0
    for task in rows:
        if used_ai:
            assigned = classified.get(str(task.id))
            if assigned is None:
                continue
            task.importance_score, task.urgency_score = assigned
        else:
            # Heuristic fallback: derive urgency from the deadline.
            task.urgency_score = prioritization.urgency_from_due(task.due_date)
        prioritization.recompute_priority_only(task)
        updated += 1

    await session.flush()
    return {"updated": updated, "used_ai": used_ai}


@router.post("/reprioritize", response_model=dict)
async def reprioritize_all(user: CurrentUser, session: SessionDep) -> dict:
    count = await TaskRepository(session).reprioritize_all(user.id)
    return {"reprioritized": count}
