from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.models.enums import PriorityBucket, TaskStatus
from app.models.task import Task
from app.services import prioritization


def _make_task(**overrides) -> Task:
    base = dict(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        title="t",
        description="",
        status=TaskStatus.INBOX,
        priority=PriorityBucket.P3,
        importance_score=0.5,
        effort_score=0.5,
        urgency_score=0.0,
        priority_score=0.0,
        procrastination_score=0.0,
        snooze_count=0,
        meta={},
    )
    base.update(overrides)
    return Task(**base)


def test_urgency_overdue_is_max() -> None:
    past = datetime.now(tz=UTC) - timedelta(hours=1)
    assert prioritization.urgency_from_due(past) == 1.0


def test_no_due_is_low() -> None:
    assert prioritization.urgency_from_due(None) < 0.2


def test_recompute_assigns_bucket() -> None:
    t = _make_task(due_date=datetime.now(tz=UTC) + timedelta(hours=2), importance_score=0.9)
    prioritization.recompute(t)
    assert t.priority == PriorityBucket.P0
    assert 0 <= t.priority_score <= 1


def test_snooze_boost() -> None:
    a = _make_task(snooze_count=0, importance_score=0.5)
    b = _make_task(snooze_count=4, importance_score=0.5)
    prioritization.recompute(a)
    prioritization.recompute(b)
    assert b.priority_score >= a.priority_score
