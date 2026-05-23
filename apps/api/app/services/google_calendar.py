"""Google Calendar integration.

Wraps Google's OAuth flow + Calendar v3 client. Stores per-user
access/refresh tokens on `User`; the helpers in this module rebuild a
`Credentials` object, transparently refresh expired access tokens, and
persist the new values back to the database.

Configured via:
    GOOGLE_CLIENT_ID
    GOOGLE_CLIENT_SECRET
    GOOGLE_REDIRECT_URI          # default: http://localhost:8000/api/v1/google/callback
    GOOGLE_POST_AUTH_REDIRECT    # where we send the browser after callback
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

import structlog
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.user import User

log = structlog.get_logger("google.calendar")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def is_configured() -> bool:
    s = get_settings()
    return bool(s.google_client_id and s.google_client_secret)


def _client_config() -> dict[str, Any]:
    s = get_settings()
    return {
        "web": {
            "client_id": s.google_client_id,
            "client_secret": s.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [s.google_redirect_uri],
        }
    }


def build_authorization_url(state: str) -> str:
    """Step 1: redirect the user to Google's consent screen."""
    s = get_settings()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = s.google_redirect_uri
    url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",  # forces refresh_token to be returned
    )
    return url


def exchange_code_for_tokens(code: str, state: str | None = None) -> Credentials:
    """Step 2: callback handler — turn the auth code into credentials."""
    s = get_settings()
    flow = Flow.from_client_config(_client_config(), scopes=SCOPES, state=state)
    flow.redirect_uri = s.google_redirect_uri
    flow.fetch_token(code=code)
    return flow.credentials


async def persist_credentials(session: AsyncSession, user: User, creds: Credentials) -> None:
    user.google_access_token = creds.token
    if creds.refresh_token:
        user.google_refresh_token = creds.refresh_token
    user.google_token_expiry = (
        creds.expiry.replace(tzinfo=UTC) if creds.expiry and creds.expiry.tzinfo is None else creds.expiry
    )
    await session.flush()


def credentials_from_user(user: User) -> Credentials | None:
    if not user.google_access_token and not user.google_refresh_token:
        return None
    s = get_settings()
    creds = Credentials(
        token=user.google_access_token,
        refresh_token=user.google_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=s.google_client_id,
        client_secret=s.google_client_secret,
        scopes=SCOPES,
    )
    if user.google_token_expiry:
        # Credentials stores expiry as naive UTC.
        exp = user.google_token_expiry
        if exp.tzinfo is not None:
            exp = exp.astimezone(UTC).replace(tzinfo=None)
        creds.expiry = exp
    return creds


async def ensure_fresh(session: AsyncSession, user: User) -> Credentials | None:
    creds = credentials_from_user(user)
    if creds is None:
        return None
    if creds.expired and creds.refresh_token:
        await asyncio.to_thread(creds.refresh, Request())
        await persist_credentials(session, user, creds)
    return creds


def _service(creds: Credentials):
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


async def list_events(
    session: AsyncSession,
    user: User,
    *,
    start: datetime,
    end: datetime,
) -> list[dict[str, Any]]:
    creds = await ensure_fresh(session, user)
    if creds is None:
        return []

    def _call() -> list[dict[str, Any]]:
        svc = _service(creds)
        res = (
            svc.events()
            .list(
                calendarId=user.google_calendar_id or "primary",
                timeMin=start.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                timeMax=end.astimezone(UTC).isoformat().replace("+00:00", "Z"),
                singleEvents=True,
                orderBy="startTime",
                maxResults=250,
            )
            .execute()
        )
        return res.get("items", [])

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:  # noqa: BLE001
        log.warning("google.list_events_failed", error=str(e))
        return []


async def create_event(
    session: AsyncSession,
    user: User,
    *,
    title: str,
    start: datetime,
    end: datetime,
    description: str = "",
) -> dict[str, Any] | None:
    creds = await ensure_fresh(session, user)
    if creds is None:
        return None
    body = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start.astimezone(UTC).isoformat().replace("+00:00", "Z")},
        "end": {"dateTime": end.astimezone(UTC).isoformat().replace("+00:00", "Z")},
    }

    def _call() -> dict[str, Any]:
        svc = _service(creds)
        return (
            svc.events()
            .insert(calendarId=user.google_calendar_id or "primary", body=body)
            .execute()
        )

    try:
        return await asyncio.to_thread(_call)
    except Exception as e:  # noqa: BLE001
        log.warning("google.create_event_failed", error=str(e), title=title)
        return None


async def create_events_bulk(
    session: AsyncSession,
    user: User,
    events: Iterable[dict[str, Any]],
) -> int:
    created = 0
    for ev in events:
        result = await create_event(
            session,
            user,
            title=ev["title"],
            start=ev["start"],
            end=ev["end"],
            description=ev.get("description", ""),
        )
        if result:
            created += 1
    return created


async def disconnect(session: AsyncSession, user: User) -> None:
    user.google_access_token = None
    user.google_refresh_token = None
    user.google_token_expiry = None
    await session.flush()
