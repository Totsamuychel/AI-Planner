from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_task_crud_flow(client: AsyncClient) -> None:
    # create
    r = await client.post("/api/v1/tasks", json={"title": "Write tests"})
    assert r.status_code == 201
    task = r.json()
    tid = task["id"]
    assert task["title"] == "Write tests"
    assert task["status"] == "inbox"
    assert task["priority"] in {"P0", "P1", "P2", "P3", "P4"}

    # list
    r = await client.get("/api/v1/tasks")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    # get
    r = await client.get(f"/api/v1/tasks/{tid}")
    assert r.status_code == 200

    # patch
    r = await client.patch(f"/api/v1/tasks/{tid}", json={"title": "Write more tests"})
    assert r.status_code == 200
    assert r.json()["title"] == "Write more tests"

    # delete
    r = await client.delete(f"/api/v1/tasks/{tid}")
    assert r.status_code == 204
    r = await client.get(f"/api/v1/tasks/{tid}")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_complete_task(client: AsyncClient) -> None:
    tid = (await client.post("/api/v1/tasks", json={"title": "Finish me"})).json()["id"]
    r = await client.post(f"/api/v1/tasks/{tid}/complete")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "done"
    assert body["completed_at"] is not None


@pytest.mark.asyncio
async def test_set_scores_updates_priority(client: AsyncClient) -> None:
    tid = (await client.post("/api/v1/tasks", json={"title": "Score me"})).json()["id"]
    r = await client.patch(
        f"/api/v1/tasks/{tid}/scores",
        json={"importance_score": 0.9, "urgency_score": 0.9},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["importance_score"] == 0.9
    assert body["urgency_score"] == 0.9
    # High importance + urgency must land in a top bucket.
    assert body["priority"] in {"P0", "P1"}


@pytest.mark.asyncio
async def test_eisenhower_ai_sort_heuristic_fallback(client: AsyncClient) -> None:
    await client.post("/api/v1/tasks", json={"title": "Sortable A"})
    await client.post("/api/v1/tasks", json={"title": "Sortable B"})
    r = await client.post("/api/v1/tasks/eisenhower/ai-sort")
    assert r.status_code == 200
    body = r.json()
    # No AI provider configured in tests -> heuristic branch.
    assert body["used_ai"] is False
    assert body["updated"] >= 2


@pytest.mark.asyncio
async def test_reprioritize(client: AsyncClient) -> None:
    await client.post("/api/v1/tasks", json={"title": "Reprio me"})
    r = await client.post("/api/v1/tasks/reprioritize")
    assert r.status_code == 200
    assert r.json()["reprioritized"] >= 1


@pytest.mark.asyncio
async def test_status_filter(client: AsyncClient) -> None:
    tid = (await client.post("/api/v1/tasks", json={"title": "Active one"})).json()["id"]
    await client.patch(f"/api/v1/tasks/{tid}", json={"status": "active"})
    r = await client.get("/api/v1/tasks", params={"status": "active"})
    assert r.status_code == 200
    assert all(t["status"] == "active" for t in r.json()["items"])
