from __future__ import annotations

from app.services.ai.provider import (
    AIExtractionResponse,
    AIProvider,
    ExtractedItem,
    NullProvider,
)


class StubProvider(AIProvider):
    name = "stub"

    def __init__(self, items: list[ExtractedItem]) -> None:
        self._items = items

    async def extract(self, *, text, context_hints=None):  # noqa: ARG002
        return AIExtractionResponse(items=self._items, model="stub", used_ai=True)


async def test_null_provider_returns_empty() -> None:
    p = NullProvider()
    r = await p.extract(text="anything")
    assert r.items == []
    assert r.used_ai is False


async def test_extracted_item_validates_fields() -> None:
    it = ExtractedItem(type="task", title="Do laundry", confidence=0.9, importance=0.4)
    assert it.type == "task"
    assert 0 <= it.confidence <= 1


async def test_stub_provider_round_trip() -> None:
    items = [ExtractedItem(type="event", title="Call Dad", confidence=0.85, due_at="2026-05-22T18:00:00")]
    p = StubProvider(items)
    r = await p.extract(text="...")
    assert r.used_ai is True
    assert r.items[0].title == "Call Dad"
    assert r.items[0].due_at == "2026-05-22T18:00:00"
