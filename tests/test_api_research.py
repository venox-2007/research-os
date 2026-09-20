"""Integration tests for the research submission API endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_research_question(async_client: AsyncClient) -> None:
    """Verify posting a valid research question creates a record."""
    payload = {
        "query": "How do sparse autoencoders interpret latent features in transformer MLP layers?",
        "discipline": "Interpretability",
        "constraints": ["focus on SAE architectures", "empirical evaluation only"],
    }
    response = await async_client.post("/api/v1/research/question", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["query"] == payload["query"]
    assert data["discipline"] == "Interpretability"
    assert data["status"] == "submitted"
    assert "id" in data

    question_id = data["id"]

    # Test retrieval by ID
    get_res = await async_client.get(f"/api/v1/research/question/{question_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == question_id

    # Test listing questions
    list_res = await async_client.get("/api/v1/research/questions")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_submit_invalid_question(async_client: AsyncClient) -> None:
    """Verify validation error when research query is too short."""
    response = await async_client.post("/api/v1/research/question", json={"query": "ab"})
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "Validation Error"
