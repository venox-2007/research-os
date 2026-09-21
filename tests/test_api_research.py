"""Integration tests for research submission and autonomous agent execution endpoints."""

from uuid import uuid4

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


@pytest.mark.asyncio
async def test_execute_research_run(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/research/run triggers autonomous agent workflow."""
    payload = {
        "question": "What are the computational trade-offs of hybrid RAG vs dense-only retrieval?",
        "discipline": "Information Retrieval",
        "constraints": ["Focus on latency and reciprocal rank fusion."],
        "max_iterations": 2,
    }
    response = await async_client.post("/api/v1/research/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "completed"
    assert data["question"] == payload["question"]
    assert "run_id" in data
    assert data["iteration_count"] >= 1
    assert data["tasks_completed"] >= 1
    assert len(data["verified_evidence"]) > 0
    assert len(data["trace"]) >= 4

    run_id = data["run_id"]

    # Test retrieving research run by ID
    get_res = await async_client.get(f"/api/v1/research/run/{run_id}")
    assert get_res.status_code == 200
    run_data = get_res.json()
    assert run_data["run_id"] == run_id
    assert run_data["question"] == payload["question"]
    assert run_data["tasks_completed"] == data["tasks_completed"]


@pytest.mark.asyncio
async def test_get_nonexistent_research_run(async_client: AsyncClient) -> None:
    """Verify 404 for invalid research run ID."""
    random_id = uuid4()
    response = await async_client.get(f"/api/v1/research/run/{random_id}")
    assert response.status_code == 404
