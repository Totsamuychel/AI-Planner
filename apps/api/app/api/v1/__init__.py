from fastapi import APIRouter

from app.api.v1 import analytics, health, learning, notes, notifications, projects, schedule, settings, tasks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(projects.router)
api_router.include_router(notes.router)
api_router.include_router(schedule.router)
api_router.include_router(analytics.router)
api_router.include_router(notifications.router)
api_router.include_router(settings.router)
api_router.include_router(learning.router)


