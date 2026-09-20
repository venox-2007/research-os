"""Client for querying the free arXiv academic API.

Parses native Atom XML responses into normalized Source domain models
without web scraping or paid credentials.
"""

import re
import xml.etree.ElementTree as ET
from typing import Any

import httpx

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Source

logger = get_logger("tools.arxiv")

ARXIV_API_URL = "https://export.arxiv.org/api/query"
ATOM_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


class ArxivError(Exception):
    """Base exception for arXiv client operations."""

    pass


class ArxivAPIError(ArxivError):
    """Raised when arXiv API returns a non-200 HTTP status."""

    pass


class ArxivParseError(ArxivError):
    """Raised when the Atom XML response from arXiv cannot be parsed."""

    pass


class ArxivClient:
    """Zero-cost asynchronous client for the arXiv open API."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.timeout = self.settings.request_timeout_seconds
        self._external_client = http_client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        sort_by: str = "relevance",
        sort_order: str = "descending",
    ) -> list[Source]:
        """Search arXiv literature and return normalized Source objects.

        Args:
            query: Free-text research query or keyword phrase.
            max_results: Maximum number of papers to retrieve (default 10).
            sort_by: Sort criterion (relevance, lastUpdatedDate, submittedDate).
            sort_order: Sort direction (descending, ascending).

        Returns:
            List of normalized Source domain models.
        """
        clean_query = query.strip()
        if not clean_query:
            return []

        # Sanitize query for arXiv query syntax
        formatted_query = f"all:{clean_query}"
        params = {
            "search_query": formatted_query,
            "start": 0,
            "max_results": max(1, min(max_results, 100)),
            "sortBy": sort_by,
            "sortOrder": sort_order,
        }

        if self._external_client:
            return await self._fetch_and_parse(self._external_client, params)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._fetch_and_parse(client, params)

    async def _fetch_and_parse(
        self, client: httpx.AsyncClient, params: dict[str, Any]
    ) -> list[Source]:
        """Execute request and parse XML response body."""
        try:
            response = await client.get(ARXIV_API_URL, params=params)
        except httpx.RequestError as exc:
            logger.error("arXiv network request failed: %s", exc)
            raise ArxivAPIError(f"Network error querying arXiv: {exc}") from exc

        if response.status_code != 200:
            logger.error("arXiv returned HTTP %d: %s", response.status_code, response.text[:200])
            raise ArxivAPIError(f"arXiv API returned HTTP {response.status_code}")

        return self._parse_atom_feed(response.text)

    def _parse_atom_feed(self, xml_content: str) -> list[Source]:
        """Parse raw Atom XML into strongly typed Source records."""
        try:
            root = ET.fromstring(xml_content)
        except ET.ParseError as exc:
            logger.error("Failed to parse arXiv Atom XML: %s", exc)
            raise ArxivParseError(f"Malformed XML response from arXiv: {exc}") from exc

        sources: list[Source] = []
        entries = root.findall("atom:entry", ATOM_NS)

        for entry in entries:
            # Title
            title_elem = entry.find("atom:title", ATOM_NS)
            if title_elem is None or not title_elem.text:
                continue
            title = re.sub(r"\s+", " ", title_elem.text).strip()

            # Catch dummy / empty entry returned by arXiv when 0 results match
            if title.lower() == "error" or not title:
                continue

            # Summary / Abstract
            summary_elem = entry.find("atom:summary", ATOM_NS)
            abstract = (
                re.sub(r"\s+", " ", summary_elem.text).strip()
                if summary_elem is not None and summary_elem.text
                else None
            )

            # Published Date
            published_elem = entry.find("atom:published", ATOM_NS)
            published = (
                published_elem.text.strip()
                if published_elem is not None and published_elem.text
                else None
            )
            pub_date = published[:10] if published else None

            # Authors
            authors: list[str] = []
            for author_node in entry.findall("atom:author", ATOM_NS):
                name_elem = author_node.find("atom:name", ATOM_NS)
                if name_elem is not None and name_elem.text:
                    authors.append(name_elem.text.strip())

            # Categories
            categories: list[str] = []
            for cat_node in entry.findall("atom:category", ATOM_NS):
                term = cat_node.get("term")
                if term:
                    categories.append(term.strip())

            # Links: abstract and PDF
            abstract_url: str | None = None
            pdf_url: str | None = None
            arxiv_id: str | None = None

            id_elem = entry.find("atom:id", ATOM_NS)
            if id_elem is not None and id_elem.text:
                raw_id_url = id_elem.text.strip()
                abstract_url = raw_id_url
                # Extract clean arxiv_id, e.g. '2301.12345v1' from 'http://arxiv.org/abs/2301.12345v1'
                match = re.search(r"arxiv\.org/abs/(.+)$", raw_id_url)
                if match:
                    arxiv_id = match.group(1)
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            for link_node in entry.findall("atom:link", ATOM_NS):
                rel = link_node.get("rel")
                link_type = link_node.get("type")
                href = link_node.get("href")

                if rel == "alternate" and href:
                    abstract_url = href
                elif link_type == "application/pdf" and href:
                    pdf_url = href

            # Create normalized Source object
            metadata = {
                "arxiv_id": arxiv_id,
                "pdf_url": pdf_url,
                "abstract_url": abstract_url,
                "categories": categories,
                "provider": "arxiv",
            }

            source = Source(
                title=title,
                authors=authors,
                publication_date=pub_date,
                url=pdf_url or abstract_url,
                source_type="arxiv",
                abstract=abstract,
                metadata=metadata,
            )
            sources.append(source)

        return sources
