"""Integration tests for the /api/v1/papers search and ingestion endpoints."""

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from backend.core.models import Source
from backend.ingestion.models import DocumentChunk, IngestionResult, ParsedDocument, ParsedPage


@pytest.mark.asyncio
async def test_search_papers_endpoint_arxiv(async_client: AsyncClient) -> None:
    """Verify paper search endpoint with arXiv provider."""
    mock_sources = [
        Source(
            title="Transformer Scaling",
            authors=["Alice", "Bob"],
            source_type="arxiv",
            metadata={"arxiv_id": "2401.12345"},
        )
    ]

    with patch(
        "backend.api.v1.endpoints.papers.ArxivClient.search", new_callable=AsyncMock
    ) as mock_search:
        mock_search.return_value = mock_sources
        response = await async_client.get(
            "/api/v1/papers/search",
            params={"query": "Transformer", "provider": "arxiv", "limit": 5},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Transformer Scaling"


@pytest.mark.asyncio
async def test_search_papers_endpoint_invalid_provider(async_client: AsyncClient) -> None:
    """Verify unsupported provider returns 400 error."""
    response = await async_client.get(
        "/api/v1/papers/search",
        params={"query": "AI", "provider": "unsupported_provider"},
    )
    assert response.status_code == 400
    assert "Unsupported provider" in response.json()["error"]


@pytest.mark.asyncio
async def test_ingest_paper_endpoint(async_client: AsyncClient) -> None:
    """Verify paper ingestion endpoint parses and returns IngestionResult."""
    mock_result = IngestionResult(
        source=Source(title="Ingested Test", url="https://arxiv.org/pdf/2401.00001.pdf"),
        document=ParsedDocument(
            document_id="doc_2401.00001",
            source_id=Source(title="").id,
            title="Ingested Test",
            total_pages=1,
            pages=[ParsedPage(page_number=1, text="Test text", char_count=9)],
        ),
        chunks=[
            DocumentChunk(
                chunk_id="doc_2401.00001_c001",
                document_id="doc_2401.00001",
                source_id=Source(title="").id,
                start_page=1,
                end_page=1,
                text="Test text",
                char_count=9,
                estimated_tokens=2,
            )
        ],
        pdf_path="/fake/path.pdf",
        cached=False,
    )

    with patch(
        "backend.api.v1.endpoints.papers.IngestionPipeline.ingest_url", new_callable=AsyncMock
    ) as mock_ingest:
        mock_ingest.return_value = mock_result
        response = await async_client.post(
            "/api/v1/papers/ingest",
            json={"url": "https://arxiv.org/pdf/2401.00001.pdf", "title": "Ingested Test"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["document"]["document_id"] == "doc_2401.00001"
    assert len(data["chunks"]) == 1


@pytest.mark.asyncio
async def test_get_paper_chunks_404(async_client: AsyncClient) -> None:
    """Verify querying non-existent chunks returns 404."""
    response = await async_client.get("/api/v1/papers/nonexistent_paper_id/chunks")
    assert response.status_code == 404
    assert "not found" in response.json()["error"].lower()
