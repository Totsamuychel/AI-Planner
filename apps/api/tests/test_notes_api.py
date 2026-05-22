from __future__ import annotations

import pytest
from httpx import AsyncClient

SAMPLE_NOTE = """---
title: Test Note
---
# Test Note

- [ ] Buy groceries #errand
- [ ] Prepare ML pipeline review до 2026-06-01
- [x] Already done

## Meeting with team
Discuss the roadmap.
"""


@pytest.mark.asyncio
async def test_notes_ingest_and_accept(client: AsyncClient, tmp_path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "note.md").write_text(SAMPLE_NOTE, encoding="utf-8")

    # create source
    r = await client.post(
        "/api/v1/notes/sources",
        json={"name": "Test Vault", "path": str(vault), "type": "obsidian"},
    )
    assert r.status_code == 201
    source = r.json()
    assert source["path"] == str(vault)

    # sync
    r = await client.post("/api/v1/notes/sync")
    assert r.status_code == 200
    stats = r.json()["sources"]["Test Vault"]
    assert stats["files_indexed"] == 1
    assert stats["entities_created"] >= 1

    # inbox populated
    r = await client.get("/api/v1/notes/inbox")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    entity_id = items[0]["id"]

    # accept -> promoted to a task
    r = await client.post(f"/api/v1/notes/inbox/{entity_id}/accept")
    assert r.status_code == 200
    task = r.json()
    assert task["source_type"] == "note"

    # accepting again is a conflict
    r = await client.post(f"/api/v1/notes/inbox/{entity_id}/accept")
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_notes_sync_is_idempotent(client: AsyncClient, tmp_path) -> None:
    vault = tmp_path / "v2"
    vault.mkdir()
    (vault / "n.md").write_text(SAMPLE_NOTE, encoding="utf-8")
    await client.post(
        "/api/v1/notes/sources",
        json={"name": "Idem", "path": str(vault), "type": "obsidian"},
    )

    first = (await client.post("/api/v1/notes/sync")).json()["sources"]["Idem"]
    second = (await client.post("/api/v1/notes/sync")).json()["sources"]["Idem"]
    # Unchanged files are not re-indexed and produce no new entities.
    assert first["files_indexed"] == 1
    assert second["files_indexed"] == 0
    assert second["entities_created"] == 0


@pytest.mark.asyncio
async def test_reject_entity(client: AsyncClient, tmp_path) -> None:
    vault = tmp_path / "v3"
    vault.mkdir()
    (vault / "n.md").write_text(SAMPLE_NOTE, encoding="utf-8")
    await client.post(
        "/api/v1/notes/sources",
        json={"name": "Rej", "path": str(vault), "type": "obsidian"},
    )
    await client.post("/api/v1/notes/sync")
    entity_id = (await client.get("/api/v1/notes/inbox")).json()["items"][0]["id"]

    r = await client.post(f"/api/v1/notes/inbox/{entity_id}/reject")
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
