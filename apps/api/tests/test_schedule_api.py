from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _make_tasks(client: AsyncClient, n: int) -> None:
    for i in range(n):
        await client.post(
            "/api/v1/tasks",
            json={"title": f"Task {i}", "estimated_minutes": 60},
        )


@pytest.mark.asyncio
async def test_generate_then_today(client: AsyncClient) -> None:
    await _make_tasks(client, 3)

    r = await client.post("/api/v1/schedule/generate")
    assert r.status_code == 200
    plan = r.json()
    assert len(plan["blocks"]) == 3
    assert "overflow_count" in plan

    r = await client.get("/api/v1/schedule/today")
    assert r.status_code == 200
    assert len(r.json()["blocks"]) == 3


@pytest.mark.asyncio
async def test_today_empty_without_generate(client: AsyncClient) -> None:
    r = await client.get("/api/v1/schedule/today")
    assert r.status_code == 200
    assert r.json()["blocks"] == []


@pytest.mark.asyncio
async def test_rebalance(client: AsyncClient) -> None:
    await _make_tasks(client, 2)
    await client.post("/api/v1/schedule/generate")
    r = await client.post("/api/v1/schedule/rebalance")
    assert r.status_code == 200
    assert len(r.json()["blocks"]) == 2
