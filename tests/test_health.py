"""Tests for application health and root endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(async_client: AsyncClient) -> None:
    """Verify root endpoint returns application metadata."""
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "ResearchOS-Test"
    assert data["status"] == "online"
    assert data["docs"] == "/docs"
    assert data["health"] == "/health"


@pytest.mark.asyncio
async def test_health_root_endpoint(async_client: AsyncClient) -> None:
    """Verify /health endpoint returns healthy status and metadata."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0-test"
    assert data["environment"] == "testing"
    assert data["llm_provider"] == "mock"
    assert data["llm_available"] is True
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_v1_endpoint(async_client: AsyncClient) -> None:
    """Verify /api/v1/health endpoint functions equivalently."""
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["llm_provider"] == "mock"
