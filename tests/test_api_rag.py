"""API endpoint tests for /api/v1/rag and /api/v1/evidence."""

from uuid import uuid4

import pytest
from httpx import AsyncClient

from backend.core.config import Settings
from backend.core.models import Evidence
from backend.evidence.store import SQLiteEvidenceStore


@pytest.mark.asyncio
async def test_rag_stats_endpoint(async_client: AsyncClient):
    resp = await async_client.get("/api/v1/rag/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "dense_index_count" in data
    assert "bm25_index_count" in data
    assert "evidence_count" in data
    assert "embedding_model" in data


@pytest.mark.asyncio
async def test_rag_search_empty_index(async_client: AsyncClient):
    resp = await async_client.post(
        "/api/v1/rag/search",
        json={"query": "transformer attention", "top_k": 5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["query"] == "transformer attention"
    assert "results" in data
    assert "diagnostics" in data


@pytest.mark.asyncio
async def test_evidence_endpoints(async_client: AsyncClient, test_settings: Settings):
    store = SQLiteEvidenceStore(db_path=test_settings.evidence_db_path)
    source_id = uuid4()
    ev = Evidence(
        chunk_id="api-test-chunk-1",
        source_id=source_id,
        source_title="API Test Paper",
        content="Evidence content for endpoint verification.",
        confidence_score=0.88,
        section="Results",
        page_numbers=[4],
        provenance_summary="API Test Paper (p. 4, Results)",
    )
    saved_id = store.save_evidence(ev)

    # Test GET /api/v1/evidence
    list_resp = await async_client.get("/api/v1/evidence")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) >= 1
    assert any(item["chunk_id"] == "api-test-chunk-1" for item in list_data)

    # Test GET /api/v1/evidence/{evidence_id}
    single_resp = await async_client.get(f"/api/v1/evidence/{saved_id}")
    assert single_resp.status_code == 200
    single_data = single_resp.json()
    assert single_data["id"] == str(saved_id)
    assert single_data["confidence_score"] == 0.88
    assert single_data["source_title"] == "API Test Paper"

    # Test 404 for unknown evidence
    fake_id = uuid4()
    not_found_resp = await async_client.get(f"/api/v1/evidence/{fake_id}")
    assert not_found_resp.status_code == 404
