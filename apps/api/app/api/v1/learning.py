from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, SessionDep
from app.models.learning import LearningItem, LearningSession
from app.models.enums import LearningItemStatus
from app.models.user import User
from app.schemas.learning import (
    LearningItemCreate,
    LearningItemOut,
    LearningItemUpdate,
    LearningSessionCreate,
    LearningSessionOut,
)

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("/goals", response_model=list[LearningItemOut])
async def list_learning_goals(
    db: SessionDep,
    user: CurrentUser,
) -> Any:
    """List all learning items for the current user."""
    result = await db.execute(
        select(LearningItem)
        .where(LearningItem.owner_id == user.id)
        .options(selectinload(LearningItem.sessions))
        .order_by(LearningItem.created_at.desc())
    )
    return result.scalars().all()


@router.post("/goals", response_model=LearningItemOut)
async def create_learning_goal(
    item_in: LearningItemCreate,
    db: SessionDep,
    user: CurrentUser,
) -> Any:
    """Create a new learning goal."""
    item = LearningItem(
        owner_id=user.id,
        title=item_in.title,
        topic=item_in.topic,
        level=item_in.level,
        target_date=item_in.target_date,
        estimated_sessions=item_in.estimated_sessions,
        status=LearningItemStatus.BACKLOG,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item, attribute_names=["sessions"])
    return item


@router.patch("/goals/{item_id}", response_model=LearningItemOut)
async def update_learning_goal(
    item_id: UUID,
    item_in: LearningItemUpdate,
    db: SessionDep,
    user: CurrentUser,
) -> Any:
    """Update a learning goal."""
    result = await db.execute(
        select(LearningItem)
        .where(LearningItem.id == item_id, LearningItem.owner_id == user.id)
        .options(selectinload(LearningItem.sessions))
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Learning item not found")

    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    await db.flush()
    return item


@router.post("/goals/{item_id}/sessions", response_model=LearningSessionOut)
async def log_learning_session(
    item_id: UUID,
    session_in: LearningSessionCreate,
    db: SessionDep,
    user: CurrentUser,
) -> Any:
    """Log a learning session and update the goal's spaced repetition schedule."""
    result = await db.execute(
        select(LearningItem)
        .where(LearningItem.id == item_id, LearningItem.owner_id == user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Learning item not found")

    # Create session
    session = LearningSession(
        learning_item_id=item.id,
        notes=session_in.notes,
        duration_minutes=session_in.duration_minutes,
    )
    db.add(session)
    
    # Update Learning Item
    item.completed_sessions += 1
    if item.status == LearningItemStatus.BACKLOG:
        item.status = LearningItemStatus.LEARNING

    if item.completed_sessions >= item.estimated_sessions:
        item.status = LearningItemStatus.COMPLETED
        item.next_review_at = None
    else:
        # Simple Spaced Repetition mechanic: next review is in (completed_sessions * 2) days
        item.next_review_at = datetime.utcnow() + timedelta(days=item.completed_sessions * 2)

    await db.flush()
    await db.refresh(session)
    return session


@router.get("/review", response_model=list[LearningItemOut])
async def get_items_for_review(
    db: SessionDep,
    user: CurrentUser,
) -> Any:
    """Get items that need to be reviewed today."""
    now = datetime.utcnow()
    result = await db.execute(
        select(LearningItem)
        .where(
            LearningItem.owner_id == user.id,
            LearningItem.status.in_([LearningItemStatus.LEARNING, LearningItemStatus.REVIEWING]),
            LearningItem.next_review_at <= now,
        )
        .options(selectinload(LearningItem.sessions))
        .order_by(LearningItem.next_review_at.asc())
    )
    return result.scalars().all()
