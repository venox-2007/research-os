"""Unit tests for configuration management."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.core.config import Settings


def test_default_settings() -> None:
    """Verify default settings reflect zero-cost local operation."""
    settings = Settings()
    assert settings.app_name == "ResearchOS"
    assert settings.app_env in {"development", "testing", "production"}
    assert settings.llm_provider == "mock"
    assert settings.api_port == 8000
    assert "http://localhost:5173" in settings.cors_origins


def test_custom_settings(tmp_path: Path) -> None:
    """Verify settings overrides and directory auto-creation."""
    custom_data = tmp_path / "custom_data"
    settings = Settings(
        app_env="testing",
        log_level="WARNING",
        api_port=9000,
        data_dir=custom_data,
    )
    assert settings.app_env == "testing"
    assert settings.log_level == "WARNING"
    assert settings.api_port == 9000
    settings.ensure_directories()
    assert custom_data.exists()


def test_invalid_log_level() -> None:
    """Verify validation fails on invalid log level."""
    with pytest.raises(ValidationError):
        Settings(log_level="INVALID_LEVEL")


def test_invalid_app_env() -> None:
    """Verify validation fails on invalid environment name."""
    with pytest.raises(ValidationError):
        Settings(app_env="staging_unsupported")
