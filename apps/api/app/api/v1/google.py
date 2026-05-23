"""Google Calendar — OAuth + Calendar API endpoints.

Auth flow (server-side, single-tenant demo user):
    1. Browser hits  GET  /api/v1/google/auth/url      -> {url}
    2. User opens the URL, grants access, Google redirects to
       GET  /api/v1/google/callback?code=&state=
    3. We exchange the code, persist tokens on the user, then redirect
       the browser to GOOGLE_POST_AUTH_REDIRECT (the web `/settings`
       page by default).

All read/write endpoints fail soft when Google is not configured or the
user hasn't connected yet — the UI shows an inert "Connect" button.
"""

from __future__ import annotations

import secrets
from datetime import UTC, date, datetime, time, timedelta
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUser, SessionDep
from app.core.config import get_settings
from app.models.enums import TaskStatus
from app.models.task import Task
from app.repositories.tasks import TaskFilter, TaskRepository
from app.services import google_calendar as gcal
from app.services.scheduler import build_plan

router = APIRouter(prefix="/google", tags=["google"])


@router.get("/status")
async def status_(user: CurrentUser) -> dict[str, Any]:
    configured = gcal.is_configured()
    connected = configured and bool(user.google_refresh_token or user.google_access_token)
    return {
        "configured": configured,
        "connected": connected,
        "calendar_id": user.google_calendar_id or "primary",
    }


@router.get("/auth/url")
async def auth_url() -> dict[str, str]:
    if not gcal.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured (set GOOGLE_CLIENT_ID/SECRET in .env).",
        )
    state = secrets.token_urlsafe(16)
    return {"url": gcal.build_authorization_url(state), "state": state}


@router.get("/callback")
async def callback(
    user: CurrentUser,
    session: SessionDep,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    error: str | None = Query(default=None),
) -> RedirectResponse:
    settings = get_settings()
    redirect = settings.google_post_auth_redirect
    if error or not code:
        return RedirectResponse(f"{redirect.split('?')[0]}?google=error", status_code=302)
    try:
        creds = gcal.exchange_code_for_tokens(code, state=state)
        await gcal.persist_credentials(session, user, creds)
    except Exception:  # noqa: BLE001
        return RedirectResponse(f"{redirect.split('?')[0]}?google=error", status_code=302)
    return RedirectResponse(redirect, status_code=302)


@router.post("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect(user: CurrentUser, session: SessionDep) -> None:
    await gcal.disconnect(session, user)


@router.get("/events")
async def list_events(
    user: CurrentUser,
    session: SessionDep,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
) -> dict[str, Any]:
    now = datetime.now(tz=UTC)
    if start is None:
        start = datetime.combine(now.date(), time(0, 0), tzinfo=UTC)
    if end is None:
        end = start + timedelta(days=1)
    events = await gcal.list_events(session, user, start=start, end=end)
    return {"events": events}


@router.post("/events")
async def create_event(
    payload: dict[str, Any],
    user: CurrentUser,
    session: SessionDep,
) -> dict[str, Any]:
    try:
        title = str(payload["title"])
        start = datetime.fromisoformat(payload["start"])
        end = datetime.fromisoformat(payload["end"])
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"bad payload: {e}")
    description = str(payload.get("description", ""))
    result = await gcal.create_event(
        session, user, title=title, start=start, end=end, description=description
    )
    if result is None:
        raise HTTPException(status_code=502, detail="Google API call failed")
    return result


def _parse_hhmm(value: str, fallback: tuple[int, int]) -> time:
    try:
        h, m = value.split(":")
        return time(int(h), int(m))
    except Exception:  # noqa: BLE001
        return time(*fallback)


@router.post("/ai-plan")
async def ai_plan(
    user: CurrentUser,
    session: SessionDep,
    target_day: date | None = Query(default=None),
) -> dict[str, Any]:
    """Schedule open tasks with the local greedy planner and push each
    block as an event into the user's Google Calendar.

    Uses the per-task priority/urgency that the AI sort already set
    (run "Sort with AI" on /matrix first to involve Ollama/OpenAI).
    """
    if not gcal.is_configured():
        raise HTTPException(status_code=503, detail="Google OAuth is not configured")
    if not user.google_refresh_token and not user.google_access_token:
        raise HTTPException(status_code=409, detail="Google account not connected")

    target_day = target_day or datetime.now(tz=UTC).date()
    ws = _parse_hhmm(user.work_hours_start, (9, 0))
    we = _parse_hhmm(user.work_hours_end, (18, 0))

    repo = TaskRepository(session)
    rows, _ = await repo.list(
        user.id,
        filt=TaskFilter(
            status=[TaskStatus.INBOX, TaskStatus.PLANNED, TaskStatus.ACTIVE]
        ),
        limit=40,
    )
    blocks = build_plan(tasks=rows, target_day=target_day, work_start=ws, work_end=we)
    if not blocks:
        return {"created": 0, "skipped": 0, "reason": "no open tasks"}

    by_id = {str(t.id): t for t in rows}
    created = 0
    for b in blocks:
        task = by_id.get(b.task_id)
        description = (task.description or "")[:500] if task else ""
        result = await gcal.create_event(
            session,
            user,
            title=b.title,
            start=b.start,
            end=b.end,
            description=description,
        )
        if result:
            created += 1
            if task and task.status == TaskStatus.INBOX:
                task.status = TaskStatus.PLANNED
            if task:
                task.scheduled_start = b.start
                task.scheduled_end = b.end
    await session.flush()
    return {"created": created, "skipped": len(blocks) - created, "day": target_day.isoformat()}
