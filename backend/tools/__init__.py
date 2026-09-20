"""Academic paper discovery tools and API clients."""

from backend.tools.arxiv import ArxivAPIError, ArxivClient, ArxivError, ArxivParseError
from backend.tools.semantic_scholar import (
    SemanticScholarAPIError,
    SemanticScholarClient,
    SemanticScholarError,
    SemanticScholarRateLimitError,
)

__all__ = [
    "ArxivAPIError",
    "ArxivClient",
    "ArxivError",
    "ArxivParseError",
    "SemanticScholarAPIError",
    "SemanticScholarClient",
    "SemanticScholarError",
    "SemanticScholarRateLimitError",
]
