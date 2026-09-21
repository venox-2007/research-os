"""Provider-agnostic free web research tool with deterministic offline fallback."""

from typing import Any
from urllib.parse import quote_plus
from uuid import uuid4

import httpx
from pydantic import BaseModel, Field

from backend.agents.tools.base import BaseResearchTool
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Evidence, Source

logger = get_logger("agents.tools.web")


class WebSearchInput(BaseModel):
    """Input parameters for free web research."""

    query: str = Field(..., min_length=2, description="Web search query or keywords")
    limit: int = Field(default=5, ge=1, le=10, description="Max search snippets to retrieve")


class WebSearchResult(BaseModel):
    """Normalized web search snippet."""

    title: str
    url: str
    snippet: str
    source_domain: str | None = None


class WebSearchTool(BaseResearchTool):
    """Provider-agnostic free web research tool."""

    name: str = "web_search"
    description: str = (
        "Search public open web resources for high-level concepts, documentation, and scientific blogs. "
        "Returns URLs, titles, and text snippets without requiring paid search APIs."
    )
    args_schema: type[BaseModel] = WebSearchInput

    def __init__(
        self,
        settings: Settings | None = None,
        mock_mode: bool | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else (self.settings.app_env == "testing" or self.settings.llm_provider == "mock")
        )

    async def _execute(self, query: str, limit: int = 5) -> dict[str, Any]:
        """Execute web query using free DuckDuckGo instant answer / HTML or deterministic offline fallback."""
        if self.mock_mode or not self.settings.enable_web_search:
            return self._mock_search(query, limit)

        try:
            results = await self._query_duckduckgo_lite(query, limit)
            if results:
                return self._format_results(query, results, "duckduckgo_free")
        except Exception as exc:
            logger.warning("Free web search failed (%s). Falling back to simulated findings.", exc)

        return self._mock_search(query, limit)

    async def _query_duckduckgo_lite(self, query: str, limit: int) -> list[WebSearchResult]:
        """Query DuckDuckGo free lite interface without requiring API keys."""
        encoded = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        headers = {"User-Agent": "ResearchOS/0.1 (Academic Research Bot; mailto:venox2007@github)"}

        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(url, headers=headers)
            if resp.status_code != 200:
                raise RuntimeError(f"DuckDuckGo returned status {resp.status_code}")

            import re

            results: list[WebSearchResult] = []
            snippets = re.findall(
                r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                resp.text,
                re.DOTALL,
            )
            for link, snippet_raw in snippets[:limit]:
                clean_snippet = re.sub(r"<[^>]+>", "", snippet_raw).strip()
                results.append(
                    WebSearchResult(
                        title=query.title(),
                        url=link,
                        snippet=clean_snippet,
                        source_domain="duckduckgo.com",
                    )
                )
            return results

    def _format_results(
        self, query: str, results: list[WebSearchResult], provider: str
    ) -> dict[str, Any]:
        evidence_items: list[dict[str, Any]] = []
        sources: list[dict[str, Any]] = []

        for r in results:
            src_id = uuid4()
            src = Source(
                id=src_id,
                title=r.title,
                url=r.url,
                source_type="web",
            )
            sources.append(src.model_dump(mode="json"))

            ev = Evidence(
                source_id=src_id,
                source_title=r.title,
                content=r.snippet,
                section="Web Snippet",
                page_number=1,
                confidence_score=0.8,
                extraction_method="web_search",
                metadata={"url": r.url, "source": src.model_dump(mode="json")},
            )
            evidence_items.append(ev.model_dump(mode="json"))

        return {
            "query": query,
            "count": len(results),
            "provider": provider,
            "results": [r.model_dump() for r in results],
            "sources": sources,
            "evidence": evidence_items,
        }

    def _mock_search(self, query: str, limit: int) -> dict[str, Any]:
        """Deterministic offline mock results for tests and zero-cost offline exploration."""
        mock_results = [
            WebSearchResult(
                title=f"Academic Survey: {query}",
                url=f"https://open-research.org/topics/{quote_plus(query)}",
                snippet=(
                    f"Comprehensive overview and synthesis of recent empirical research into '{query}'. "
                    "Explores core methodologies, comparative benchmarks, and open research challenges."
                ),
                source_domain="open-research.org",
            ),
            WebSearchResult(
                title=f"Methods and Benchmarks for {query}",
                url=f"https://arxiv-sanity-lite.com/search?q={quote_plus(query)}",
                snippet=(
                    f"Empirical comparisons, ablation studies, and evaluation frameworks focusing on {query}. "
                    "Highlights experimental tradeoffs between computational efficiency and accuracy."
                ),
                source_domain="arxiv-sanity-lite.com",
            ),
        ]
        chosen = mock_results[:limit]
        return self._format_results(query, chosen, "mock_offline")
