"""Health check endpoint providing runtime status and configuration metadata."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends

from backend.core.config import Settings, get_settings
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=dict[str, Any])
async def check_health(
    settings: Settings = Depends(get_settings),
    llm_provider: BaseLLMProvider = Depends(get_llm_provider),
) -> dict[str, Any]:
    """Return health status, environment, version, and LLM readiness."""
    is_llm_ready = await llm_provider.is_available()

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "llm_provider": llm_provider.provider_name,
        "llm_available": is_llm_ready,
        "timestamp": datetime.now(UTC).isoformat(),
    }
