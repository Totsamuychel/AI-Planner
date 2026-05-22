from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_learning_goal_and_sessions(client: AsyncClient) -> None:
    # create a goal
    r = await client.post(
        "/api/v1/learning/goals",
        json={"title": "Learn LangGraph", "topic": "AI", "estimated_sessions": 2},
    )
    assert r.status_code == 200
    goal = r.json()
    gid = goal["id"]
    assert goal["status"] == "backlog"
    assert goal["completed_sessions"] == 0

    # log first session -> moves to "learning", schedules a review
    r = await client.post(
        f"/api/v1/learning/goals/{gid}/sessions",
        json={"duration_minutes": 30, "notes": "Read the docs"},
    )
    assert r.status_code == 200

    goals = (await client.get("/api/v1/learning/goals")).json()
    g = next(x for x in goals if x["id"] == gid)
    assert g["completed_sessions"] == 1
    assert g["status"] == "learning"
    assert g["next_review_at"] is not None

    # log second session -> reaches estimated_sessions -> completed
    r = await client.post(
        f"/api/v1/learning/goals/{gid}/sessions",
        json={"duration_minutes": 25},
    )
    assert r.status_code == 200

    goals = (await client.get("/api/v1/learning/goals")).json()
    g = next(x for x in goals if x["id"] == gid)
    assert g["completed_sessions"] == 2
    assert g["status"] == "completed"


@pytest.mark.asyncio
async def test_learning_review_endpoint(client: AsyncClient) -> None:
    r = await client.get("/api/v1/learning/review")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_session_for_missing_goal_404(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/learning/goals/00000000-0000-0000-0000-000000000000/sessions",
        json={"duration_minutes": 10},
    )
    assert r.status_code == 404
