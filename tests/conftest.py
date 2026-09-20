"""Pytest test suite configuration and fixtures for ResearchOS."""

from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.core.app import create_app
from backend.core.config import Settings
from backend.llm.mock import MockLLMProvider


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    """Create a temporary isolated Settings instance for testing."""
    return Settings(
        app_name="ResearchOS-Test",
        app_version="0.1.0-test",
        app_env="testing",
        log_level="DEBUG",
        llm_provider="mock",
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        experiments_dir=tmp_path / "experiments",
    )


@pytest.fixture
def test_app(test_settings: Settings) -> FastAPI:
    """Create FastAPI application with test configuration."""
    return create_app(test_settings)


@pytest_asyncio.fixture
async def async_client(test_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Provide an asynchronous HTTP test client bound to test_app."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def mock_llm() -> MockLLMProvider:
    """Provide a direct MockLLMProvider instance for unit tests."""
    return MockLLMProvider(default_response="Test synthesis response")
