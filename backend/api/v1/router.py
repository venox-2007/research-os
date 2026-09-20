"""Version 1 API router consolidating health, research, and future endpoints."""

from fastapi import APIRouter

from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.research import router as research_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(research_router)
