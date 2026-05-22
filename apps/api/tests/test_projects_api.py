from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_project_crud_flow(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/projects",
        json={"name": "Side project", "color": "#34d399"},
    )
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["name"] == "Side project"

    r = await client.get("/api/v1/projects")
    assert r.status_code == 200
    assert any(p["id"] == pid for p in r.json())

    r = await client.patch(f"/api/v1/projects/{pid}", json={"name": "Renamed"})
    assert r.status_code == 200
    assert r.json()["name"] == "Renamed"

    r = await client.delete(f"/api/v1/projects/{pid}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_task_can_link_to_project(client: AsyncClient) -> None:
    pid = (
        await client.post("/api/v1/projects", json={"name": "Linked"})
    ).json()["id"]
    r = await client.post(
        "/api/v1/tasks", json={"title": "In a project", "project_id": pid}
    )
    assert r.status_code == 201
    assert r.json()["project_id"] == pid


@pytest.mark.asyncio
async def test_update_missing_project_404(client: AsyncClient) -> None:
    r = await client.patch(
        "/api/v1/projects/00000000-0000-0000-0000-000000000000",
        json={"name": "x"},
    )
    assert r.status_code == 404
