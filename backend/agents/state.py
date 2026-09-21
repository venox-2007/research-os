"""Strongly typed state definitions and domain models for the LangGraph research workflow."""

from typing import Any, Literal, TypedDict
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from backend.agents.events import TraceEvent
from backend.core.models import Evidence, ResearchPlan, Source

SupportStatus = Literal["supported", "partially_supported", "unsupported"]
ResearchStatus = Literal[
    "initialized",
    "planning",
    "researching",
    "verifying",
    "critiquing",
    "refining",
    "completed",
    "failed",
]


class VerificationResult(BaseModel):
    """Structured audit assessment of a specific piece of retrieved evidence."""

    id: UUID = Field(default_factory=uuid4, description="Unique verification identifier")
    evidence_id: UUID | str = Field(..., description="ID of the verified Evidence object")
    chunk_id: str | None = Field(default=None, description="Linked chunk identifier")
    relevant: bool = Field(
        ..., description="Whether the excerpt addresses the research question/task"
    )
    support_status: SupportStatus = Field(
        ...,
        description="Claim support classification: supported, partially_supported, unsupported",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for this verification judgment",
    )
    reason: str = Field(..., description="Explicit rationale for the verification decision")
    is_contradictory: bool = Field(
        default=False,
        description="Whether this evidence contradicts other verified findings",
    )
    contradiction_details: str | None = Field(
        default=None,
        description="Explanation of contradiction if detected",
    )


class CriticEvaluation(BaseModel):
    """Structured assessment produced by the Research Critic at the end of an iteration."""

    id: UUID = Field(default_factory=uuid4, description="Unique critic evaluation identifier")
    iteration: int = Field(default=1, description="Workflow iteration number being evaluated")
    is_sufficient: bool = Field(
        ...,
        description="Whether current evidence is sufficient to answer the research question",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in research completeness",
    )
    reason: str = Field(..., description="Detailed explanation of the critic's verdict")
    unanswered_subquestions: list[str] = Field(
        default_factory=list,
        description="Specific subquestions remaining unresolved",
    )
    weak_evidence_notes: list[str] = Field(
        default_factory=list,
        description="Critique of weak, ambiguous, or questionable evidence items",
    )
    missing_topics: list[str] = Field(
        default_factory=list,
        description="Important perspectives or dimensions missing from the evidence",
    )
    recommended_queries: list[str] = Field(
        default_factory=list,
        description="Recommended search queries for the next iteration",
    )
    suggested_tasks: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Concrete new tasks suggested to resolve gaps",
    )


class ResearchState(TypedDict):
    """Strongly typed, serializable LangGraph state for ResearchOS workflow."""

    # Initial inputs
    question: str
    discipline: str | None
    constraints: list[str]

    # Planning & Tasks
    plan: dict[str, Any] | None
    tasks: list[dict[str, Any]]
    completed_tasks: list[dict[str, Any]]
    pending_tasks: list[dict[str, Any]]
    current_task: dict[str, Any] | None

    # Search & Retrieval Evidence
    search_queries: list[str]
    retrieved_evidence: list[dict[str, Any]]
    verified_evidence: list[dict[str, Any]]
    verification_results: list[dict[str, Any]]
    sources: list[dict[str, Any]]

    # Experiments (Milestone 5)
    experiment_specs: list[dict[str, Any]]
    experiment_results: list[dict[str, Any]]

    # Synthesis & Critique
    contradictions: list[str]
    research_notes: list[str]
    critic_evaluations: list[dict[str, Any]]

    # Workflow Control & Observability
    iteration_count: int
    max_iterations: int
    status: str
    errors: list[str]
    trace: list[dict[str, Any]]

    # Final Consolidated Output
    final_context: dict[str, Any]


def create_initial_research_state(
    question: str,
    discipline: str | None = None,
    constraints: list[str] | None = None,
    max_iterations: int = 3,
) -> ResearchState:
    """Instantiate a clean, fully initialized ResearchState."""
    return ResearchState(
        question=question.strip(),
        discipline=discipline,
        constraints=constraints or [],
        plan=None,
        tasks=[],
        completed_tasks=[],
        pending_tasks=[],
        current_task=None,
        search_queries=[],
        retrieved_evidence=[],
        verified_evidence=[],
        verification_results=[],
        sources=[],
        experiment_specs=[],
        experiment_results=[],
        contradictions=[],
        research_notes=[],
        critic_evaluations=[],
        iteration_count=0,
        max_iterations=max_iterations,
        status="initialized",
        errors=[],
        trace=[],
        final_context={},
    )


class ResearchRunResult(BaseModel):
    """Public deliverable payload returned by the research workflow."""

    question: str
    status: str
    iteration_count: int
    max_iterations: int
    plan: ResearchPlan | None = None
    tasks_completed: int = 0
    tasks_total: int = 0
    verified_evidence_count: int = 0
    sources_count: int = 0
    verified_evidence: list[Evidence] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)
    experiment_specs: list[dict[str, Any]] = Field(default_factory=list)
    experiment_results: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    research_notes: list[str] = Field(default_factory=list)
    critic_summary: str | None = None
    confidence_score: float = 0.0
    trace: list[TraceEvent] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    final_context: dict[str, Any] = Field(default_factory=dict)
