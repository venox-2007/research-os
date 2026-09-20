"""Deterministic offline unit tests for the arXiv academic client."""

import httpx
import pytest

from backend.tools.arxiv import ArxivAPIError, ArxivClient, ArxivParseError

SAMPLE_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <title type="html">arXiv Query: search_query=all:attention</title>
  <id>http://arxiv.org/api/12345</id>
  <updated>2026-01-01T00:00:00Z</updated>
  <entry>
    <id>http://arxiv.org/abs/1706.03762v2</id>
    <published>2017-06-12T17:57:34Z</published>
    <title>Attention Is All You Need</title>
    <summary>The dominant sequence transduction models are based on complex networks.</summary>
    <author>
      <name>Ashish Vaswani</name>
    </author>
    <author>
      <name>Noam Shazeer</name>
    </author>
    <arxiv:primary_category term="cs.CL"/>
    <category term="cs.CL"/>
    <category term="cs.LG"/>
    <link rel="alternate" href="http://arxiv.org/abs/1706.03762v2" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/1706.03762v2" type="application/pdf"/>
  </entry>
</feed>
"""

EMPTY_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title type="html">arXiv Query</title>
  <id>http://arxiv.org/api/empty</id>
  <updated>2026-01-01T00:00:00Z</updated>
</feed>
"""


@pytest.mark.asyncio
async def test_arxiv_successful_search() -> None:
    """Verify arXiv client correctly parses Atom feed into normalized Source objects."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "attention" in str(request.url)
        return httpx.Response(200, text=SAMPLE_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        arxiv_client = ArxivClient(http_client=client)
        sources = await arxiv_client.search(query="attention", max_results=5)

    assert len(sources) == 1
    src = sources[0]
    assert src.title == "Attention Is All You Need"
    assert src.authors == ["Ashish Vaswani", "Noam Shazeer"]
    assert src.publication_date == "2017-06-12"
    assert src.source_type == "arxiv"
    assert src.metadata["arxiv_id"] == "1706.03762v2"
    assert src.metadata["pdf_url"] == "http://arxiv.org/pdf/1706.03762v2"
    assert src.pdf_url == "http://arxiv.org/pdf/1706.03762v2"


@pytest.mark.asyncio
async def test_arxiv_empty_result() -> None:
    """Verify arXiv client handles feeds with zero entries gracefully."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=EMPTY_ARXIV_XML)

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        arxiv_client = ArxivClient(http_client=client)
        sources = await arxiv_client.search(query="nonexistent_query_string_xyz")

    assert sources == []


@pytest.mark.asyncio
async def test_arxiv_empty_query() -> None:
    """Verify blank search queries return empty list immediately without network request."""
    arxiv_client = ArxivClient()
    sources = await arxiv_client.search(query="   ")
    assert sources == []


@pytest.mark.asyncio
async def test_arxiv_malformed_xml() -> None:
    """Verify malformed XML raises ArxivParseError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<feed>Broken unclosed tag")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        arxiv_client = ArxivClient(http_client=client)
        with pytest.raises(ArxivParseError):
            await arxiv_client.search(query="test")


@pytest.mark.asyncio
async def test_arxiv_http_error() -> None:
    """Verify non-200 HTTP status raises ArxivAPIError."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        arxiv_client = ArxivClient(http_client=client)
        with pytest.raises(ArxivAPIError) as exc_info:
            await arxiv_client.search(query="test")
        assert "503" in str(exc_info.value)
