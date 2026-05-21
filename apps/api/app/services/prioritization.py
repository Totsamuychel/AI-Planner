"""Prioritization engine.

Phase 1 implements the baseline scoring described in WORK.md §7.
Later phases (anti-procrastination, scheduling) extend it.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.enums import PriorityBucket
from app.models.task import Task

WEIGHTS = {
    "urgency": 0.35,
    "importance": 0.30,
    "effort": 0.10,
    "strategic": 0.10,
    "procrastination": 0.15,
}


def urgency_from_due(due: datetime | None, now: datetime | None = None) -> float:
    if due is None:
        return 0.1
    now = now or datetime.now(tz=UTC)
    if due.tzinfo is None:
        due = due.replace(tzinfo=UTC)
    hours = (due - now).total_seconds() / 3600
    if hours <= 0:
        return 1.0
    if hours <= 6:
        return 0.95
    if hours <= 24:
        return 0.85
    if hours <= 72:
        return 0.6
    if hours <= 24 * 7:
        return 0.4
    return 0.2


def compute_procrastination_score(task: Task, *, now: datetime | None = None) -> float:
    now = now or datetime.now(tz=UTC)
    snooze_penalty = min(0.5, (task.snooze_count or 0) * 0.1)

    created = task.created_at or now
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
        
    age_days = max(0, (now - created).total_seconds() / 86400)
    time_penalty = min(0.5, age_days / 30.0)
    
    return min(1.0, snooze_penalty + time_penalty)


def compute_priority_score(task: Task, *, now: datetime | None = None) -> float:
    urgency = urgency_from_due(task.due_date, now=now)
    importance = float(task.importance_score or 0.0)
    effort_inverse = 1.0 - float(task.effort_score or 0.0)
    strategic = 1.0 if task.project_id else 0.3

    procrastination_recovery = min(1.0, (task.snooze_count or 0) * 0.15)

    score = (
        urgency * WEIGHTS["urgency"]
        + importance * WEIGHTS["importance"]
        + effort_inverse * WEIGHTS["effort"]
        + strategic * WEIGHTS["strategic"]
        + procrastination_recovery * WEIGHTS["procrastination"]
    )
    return round(max(0.0, min(1.0, score)), 4)


def bucket_from_score(score: float, *, has_due_soon: bool = False) -> PriorityBucket:
    if score >= 0.8 or has_due_soon:
        return PriorityBucket.P0
    if score >= 0.65:
        return PriorityBucket.P1
    if score >= 0.45:
        return PriorityBucket.P2
    if score >= 0.25:
        return PriorityBucket.P3
    return PriorityBucket.P4


def recompute(task: Task, *, now: datetime | None = None) -> None:
    """Mutate task in place — sets urgency_score, priority_score, priority."""
    now = now or datetime.now(tz=UTC)
    urgency = urgency_from_due(task.due_date, now=now)
    task.urgency_score = urgency
    task.procrastination_score = compute_procrastination_score(task, now=now)
    task.priority_score = compute_priority_score(task, now=now)
    task.priority = bucket_from_score(task.priority_score, has_due_soon=urgency >= 0.95)
