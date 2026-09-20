"""Centralized configuration management for ResearchOS.

Loads environment variables from `.env` or system environment, with
safe, zero-cost defaults suitable for offline development and testing.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings for ResearchOS.

    Configured via environment variables or `.env` file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application metadata
    app_name: str = Field(default="ResearchOS", description="Application display name")
    app_version: str = Field(default="0.1.0", description="Semantic version")
    app_env: str = Field(
        default="development", description="Environment: development, testing, production"
    )
    log_level: str = Field(default="INFO", description="Logging verbosity")

    # API Server configuration
    api_host: str = Field(default="127.0.0.1", description="Host address for FastAPI server")
    api_port: int = Field(default=8000, description="Port for FastAPI server")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        description="Allowed CORS origins for the API",
    )

    # LLM Provider configuration
    # Default 'mock' ensures zero cost and zero external dependencies
    llm_provider: str = Field(
        default="mock",
        description="Active LLM provider: mock, ollama, or gemini",
    )
    local_model_name: str = Field(
        default="llama3.2",
        description="Default local model tag (for Ollama)",
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Base URL for local Ollama daemon",
    )
    gemini_api_key: str | None = Field(
        default=None,
        description="Optional Gemini API key for free-tier usage",
    )

    # Local storage paths (all kept local, zero-cost)
    data_dir: Path = Field(default=Path("./data"), description="Base local data storage")
    cache_dir: Path = Field(default=Path("./data/cache"), description="Local cache directory")
    experiments_dir: Path = Field(
        default=Path("./data/experiments"),
        description="Directory for local experiment sandboxes",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate and normalize log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = value.upper()
        if normalized not in valid_levels:
            raise ValueError(f"Invalid log_level '{value}'. Must be one of {valid_levels}")
        return normalized

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        """Validate application environment."""
        valid_envs = {"development", "testing", "production"}
        normalized = value.lower()
        if normalized not in valid_envs:
            raise ValueError(f"Invalid app_env '{value}'. Must be one of {valid_envs}")
        return normalized

    def ensure_directories(self) -> None:
        """Ensure that required local directories exist on the filesystem."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached instance of the application settings."""
    settings = Settings()
    settings.ensure_directories()
    return settings
