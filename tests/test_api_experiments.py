"""Integration tests for experiment engine REST API endpoints."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_plan_and_run_experiment_api(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/experiments/plan and POST /api/v1/experiments/run."""
    # 1. Plan experiment
    plan_payload = {
        "task_title": "Benchmark linear model performance on synthetic features",
        "hypothesis": "Feature coefficients reflect generation weights.",
    }
    plan_resp = await async_client.post("/api/v1/experiments/plan", json=plan_payload)
    assert plan_resp.status_code == 201
    spec_data = plan_resp.json()
    assert spec_data["is_executable"] is True
    assert "experiment_id" in spec_data
    exp_id = spec_data["experiment_id"]

    # 2. Retrieve planned spec
    get_spec = await async_client.get(f"/api/v1/experiments/{exp_id}")
    assert get_spec.status_code == 200
    assert get_spec.json()["experiment_id"] == exp_id

    # 3. Execute experiment
    run_resp = await async_client.post(
        "/api/v1/experiments/run",
        json={"experiment_id": exp_id},
    )
    assert run_resp.status_code == 200
    res_data = run_resp.json()
    assert res_data["status"] == "completed"
    assert len(res_data["metrics"]) >= 3
    assert len(res_data["artifacts"]) >= 2

    # 4. Retrieve results
    res_get = await async_client.get(f"/api/v1/experiments/{exp_id}/results")
    assert res_get.status_code == 200
    assert res_get.json()["status"] == "completed"

    # 5. List artifacts
    art_get = await async_client.get(f"/api/v1/experiments/{exp_id}/artifacts")
    assert art_get.status_code == 200
    assert len(art_get.json()) >= 2


@pytest.mark.asyncio
async def test_catalog_endpoints(async_client: AsyncClient) -> None:
    """Verify listing functions and datasets from catalogs."""
    func_resp = await async_client.get("/api/v1/experiments/catalog/functions")
    assert func_resp.status_code == 200
    funcs = func_resp.json()
    assert len(funcs) >= 5

    data_resp = await async_client.get("/api/v1/experiments/catalog/datasets")
    assert data_resp.status_code == 200
    datasets = data_resp.json()
    assert len(datasets) >= 3


@pytest.mark.asyncio
async def test_get_nonexistent_experiment(async_client: AsyncClient) -> None:
    """Verify 404 on missing experiment."""
    random_id = uuid4()
    resp = await async_client.get(f"/api/v1/experiments/{random_id}")
    assert resp.status_code == 404
