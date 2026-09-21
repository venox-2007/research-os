"""Observability and execution trace event models for agentic research orchestration."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

EventType = Literal[
    "node_start",
    "node_complete",
    "task_start",
    "task_complete",
    "tool_start",
    "tool_end",
    "tool_call",
    "tool_result",
    "evidence_verified",
    "contradiction_detected",
    "critique_complete",
    "critic_verdict",
    "iteration_start",
    "iteration_end",
    "workflow_complete",
    "error",
    "status_change",
]


class TraceEvent(BaseModel):
    """Structured record of a single execution event within the LangGraph research flow."""

    id: UUID = Field(default_factory=uuid4, description="Unique event identifier")
    event_type: EventType = Field(..., description="Category of the event")
    node_name: str | None = Field(default=None, description="Graph node name where event occurred")
    iteration: int = Field(default=0, description="Workflow iteration count")
    message: str = Field(..., description="Human-readable event description")
    details: dict[str, Any] = Field(default_factory=dict, description="Structured event payload")
    duration_ms: float | None = Field(default=None, description="Duration in milliseconds if timed")
    error: str | None = Field(
        default=None, description="Error message if event describes a failure"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Time of occurrence in UTC",
    )


class TraceCollector:
    """Utility collector for assembling, querying, and serializing execution traces."""

    def __init__(
        self,
        existing_events: list[dict[str, Any] | TraceEvent] | None = None,
    ) -> None:
        self.events: list[TraceEvent] = []
        if existing_events:
            for ev in existing_events:
                if isinstance(ev, TraceEvent):
                    self.events.append(ev)
                elif isinstance(ev, dict):
                    try:
                        self.events.append(TraceEvent(**ev))
                    except Exception:
                        pass

    def record(
        self,
        event_type: EventType,
        message: str,
        node_name: str | None = None,
        iteration: int = 0,
        details: dict[str, Any] | None = None,
        duration_ms: float | None = None,
        error: str | None = None,
    ) -> TraceEvent:
        """Create, store, and return a new TraceEvent."""
        event = TraceEvent(
            event_type=event_type,
            node_name=node_name,
            iteration=iteration,
            message=message,
            details=details or {},
            duration_ms=duration_ms,
            error=error,
        )
        self.events.append(event)
        return event

    def get_events_for_node(self, node_name: str) -> list[TraceEvent]:
        """Filter recorded events by graph node name."""
        return [e for e in self.events if e.node_name == node_name]

    def get_errors(self) -> list[TraceEvent]:
        """Filter recorded events that captured errors."""
        return [e for e in self.events if e.error is not None or e.event_type == "error"]

    def to_dicts(self) -> list[dict[str, Any]]:
        """Serialize all events to dictionaries."""
        return [e.model_dump(mode="json") for e in self.events]

    def to_dict_list(self) -> list[dict[str, Any]]:
        """Serialize all events to dictionaries (alias)."""
        return self.to_dicts()
