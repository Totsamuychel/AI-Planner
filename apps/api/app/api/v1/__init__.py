from fastapi import APIRouter

from app.api.v1 import analytics, health, projects, tasks

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(projects.router)
api_router.include_router(analytics.router)
