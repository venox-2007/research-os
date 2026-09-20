"""FastAPI application factory for ResearchOS.

Creates and configures the FastAPI application instance with CORS,
logging, standardized error handling, and versioned routing.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.v1.endpoints.health import router as root_health_router
from backend.api.v1.router import api_v1_router
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger, setup_logging

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager for startup and shutdown routines."""
    settings = app.state.settings
    logger.info(
        "Starting %s v%s in '%s' environment (LLM: %s)",
        settings.app_name,
        settings.app_version,
        settings.app_env,
        settings.llm_provider,
    )
    yield
    logger.info("Shutting down %s...", settings.app_name)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory creating and configuring the primary FastAPI application.

    Args:
        settings: Optional custom Settings instance. Defaults to get_settings().

    Returns:
        Configured FastAPI application instance.
    """
    app_settings = settings or get_settings()
    setup_logging(app_settings.log_level)

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description="Autonomous AI Research Engineer operating under a ₹0-cost constraint.",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.dependency_overrides[get_settings] = lambda: app_settings

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Standardized Exception Handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "status_code": 422,
                "detail": exc.errors(),
                "path": request.url.path,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        logger.info("HTTPException on %s: [%d] %s", request.url.path, exc.status_code, exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Unhandled internal exception on %s: %s", request.url.path, str(exc), exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "status_code": 500,
                "detail": str(exc)
                if app_settings.app_env != "production"
                else "An unexpected error occurred",
                "path": request.url.path,
            },
        )

    # Root health endpoint (/health) for load balancers & quick probes
    app.include_router(root_health_router)

    # Versioned API routes (/api/v1/...)
    app.include_router(api_v1_router)

    @app.get("/", tags=["Root"])
    async def root_index() -> dict:
        """Root endpoint returning basic application information."""
        return {
            "app": app_settings.app_name,
            "version": app_settings.app_version,
            "status": "online",
            "docs": "/docs",
            "health": "/health",
        }

    return app
