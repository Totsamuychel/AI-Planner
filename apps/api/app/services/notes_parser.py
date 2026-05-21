"""Heuristic Markdown / Obsidian note parser.

In Phase 2 it produces structured candidates from raw markdown without an LLM.
Phase 3 layers AI-based extraction on top of the same `ExtractedEntity` model.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import yaml

from app.models.notes import EntityType

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
CHECKBOX_RE = re.compile(r"^(?P<indent>\s*)[-*+]\s*\[(?P<mark> |x|X)\]\s*(?P<text>.+?)\s*$", re.MULTILINE)
TAG_RE = re.compile(r"(?<![\w/])#([A-Za-zА-Яа-я0-9][\w/-]*)")
WIKILINK_RE = re.compile(r"\[\[([^\[\]\n]+?)\]\]")
ISO_DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}(?::\d{2})?))?\b")
EU_DATE_RE = re.compile(r"\b(\d{1,2})[./](\d{1,2})[./](\d{2,4})\b")
DUE_HINT_RE = re.compile(
    r"\b(?:до|by|due|deadline|к)\b\s+([^\n.;,]+?)(?:[\n.;,]|$)", re.IGNORECASE,
)

COMMITMENT_VERBS = (
    "нужно", "надо", "должен", "должна", "сделать", "написать", "позвонить",
    "встретиться", "купить", "заказать", "оплатить", "отправить", "подготовить",
    "todo", "must", "should", "need to", "have to", "remember to", "buy",
    "call", "email", "send", "prepare", "finish", "fix",
)
LEARNING_HINTS = ("learn", "study", "read", "course", "lesson", "урок", "изучить", "почитать", "курс")
EVENT_HINTS = ("meeting", "event", "встреча", "митинг", "созвон", "звонок", "demo", "presentation")


@dataclass
class Candidate:
    """A structured fragment surfaced from a note."""
    entity_type: EntityType
    title: str
    content: str = ""
    source_excerpt: str = ""
    source_line: int | None = None
    confidence: float = 0.5
    normalized: dict[str, Any] = field(default_factory=dict)

    def dedupe_key(self, doc_path: str) -> str:
        raw = f"{doc_path}|{self.entity_type}|{self.title.strip().lower()}|{self.source_line or ''}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:32]


@dataclass
class ParsedNote:
    title: str
    frontmatter: dict[str, Any]
    raw_text: str
    word_count: int
    candidates: list[Candidate]


def _try_parse_date(value: str) -> str | None:
    value = value.strip()
    m = ISO_DATE_RE.search(value)
    if m:
        d, t = m.group(1), m.group(2)
        return f"{d}T{t}:00" if t and len(t) == 5 else (f"{d}T{t}" if t else f"{d}T09:00:00")
    m = EU_DATE_RE.search(value)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        if len(year) == 2:
            year = "20" + year
        try:
            d = date(int(year), int(month), int(day))
        except ValueError:
            return None
        return f"{d.isoformat()}T09:00:00"
    return None


def _classify_text(text: str) -> tuple[EntityType, float]:
    lower = text.lower()
    if any(h in lower for h in EVENT_HINTS):
        return EntityType.EVENT, 0.7
    if any(h in lower for h in LEARNING_HINTS):
        return EntityType.LEARNING, 0.7
    if any(v in lower for v in COMMITMENT_VERBS):
        return EntityType.TASK, 0.7
    return EntityType.IDEA, 0.4


def parse_markdown(text: str, *, file_path: str) -> ParsedNote:
    frontmatter: dict[str, Any] = {}
    body = text
    m = FRONTMATTER_RE.match(text)
    if m:
        try:
            parsed = yaml.safe_load(m.group(1)) or {}
            if isinstance(parsed, dict):
                frontmatter = parsed
        except yaml.YAMLError:
            frontmatter = {}
        body = text[m.end() :]

    title = str(frontmatter.get("title") or "")
    if not title:
        h = HEADING_RE.search(body)
        if h:
            title = h.group(2).strip()
        else:
            title = file_path.rsplit("/", 1)[-1].removesuffix(".md")

    candidates: list[Candidate] = []
    lines = body.splitlines()

    # 1. checkbox tasks
    for m in CHECKBOX_RE.finditer(body):
        raw_text = m.group("text").strip()
        if not raw_text:
            continue
        line_no = body[: m.start()].count("\n") + 1
        tags = TAG_RE.findall(raw_text)
        wiki = WIKILINK_RE.findall(raw_text)
        clean = TAG_RE.sub("", raw_text).strip()
        clean = WIKILINK_RE.sub(r"\1", clean).strip()
        due_iso = _detect_due(raw_text)
        checked = m.group("mark").lower() == "x"
        cand = Candidate(
            entity_type=EntityType.TASK,
            title=clean[:300] or raw_text[:300],
            content=raw_text,
            source_excerpt=raw_text,
            source_line=line_no,
            confidence=0.92 if not checked else 0.5,
            normalized={
                "due_at": due_iso,
                "tags": tags,
                "wikilinks": wiki,
                "completed": checked,
            },
        )
        candidates.append(cand)

    # 2. heading-level commitments / events
    for h in HEADING_RE.finditer(body):
        text_h = h.group(2).strip()
        if not text_h:
            continue
        kind, conf = _classify_text(text_h)
        if kind in (EntityType.TASK, EntityType.EVENT, EntityType.LEARNING):
            line_no = body[: h.start()].count("\n") + 1
            candidates.append(
                Candidate(
                    entity_type=kind,
                    title=text_h[:300],
                    content="",
                    source_excerpt=lines[line_no - 1] if line_no - 1 < len(lines) else text_h,
                    source_line=line_no,
                    confidence=conf,
                    normalized={"due_at": _detect_due(text_h)},
                )
            )

    # 3. commitment sentences in body text
    for i, line in enumerate(lines, start=1):
        s = line.strip()
        if not s or s.startswith("#") or CHECKBOX_RE.match(line):
            continue
        if len(s) < 8 or len(s) > 240:
            continue
        kind, conf = _classify_text(s)
        if kind == EntityType.IDEA:
            continue
        candidates.append(
            Candidate(
                entity_type=kind,
                title=s[:300],
                content="",
                source_excerpt=s,
                source_line=i,
                confidence=max(0.4, conf - 0.15),  # body-text matches are noisier than checkboxes
                normalized={"due_at": _detect_due(s)},
            )
        )

    word_count = len(body.split())
    return ParsedNote(
        title=title.strip(),
        frontmatter=frontmatter,
        raw_text=text,
        word_count=word_count,
        candidates=candidates,
    )


def _detect_due(text: str) -> str | None:
    m = DUE_HINT_RE.search(text)
    if m:
        d = _try_parse_date(m.group(1))
        if d:
            return d
    return _try_parse_date(text)


def file_checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
