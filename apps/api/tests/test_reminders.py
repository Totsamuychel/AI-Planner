from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_notification_test_endpoint(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/notifications/test",
        json={"channel": "desktop", "message": "hello"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_notification_history_empty(client: AsyncClient) -> None:
    r = await client.get("/api/v1/notifications/history")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_notification_test_requires_body(client: AsyncClient) -> None:
    r = await client.post("/api/v1/notifications/test")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_telegram_settings(client: AsyncClient) -> None:
    r = await client.patch(
        "/api/v1/settings/telegram",
        json={"telegram_chat_id": "123456789"},
    )
    assert r.status_code == 200
    assert r.json()["telegram_chat_id"] == "123456789"
