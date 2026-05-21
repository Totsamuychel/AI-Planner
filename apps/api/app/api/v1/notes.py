from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import desc, func, select

from app.api.deps import CurrentUser, SessionDep
from app.models.notes import (
    EntityStatus,
    EntityType,
    ExtractedEntity,
    NoteDocument,
    NoteSource,
)
from app.schemas.common import Page
from app.schemas.notes import (
    EntityRead,
    IngestStatsOut,
    NoteDocumentRead,
    NoteSourceCreate,
    NoteSourceRead,
    SyncResult,
)
from app.schemas.task import TaskRead
from app.services.ai import get_provider
from app.services.ai.extraction import extract_for_document
from app.services.notes_ingest import accept_entity, sync_all_for_owner, sync_source

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("/ai/status")
async def ai_status() -> dict[str, str | bool]:
    p = get_provider()
    return {"provider": p.name, "enabled": p.name != "null"}


@router.post("/documents/{document_id}/extract")
async def extract_document(
    document_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> dict:
    doc = (
        await session.execute(
            select(NoteDocument).where(
                NoteDocument.id == document_id, NoteDocument.owner_id == user.id
            )
        )
    ).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="document not found")
    res = await extract_for_document(session, doc, provider=get_provider())
    return {"created": res.created, "used_ai": res.used_ai, "model": res.model}


@router.get("/sources", response_model=list[NoteSourceRead])
async def list_sources(user: CurrentUser, session: SessionDep) -> list[NoteSourceRead]:
    rows = (
        await session.execute(
            select(NoteSource).where(NoteSource.owner_id == user.id).order_by(NoteSource.created_at.asc())
        )
    ).scalars().all()
    return [NoteSourceRead.model_validate(r) for r in rows]


@router.post("/sources", response_model=NoteSourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    payload: NoteSourceCreate, user: CurrentUser, session: SessionDep
) -> NoteSourceRead:
    src = NoteSource(
        owner_id=user.id,
        name=payload.name,
        type=payload.type,
        path=payload.path,
        sync_interval_seconds=payload.sync_interval_seconds,
    )
    session.add(src)
    await session.flush()
    return NoteSourceRead.model_validate(src)


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    src = (
        await session.execute(
            select(NoteSource).where(NoteSource.id == source_id, NoteSource.owner_id == user.id)
        )
    ).scalar_one_or_none()
    if src is None:
        raise HTTPException(status_code=404, detail="source not found")
    await session.delete(src)


@router.post("/sync", response_model=SyncResult)
async def sync_all(user: CurrentUser, session: SessionDep) -> SyncResult:
    result = await sync_all_for_owner(session, user.id)
    return SyncResult(sources={k: IngestStatsOut(**v.as_dict()) for k, v in result.items()})


@router.post("/sources/{source_id}/sync", response_model=IngestStatsOut)
async def sync_one(source_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> IngestStatsOut:
    src = (
        await session.execute(
            select(NoteSource).where(NoteSource.id == source_id, NoteSource.owner_id == user.id)
        )
    ).scalar_one_or_none()
    if src is None:
        raise HTTPException(status_code=404, detail="source not found")
    stats = await sync_source(session, src)
    return IngestStatsOut(**stats.as_dict())


@router.get("/documents", response_model=Page[NoteDocumentRead])
async def list_documents(
    user: CurrentUser,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[NoteDocumentRead]:
    base = select(NoteDocument).where(NoteDocument.owner_id == user.id)
    total = int((await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one())
    rows = (
        await session.execute(
            base.order_by(desc(NoteDocument.updated_at)).limit(limit).offset(offset)
        )
    ).scalars().all()
    return Page[NoteDocumentRead](
        items=[NoteDocumentRead.model_validate(d) for d in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/inbox", response_model=Page[EntityRead])
async def inbox(
    user: CurrentUser,
    session: SessionDep,
    entity_type: list[EntityType] | None = Query(default=None),
    status_in: list[EntityStatus] | None = Query(default=[EntityStatus.PENDING], alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Page[EntityRead]:
    base = select(ExtractedEntity).where(ExtractedEntity.owner_id == user.id)
    if status_in:
        base = base.where(ExtractedEntity.status.in_(status_in))
    if entity_type:
        base = base.where(ExtractedEntity.entity_type.in_(entity_type))
    total = int((await session.execute(select(func.count()).select_from(base.subquery()))).scalar_one())
    rows = (
        await session.execute(
            base.order_by(desc(ExtractedEntity.confidence), desc(ExtractedEntity.created_at))
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()
    return Page[EntityRead](
        items=[EntityRead.model_validate(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/inbox/{entity_id}/accept", response_model=TaskRead)
async def accept(entity_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> TaskRead:
    ent = (
        await session.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.id == entity_id, ExtractedEntity.owner_id == user.id
            )
        )
    ).scalar_one_or_none()
    if ent is None:
        raise HTTPException(status_code=404, detail="entity not found")
    if ent.status != EntityStatus.PENDING:
        raise HTTPException(status_code=409, detail="entity already processed")
    task = await accept_entity(session, ent)
    return TaskRead.model_validate(task)


@router.post("/inbox/{entity_id}/reject", response_model=EntityRead)
async def reject(entity_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> EntityRead:
    ent = (
        await session.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.id == entity_id, ExtractedEntity.owner_id == user.id
            )
        )
    ).scalar_one_or_none()
    if ent is None:
        raise HTTPException(status_code=404, detail="entity not found")
    ent.status = EntityStatus.REJECTED
    await session.flush()
    return EntityRead.model_validate(ent)
