"""Client for querying the free Semantic Scholar Academic Graph API.

Extracts titles, abstracts, citation counts, open-access PDFs, and DOIs
with rate-limit handling and automatic backoff.
"""

import asyncio
from typing import Any

import httpx

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Source

logger = get_logger("tools.semantic_scholar")

SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
PAPER_FIELDS = "title,authors,abstract,year,paperId,externalIds,venue,citationCount,openAccessPdf"


class SemanticScholarError(Exception):
    """Base exception for Semantic Scholar operations."""

    pass


class SemanticScholarAPIError(SemanticScholarError):
    """Raised on non-200 HTTP responses other than handled rate limits."""

    pass


class SemanticScholarRateLimitError(SemanticScholarError):
    """Raised when request rate limits are exhausted after retries."""

    pass


class SemanticScholarClient:
    """Asynchronous client for Semantic Scholar Academic Graph."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int = 3,
        initial_backoff: float = 0.5,
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout = self.settings.request_timeout_seconds
        self.api_key = self.settings.semantic_scholar_api_key
        self._external_client = http_client
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[Source]:
        """Search Semantic Scholar papers and return normalized Source domain models.

        Args:
            query: Topic or hypothesis search phrase.
            limit: Maximum results to return (capped at 100).

        Returns:
            List of normalized Source objects.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        params = {
            "query": clean_query,
            "limit": max(1, min(limit, 100)),
            "fields": PAPER_FIELDS,
        }

        headers: dict[str, str] = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key

        if self._external_client:
            return await self._execute_search_with_retry(self._external_client, params, headers)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._execute_search_with_retry(client, params, headers)

    async def _execute_search_with_retry(
        self,
        client: httpx.AsyncClient,
        params: dict[str, Any],
        headers: dict[str, str],
    ) -> list[Source]:
        """Execute GET with exponential backoff on HTTP 429 rate limit."""
        backoff = self.initial_backoff

        for attempt in range(self.max_retries + 1):
            try:
                response = await client.get(
                    SEMANTIC_SCHOLAR_SEARCH_URL,
                    params=params,
                    headers=headers,
                )
            except httpx.RequestError as exc:
                logger.error("Semantic Scholar network error: %s", exc)
                raise SemanticScholarAPIError(f"Network error: {exc}") from exc

            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception as exc:
                    logger.error("Failed to parse Semantic Scholar JSON: %s", exc)
                    raise SemanticScholarAPIError("Invalid JSON from Semantic Scholar") from exc
                return self._normalize_results(data)

            if response.status_code == 429:
                if attempt < self.max_retries:
                    logger.warning(
                        "Semantic Scholar rate limited (429). Retrying in %.2fs (attempt %d/%d)...",
                        backoff,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise SemanticScholarRateLimitError(
                    "Semantic Scholar rate limit exceeded after retries"
                )

            logger.error(
                "Semantic Scholar returned HTTP %d: %s", response.status_code, response.text[:200]
            )
            raise SemanticScholarAPIError(
                f"Semantic Scholar API returned HTTP {response.status_code}"
            )

        return []

    def _normalize_results(self, data: dict[str, Any]) -> list[Source]:
        """Convert raw Semantic Scholar JSON items into normalized Source models."""
        raw_papers = data.get("data", [])
        sources: list[Source] = []

        for paper in raw_papers:
            title = (paper.get("title") or "").strip()
            if not title:
                continue

            authors = [a.get("name", "").strip() for a in paper.get("authors", []) if a.get("name")]

            year = paper.get("year")
            pub_date = str(year) if year else None

            # DOI and external references
            external_ids = paper.get("externalIds") or {}
            doi = external_ids.get("DOI")
            arxiv_id = external_ids.get("ArXiv")

            # PDF link detection
            open_access_info = paper.get("openAccessPdf") or {}
            pdf_url = open_access_info.get("url")
            if not pdf_url and arxiv_id:
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            paper_id = paper.get("paperId")
            canonical_url = (
                pdf_url
                or (f"https://doi.org/{doi}" if doi else None)
                or (f"https://www.semanticscholar.org/paper/{paper_id}" if paper_id else None)
            )

            metadata = {
                "paper_id": paper_id,
                "doi": doi,
                "arxiv_id": arxiv_id,
                "venue": paper.get("venue"),
                "citation_count": paper.get("citationCount"),
                "pdf_url": pdf_url,
                "provider": "semantic_scholar",
            }

            source = Source(
                title=title,
                authors=authors,
                publication_date=pub_date,
                url=canonical_url,
                source_type="semantic_scholar",
                abstract=paper.get("abstract"),
                metadata=metadata,
            )
            sources.append(source)

        return sources
