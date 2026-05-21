"""AI provider abstraction for note extraction.

Phase 3 ships two implementations:

- `OpenAIProvider` — JSON-mode chat completion, returns a list of structured
  entities matching `ExtractedItem`.
- `NullProvider` — no-op fallback used when no API key is configured. The
  ingest pipeline still works (heuristic parser produces candidates).

Switch is config-driven so the rest of the app never depends on the
LLM being present.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Literal

import httpx
import structlog
from pydantic import BaseModel, Field

from app.core.config import get_settings

log = structlog.get_logger("ai.provider")


EntityKind = Literal["task", "event", "idea", "learning", "reference", "info", "reflection"]


class ExtractedItem(BaseModel):
    type: EntityKind
    title: str = Field(min_length=1, max_length=300)
    description: str = ""
    due_at: str | None = None  # ISO-8601 or null
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    tags: list[str] = Field(default_factory=list)
    source_excerpt: str = ""


class AIExtractionResponse(BaseModel):
    items: list[ExtractedItem] = Field(default_factory=list)
    model: str = ""
    used_ai: bool = False


SYSTEM_PROMPT = (
    "You extract actionable items from a personal note. "
    "Return ONLY JSON with the shape "
    '{"items":[{type, title, description, due_at, importance, confidence, tags, source_excerpt}]}. '
    "type ∈ {task, event, idea, learning, reference, info, reflection}. "
    "Only emit items the user clearly intends to act on. "
    "Do NOT invent deadlines: if the note has no explicit date, set due_at=null. "
    "importance and confidence are floats in [0,1]. "
    "Keep source_excerpt verbatim from the note. "
    "Be conservative: prefer fewer high-confidence items over noisy guesses."
)


class AIProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    async def extract(self, *, text: str, context_hints: dict[str, Any] | None = None) -> AIExtractionResponse:
        ...


class NullProvider(AIProvider):
    name = "null"

    async def extract(self, *, text: str, context_hints: dict[str, Any] | None = None) -> AIExtractionResponse:  # noqa: ARG002
        return AIExtractionResponse(items=[], model="null", used_ai=False)


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._endpoint = "https://api.openai.com/v1/chat/completions"

    async def extract(
        self, *, text: str, context_hints: dict[str, Any] | None = None
    ) -> AIExtractionResponse:
        hints = json.dumps(context_hints or {}, ensure_ascii=False)
        user_prompt = (
            f"Heuristic hints (drafts from a regex parser; may be wrong):\n{hints}\n\n"
            f"Note text:\n```\n{text[:8000]}\n```"
        )
        payload = {
            "model": self._model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "authorization": f"Bearer {self._api_key}",
            "content-type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                r = await client.post(self._endpoint, json=payload, headers=headers)
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
        except Exception as e:  # noqa: BLE001
            log.warning("openai.extract_failed", error=str(e))
            return AIExtractionResponse(items=[], model=self._model, used_ai=False)

        try:
            parsed = json.loads(content)
            raw_items = parsed.get("items", [])
        except (ValueError, KeyError):
            log.warning("openai.invalid_json", preview=content[:200])
            return AIExtractionResponse(items=[], model=self._model, used_ai=False)

        items: list[ExtractedItem] = []
        for ri in raw_items:
            try:
                items.append(ExtractedItem.model_validate(ri))
            except Exception as e:  # noqa: BLE001
                log.warning("openai.invalid_item", error=str(e), item=ri)
        return AIExtractionResponse(items=items, model=self._model, used_ai=True)


def get_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.ai_model)
    return NullProvider()
