import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root(client: AsyncClient) -> None:
    r = await client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "neuroplan-api"


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
