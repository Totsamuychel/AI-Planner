from __future__ import annotations

from datetime import date, timedelta

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_subscription_crud(client: AsyncClient) -> None:
    next_date = (date.today() + timedelta(days=10)).isoformat()
    r = await client.post(
        "/api/v1/subscriptions",
        json={
            "name": "Netflix",
            "amount": 15.99,
            "currency": "USD",
            "billing_period": "monthly",
            "next_billing_date": next_date,
            "notify_days_before": 1,
        },
    )
    assert r.status_code == 201
    sub = r.json()
    sid = sub["id"]
    assert sub["name"] == "Netflix"
    assert sub["active"] is True

    r = await client.get("/api/v1/subscriptions")
    assert r.status_code == 200
    assert any(s["id"] == sid for s in r.json())

    r = await client.patch(f"/api/v1/subscriptions/{sid}", json={"amount": 17.99})
    assert r.status_code == 200
    assert float(r.json()["amount"]) == 17.99

    r = await client.delete(f"/api/v1/subscriptions/{sid}")
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_summary_normalizes_to_month(client: AsyncClient) -> None:
    next_date = (date.today() + timedelta(days=5)).isoformat()
    await client.post(
        "/api/v1/subscriptions",
        json={
            "name": "Yearly Premium",
            "amount": 120.0,
            "currency": "USD",
            "billing_period": "yearly",
            "next_billing_date": next_date,
        },
    )
    r = await client.get("/api/v1/subscriptions/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["active_count"] == 1
    # yearly / 12 == 10/mo
    assert abs(body["monthly_total"] - 10.0) < 0.01
    assert len(body["upcoming"]) == 1  # within 7 days


@pytest.mark.asyncio
async def test_dispatch_runs_without_telegram(client: AsyncClient) -> None:
    """dispatch returns 0 sent when no Telegram token / chat is configured."""
    next_date = date.today().isoformat()
    await client.post(
        "/api/v1/subscriptions",
        json={
            "name": "Spotify",
            "amount": 9.99,
            "currency": "USD",
            "billing_period": "monthly",
            "next_billing_date": next_date,
            "notify_days_before": 1,
        },
    )
    r = await client.post("/api/v1/subscriptions/dispatch-notifications")
    assert r.status_code == 200
    body = r.json()
    assert body["sent"] == 0
    assert "advanced" in body


@pytest.mark.asyncio
async def test_google_status_inert_when_unconfigured(client: AsyncClient) -> None:
    r = await client.get("/api/v1/google/status")
    assert r.status_code == 200
    body = r.json()
    assert body["configured"] is False
    assert body["connected"] is False
