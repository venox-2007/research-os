"""Abstract base class and models for agent research tools."""

import time
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field

from backend.core.logging import get_logger

logger = get_logger("agents.tools")


class ToolResult(BaseModel):
    """Normalized deliverable produced by an agent research tool."""

    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def evidence_items(self) -> list[Any]:
        """Convenience property extracting evidence items from output payload."""
        if isinstance(self.data, dict):
            return self.data.get("evidence", [])
        if isinstance(self.data, list):
            return self.data
        return []


class BaseResearchTool(ABC):
    """Base interface for all tools accessible to ResearchOS agents."""

    name: str = "base_tool"
    description: str = "Base agent tool"
    args_schema: type[BaseModel] | None = None

    async def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with timing, input validation, and error wrapping."""
        t0 = time.perf_counter()
        logger.info("Tool '%s' started with arguments: %s", self.name, list(kwargs.keys()))

        # Validate arguments if schema is defined
        if self.args_schema:
            try:
                validated_args = self.args_schema(**kwargs)
                kwargs = validated_args.model_dump()
            except Exception as exc:
                elapsed = (time.perf_counter() - t0) * 1000.0
                logger.warning("Tool '%s' validation failed: %s", self.name, exc)
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    error=f"Argument validation failed: {exc}",
                    duration_ms=round(elapsed, 2),
                )

        try:
            data = await self._execute(**kwargs)
            elapsed = (time.perf_counter() - t0) * 1000.0
            logger.info("Tool '%s' succeeded in %.1fms", self.name, elapsed)
            return ToolResult(
                tool_name=self.name,
                success=True,
                data=data,
                duration_ms=round(elapsed, 2),
            )
        except Exception as exc:
            elapsed = (time.perf_counter() - t0) * 1000.0
            logger.error("Tool '%s' failed: %s", self.name, exc)
            return ToolResult(
                tool_name=self.name,
                success=False,
                error=str(exc),
                duration_ms=round(elapsed, 2),
            )

    @abstractmethod
    async def _execute(self, **kwargs: Any) -> Any:
        """Internal execution logic to be implemented by child tool."""
        pass
