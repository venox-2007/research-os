"""Deterministic offline unit tests for the Semantic Scholar client."""

import httpx
import pytest

from backend.tools.semantic_scholar import (
    SemanticScholarAPIError,
    SemanticScholarClient,
    SemanticScholarRateLimitError,
)

SAMPLE_S2_PAYLOAD = {
    "total": 1,
    "offset": 0,
    "data": [
        {
            "paperId": "649def34f8be52c8b66281af98ae772c99cfd5b3",
            "title": "Language Models are Few-Shot Learners",
            "abstract": (
                "Recent work has demonstrated substantial gains on many NLP tasks and benchmarks."
            ),
            "year": 2020,
            "venue": "NeurIPS",
            "citationCount": 25000,
            "externalIds": {
                "DOI": "10.48550/arXiv.2005.14165",
                "ArXiv": "2005.14165",
            },
            "authors": [
                {"authorId": "1", "name": "Tom B. Brown"},
                {"authorId": "2", "name": "Benjamin Mann"},
            ],
            "openAccessPdf": {
                "url": "https://arxiv.org/pdf/2005.14165.pdf",
                "status": "GREEN",
            },
        }
    ],
}


@pytest.mark.asyncio
async def test_semantic_scholar_successful_search() -> None:
    """Verify Semantic Scholar JSON response is normalized into Source objects."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "few-shot" in str(request.url)
        return httpx.Response(200, json=SAMPLE_S2_PAYLOAD)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        s2_client = SemanticScholarClient(http_client=client)
        sources = await s2_client.search(query="few-shot", limit=5)

    assert len(sources) == 1
    src = sources[0]
    assert src.title == "Language Models are Few-Shot Learners"
    assert src.authors == ["Tom B. Brown", "Benjamin Mann"]
    assert src.publication_date == "2020"
    assert src.source_type == "semantic_scholar"
    assert src.metadata["doi"] == "10.48550/arXiv.2005.14165"
    assert src.metadata["citation_count"] == 25000
    assert src.metadata["venue"] == "NeurIPS"
    assert src.pdf_url == "https://arxiv.org/pdf/2005.14165.pdf"


@pytest.mark.asyncio
async def test_semantic_scholar_empty_results() -> None:
    """Verify empty results data array returns empty list."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"total": 0, "offset": 0, "data": []})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        s2_client = SemanticScholarClient(http_client=client)
        sources = await s2_client.search(query="nonexistent_phrase")

    assert sources == []


@pytest.mark.asyncio
async def test_semantic_scholar_rate_limit_retry() -> None:
    """Verify 429 response triggers backoff retry and succeeds on subsequent 200."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(429, text="Too Many Requests")
        return httpx.Response(200, json=SAMPLE_S2_PAYLOAD)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        s2_client = SemanticScholarClient(
            http_client=client,
            max_retries=2,
            initial_backoff=0.01,  # Fast backoff for tests
        )
        sources = await s2_client.search(query="retry test")

    assert call_count == 2
    assert len(sources) == 1


@pytest.mark.asyncio
async def test_semantic_scholar_rate_limit_exhausted() -> None:
    """Verify persistent 429 raises SemanticScholarRateLimitError after retries."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, text="Rate Limited")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        s2_client = SemanticScholarClient(
            http_client=client,
            max_retries=2,
            initial_backoff=0.01,
        )
        with pytest.raises(SemanticScholarRateLimitError):
            await s2_client.search(query="rate limit fail")


@pytest.mark.asyncio
async def test_semantic_scholar_http_error() -> None:
    """Verify HTTP 500 raises SemanticScholarAPIError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Server Error")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        s2_client = SemanticScholarClient(http_client=client)
        with pytest.raises(SemanticScholarAPIError):
            await s2_client.search(query="error query")
