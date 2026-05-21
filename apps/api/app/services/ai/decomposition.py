"""AI service for task decomposition."""

from __future__ import annotations

import json
from typing import Any

from app.services.ai.provider import generate_structured
from app.models.task import Task


async def decompose_task(task_title: str, task_description: str | None = None) -> list[dict[str, Any]]:
    """Suggest micro-steps to overcome procrastination on a task."""
    schema = {
        "type": "object",
        "properties": {
            "subtasks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "A very small, actionable first step."},
                        "estimated_minutes": {"type": "integer", "description": "Estimated time (1 to 15 mins)"}
                    },
                    "required": ["title", "estimated_minutes"]
                },
                "minItems": 2,
                "maxItems": 5,
            }
        },
        "required": ["subtasks"]
    }
    
    prompt = f"""
    The user is procrastinating on the following task.
    Title: {task_title}
    Description: {task_description or "None"}
    
    Please break this task down into 2-5 extremely small, low-friction micro-steps to help them regain momentum.
    The first step should ideally take less than 5 minutes.
    """
    
    result = await generate_structured(prompt, schema)
    
    if not result or "subtasks" not in result:
        return []
        
    return result["subtasks"]
