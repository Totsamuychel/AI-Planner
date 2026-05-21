from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time, timedelta

from app.models.enums import EnergyType, PriorityBucket, TaskStatus
from app.models.task import Task
from app.services.scheduler import build_plan


def _t(title: str, score: float, minutes: int | None = None, status: TaskStatus = TaskStatus.INBOX) -> Task:
    return Task(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        title=title,
        description="",
        status=status,
        priority=PriorityBucket.P2,
        priority_score=score,
        urgency_score=0.5,
        importance_score=0.5,
        effort_score=0.5,
        procrastination_score=0.0,
        snooze_count=0,
        estimated_minutes=minutes,
        energy_type=EnergyType.DEEP,
        meta={},
    )


def test_empty_input_yields_empty_plan() -> None:
    blocks = build_plan(
        tasks=[],
        target_day=date(2026, 5, 21),
        work_start=time(9),
        work_end=time(18),
    )
    assert blocks == []


def test_orders_by_priority_score_desc() -> None:
    tasks = [_t("Low", 0.2, 30), _t("High", 0.9, 30), _t("Mid", 0.5, 30)]
    blocks = build_plan(
        tasks=tasks, target_day=date(2026, 5, 21), work_start=time(9), work_end=time(18)
    )
    assert [b.title for b in blocks] == ["High", "Mid", "Low"]


def test_packs_consecutively_with_breaks() -> None:
    tasks = [_t("A", 0.9, 60), _t("B", 0.8, 60)]
    blocks = build_plan(
        tasks=tasks, target_day=date(2026, 5, 21), work_start=time(9), work_end=time(18)
    )
    assert blocks[0].start == datetime(2026, 5, 21, 9, 0, tzinfo=UTC)
    assert blocks[0].end == datetime(2026, 5, 21, 10, 0, tzinfo=UTC)
    # 5-minute break
    assert blocks[1].start == blocks[0].end + timedelta(minutes=5)


def test_marks_overflow_when_past_work_end() -> None:
    tasks = [_t(f"t{i}", 0.9 - i * 0.01, 90) for i in range(8)]
    blocks = build_plan(
        tasks=tasks, target_day=date(2026, 5, 21), work_start=time(9), work_end=time(13)
    )
    assert any(b.overflow for b in blocks), "expected some blocks to overflow"


def test_skips_done_and_archived() -> None:
    tasks = [_t("a", 0.9, 30, status=TaskStatus.DONE), _t("b", 0.5, 30)]
    blocks = build_plan(
        tasks=tasks, target_day=date(2026, 5, 21), work_start=time(9), work_end=time(18)
    )
    assert [b.title for b in blocks] == ["b"]


def test_default_duration_for_missing_estimate() -> None:
    blocks = build_plan(
        tasks=[_t("x", 0.5, None)],
        target_day=date(2026, 5, 21),
        work_start=time(9),
        work_end=time(18),
    )
    assert (blocks[0].end - blocks[0].start).total_seconds() / 60 == 30
