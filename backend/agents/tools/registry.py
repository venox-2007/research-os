"""Tool registry managing discovery, execution, and telemetry for research agents."""

from typing import Any

from backend.agents.tools.academic_search import (
    ArxivSearchTool,
    PaperIngestTool,
    SemanticScholarSearchTool,
)
from backend.agents.tools.base import BaseResearchTool, ToolResult
from backend.agents.tools.rag_search import RAGSearchTool
from backend.agents.tools.web_search import WebSearchTool
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger

logger = get_logger("agents.tools.registry")


class ToolRegistry:
    """Central catalog of validated, executable tools available to ResearchOS agents."""

    def __init__(self) -> None:
        self._tools: dict[str, BaseResearchTool] = {}

    def register(self, tool: BaseResearchTool) -> None:
        """Register a tool instance under its canonical name."""
        self._tools[tool.name] = tool
        logger.debug("Registered agent tool: '%s'", tool.name)

    def get(self, name: str) -> BaseResearchTool | None:
        """Lookup a registered tool by name."""
        return self._tools.get(name)

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def list_tools(self) -> list[dict[str, Any]]:
        """Return introspection schemas for all registered tools."""
        manifest: list[dict[str, Any]] = []
        for name, tool in self._tools.items():
            schema_dict = None
            if tool.args_schema:
                schema_dict = tool.args_schema.model_json_schema()
            manifest.append(
                {
                    "name": name,
                    "description": tool.description,
                    "parameters": schema_dict,
                }
            )
        return manifest

    async def invoke(self, name: str, **kwargs: Any) -> ToolResult:
        """Execute a registered tool by name with arguments."""
        tool = self.get(name)
        if not tool:
            logger.error("Attempted to invoke unregistered tool '%s'", name)
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Unrecognized tool '{name}'. Available: {list(self._tools.keys())}",
            )
        return await tool.run(**kwargs)


def get_default_tool_registry(
    settings: Settings | None = None,
    mock_mode: bool | None = None,
) -> ToolRegistry:
    """Construct and configure the standard tool registry with all M2/M3 tools."""
    app_settings = settings or get_settings()
    registry = ToolRegistry()

    # Register M3 RAG search tool
    registry.register(RAGSearchTool(settings=app_settings, mock_mode=mock_mode))

    # Register M2 Academic discovery and ingestion tools
    registry.register(ArxivSearchTool(settings=app_settings, mock_mode=mock_mode))
    registry.register(SemanticScholarSearchTool(settings=app_settings, mock_mode=mock_mode))
    registry.register(PaperIngestTool(settings=app_settings))

    # Register Web research tool
    registry.register(WebSearchTool(settings=app_settings, mock_mode=mock_mode))

    return registry
