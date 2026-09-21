"""Version 1 API router consolidating health, research, experiments, and RAG endpoints."""

from fastapi import APIRouter

from backend.api.v1.endpoints.experiments import router as experiments_router
from backend.api.v1.endpoints.health import router as health_router
from backend.api.v1.endpoints.papers import router as papers_router
from backend.api.v1.endpoints.rag import router as rag_router
from backend.api.v1.endpoints.reports import router as reports_router
from backend.api.v1.endpoints.research import router as research_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount sub-routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(papers_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(experiments_router)
api_v1_router.include_router(reports_router)
