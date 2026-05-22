"""AI-driven Eisenhower classification.

Given the user's open tasks, ask the LLM to assign each an `importance`
and `urgency` score in [0, 1] — the two axes of the Eisenhower matrix.
The endpoint then writes those scores back and recomputes priority.

Falls back to a deterministic heuristic when no AI provider is
configured, so the "Sort with AI" button always does something useful.
"""

from __future__ import annotations

from collections.abc import Sequence

import structlog

from app.models.task import Task
from app.services.ai.provider import generate_structured

log = structlog.get_logger("ai.eisenhower")

MAX_TASKS = 60

_SCHEMA = {
    "assignments": [
        {"id": "string", "importance": "number 0..1", "urgency": "number 0..1"}
    ]
}

_PROMPT_HEADER = (
    "You are a productivity coach applying the Eisenhower matrix.\n"
    "For every task below assign two floats in [0,1]:\n"
    "- importance: how much it advances meaningful goals (impact, not noise).\n"
    "- urgency: how time-critical it is (deadlines, things that decay).\n"
    "Quadrants: importance>=0.5 & urgency>=0.5 = Do First; "
    "importance>=0.5 & urgency<0.5 = Schedule; "
    "importance<0.5 & urgency>=0.5 = Delegate; "
    "importance<0.5 & urgency<0.5 = Eliminate.\n"
    "Be decisive — avoid clustering everything at 0.5. Use the due dates.\n"
    'Return ONLY JSON: {"assignments":[{"id":"<task id>",'
    '"importance":<float>,"urgency":<float>}]}.\n\n'
    "Tasks:\n"
)


def _clamp(v: object) -> float:
    try:
        f = float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(1.0, f))


def _build_prompt(tasks: Sequence[Task]) -> str:
    lines = []
    for t in tasks:
        due = t.due_date.isoformat() if t.due_date else "no deadline"
        desc = (t.description or "").strip().replace("\n", " ")[:160]
        lines.append(
            f"- id={t.id} | title={t.title!r} | due={due} | "
            f"project={'yes' if t.project_id else 'none'} | notes={desc!r}"
        )
    return _PROMPT_HEADER + "\n".join(lines)


async def ai_classify(tasks: Sequence[Task]) -> dict[str, tuple[float, float]]:
    """Return {task_id: (importance, urgency)}. Empty dict if AI unavailable."""
    if not tasks:
        return {}
    subset = list(tasks)[:MAX_TASKS]
    result = await generate_structured(_build_prompt(subset), _SCHEMA)
    if not result or "assignments" not in result:
        log.info("eisenhower.ai_unavailable")
        return {}

    valid_ids = {str(t.id) for t in subset}
    out: dict[str, tuple[float, float]] = {}
    for row in result.get("assignments", []):
        if not isinstance(row, dict):
            continue
        tid = str(row.get("id", ""))
        if tid not in valid_ids:
            continue
        out[tid] = (_clamp(row.get("importance")), _clamp(row.get("urgency")))
    log.info("eisenhower.ai_done", classified=len(out), requested=len(subset))
    return out
