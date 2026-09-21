"""Agent research tools package."""

from backend.agents.tools.academic_search import (
    ArxivSearchTool,
    PaperIngestTool,
    SemanticScholarSearchTool,
)
from backend.agents.tools.base import BaseResearchTool, ToolResult
from backend.agents.tools.rag_search import RAGSearchTool
from backend.agents.tools.registry import ToolRegistry, get_default_tool_registry
from backend.agents.tools.web_search import WebSearchTool

__all__ = [
    "BaseResearchTool",
    "ToolResult",
    "RAGSearchTool",
    "ArxivSearchTool",
    "SemanticScholarSearchTool",
    "PaperIngestTool",
    "WebSearchTool",
    "ToolRegistry",
    "get_default_tool_registry",
]
