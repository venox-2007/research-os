"""ResearchOS application server entrypoint."""

import uvicorn

from backend.core.config import get_settings


def main() -> None:
    """Run the Uvicorn ASGI server using settings from environment."""
    settings = get_settings()
    uvicorn.run(
        "backend.core.app:create_app",
        factory=True,
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
