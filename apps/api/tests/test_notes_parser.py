from __future__ import annotations

from app.models.notes import EntityType
from app.services.notes_parser import file_checksum, parse_markdown


def test_parses_frontmatter_and_title() -> None:
    md = """---
title: Daily Plan
tags: [work, ml]
---

# Daily Plan

Some intro.
"""
    p = parse_markdown(md, file_path="daily.md")
    assert p.frontmatter["title"] == "Daily Plan"
    assert p.title == "Daily Plan"


def test_checkbox_becomes_task_candidate() -> None:
    md = "# Notes\n\n- [ ] Review ML pipeline #work до 2026-05-25\n- [x] Buy milk\n"
    p = parse_markdown(md, file_path="n.md")
    tasks = [c for c in p.candidates if c.entity_type == EntityType.TASK]
    assert len(tasks) >= 2
    open_task = next(c for c in tasks if "Review" in c.title)
    assert open_task.confidence > 0.8
    assert open_task.normalized.get("tags") == ["work"]
    assert open_task.normalized.get("due_at", "").startswith("2026-05-25")


def test_event_heading_classification() -> None:
    md = "## Meeting with team\n\nDiscuss roadmap.\n"
    p = parse_markdown(md, file_path="n.md")
    assert any(c.entity_type == EntityType.EVENT for c in p.candidates)


def test_learning_classification() -> None:
    md = "Need to learn LangGraph this week.\n"
    p = parse_markdown(md, file_path="n.md")
    assert any(c.entity_type == EntityType.LEARNING for c in p.candidates)


def test_checksum_stable() -> None:
    a = file_checksum("hello world")
    b = file_checksum("hello world")
    assert a == b
    assert len(a) == 64


def test_dedupe_keys_differ() -> None:
    md = "- [ ] One thing\n- [ ] Another thing\n"
    p = parse_markdown(md, file_path="x.md")
    keys = {c.dedupe_key("x.md") for c in p.candidates}
    assert len(keys) == len(p.candidates)
