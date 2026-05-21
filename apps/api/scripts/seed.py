"""Populate the dev database with a small sample dataset."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.enums import EnergyType, TaskSourceType, TaskStatus
from app.models.project import Project
from app.models.task import Task
from app.services import prioritization
from app.services.users import get_or_create_default_user


SAMPLE_PROJECTS = [
    {"name": "NeuroPlan", "color": "#7c5cff", "description": "Self-hosted productivity OS."},
    {"name": "Learning", "color": "#22d3ee", "description": "Курсы и обучение."},
    {"name": "Life", "color": "#34d399", "description": "Personal errands and habits."},
]


def _sample_tasks(project_ids: dict[str, str]) -> list[dict]:
    now = datetime.now(tz=UTC)
    return [
        {
            "title": "Спроектировать AI extraction pipeline",
            "description": "Sketch pipeline: ingest → chunk → extract → dedupe → save.",
            "project_id": project_ids["NeuroPlan"],
            "status": TaskStatus.PLANNED,
            "due_date": now + timedelta(days=2),
            "importance_score": 0.85,
            "effort_score": 0.7,
            "energy_type": EnergyType.DEEP,
            "estimated_minutes": 120,
        },
        {
            "title": "Сделать дашборд страницы Tasks",
            "description": "List + filters + KPI cards + animations.",
            "project_id": project_ids["NeuroPlan"],
            "status": TaskStatus.ACTIVE,
            "due_date": now + timedelta(hours=8),
            "importance_score": 0.8,
            "effort_score": 0.5,
            "energy_type": EnergyType.DEEP,
            "estimated_minutes": 90,
        },
        {
            "title": "Изучить LangGraph",
            "description": "Прочитать tutorial, собрать demo agent.",
            "project_id": project_ids["Learning"],
            "status": TaskStatus.INBOX,
            "due_date": now + timedelta(days=5),
            "importance_score": 0.7,
            "effort_score": 0.6,
            "energy_type": EnergyType.LEARNING,
            "estimated_minutes": 60,
        },
        {
            "title": "Записаться к врачу",
            "description": "Annual check-up.",
            "project_id": project_ids["Life"],
            "status": TaskStatus.INBOX,
            "due_date": now + timedelta(days=1),
            "importance_score": 0.6,
            "effort_score": 0.2,
            "energy_type": EnergyType.ERRAND,
            "estimated_minutes": 10,
        },
        {
            "title": "Откладываемая задача — оформить документы",
            "description": "Long overdue, has been snoozed.",
            "project_id": project_ids["Life"],
            "status": TaskStatus.SNOOZED,
            "due_date": now - timedelta(days=2),
            "importance_score": 0.5,
            "effort_score": 0.4,
            "estimated_minutes": 45,
        },
    ]


async def run() -> None:
    async with SessionLocal() as session:
        async with session.begin():
            user = await get_or_create_default_user(session)
            existing_projects = {
                p.name: p
                for p in (
                    await session.execute(
                        select(Project).where(Project.owner_id == user.id)
                    )
                ).scalars()
            }
            for sp in SAMPLE_PROJECTS:
                if sp["name"] not in existing_projects:
                    proj = Project(owner_id=user.id, **sp)
                    session.add(proj)
                    await session.flush()
                    existing_projects[sp["name"]] = proj

            project_ids = {n: str(p.id) for n, p in existing_projects.items()}

            existing_titles = {
                t.title
                for t in (
                    await session.execute(select(Task).where(Task.owner_id == user.id))
                ).scalars()
            }
            for st in _sample_tasks(project_ids):
                if st["title"] in existing_titles:
                    continue
                task = Task(
                    owner_id=user.id,
                    source_type=TaskSourceType.MANUAL,
                    **{k: v for k, v in st.items() if k != "project_id"},
                    project_id=st["project_id"],
                )
                prioritization.recompute(task)
                session.add(task)
            print("seed: ok", flush=True)


if __name__ == "__main__":
    asyncio.run(run())
