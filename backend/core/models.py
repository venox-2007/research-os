"""Core domain models for ResearchOS.

Defines Pydantic data models for the complete autonomous research lifecycle:
questions, plans, tasks, sources, evidence, citations, experiments, and results.
"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


class ResearchQuestion(BaseModel):
    """Initial research query submitted by the user."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the research query")
    query: str = Field(..., min_length=3, description="The research question or problem statement")
    discipline: str | None = Field(default=None, description="Domain / academic discipline")
    constraints: list[str] = Field(
        default_factory=list,
        description="Explicit constraints, e.g. 'only papers after 2022'",
    )
    status: str = Field(
        default="submitted",
        description=(
            "Status: submitted, planning, researching, experimenting, "
            "synthesizing, completed, failed"
        ),
    )
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Source(BaseModel):
    """Academic paper or primary source discovered during research."""

    id: UUID = Field(default_factory=uuid4, description="Unique source identifier")
    title: str = Field(..., description="Paper or article title")
    authors: list[str] = Field(default_factory=list, description="Author names")
    publication_date: str | None = Field(default=None, description="Publication date or year")
    url: str | None = Field(default=None, description="URL or DOI link")
    source_type: str = Field(
        default="academic",
        description="Origin type: arxiv, semantic_scholar, web, local_pdf",
    )
    abstract: str | None = Field(default=None, description="Paper abstract")
    bibtex: str | None = Field(default=None, description="BibTeX entry for reference")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(BaseModel):
    """Extracted snippet linked to a primary source with confidence and provenance."""

    id: UUID = Field(default_factory=uuid4, description="Unique evidence identifier")
    source_id: UUID = Field(..., description="Foreign reference to the Source")
    content: str = Field(..., min_length=1, description="Verbatim quote or relevant excerpt")
    section: str | None = Field(default=None, description="Source section (e.g. '3.2 Methodology')")
    page_number: int | None = Field(default=None, description="Page number where snippet occurs")
    confidence_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Retrieval/verification confidence score",
    )
    extraction_method: str = Field(
        default="hybrid_rag",
        description="Extraction method (dense_faiss, bm25, direct_parse)",
    )
    created_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    """Verified reference linking generated claims back to traceable evidence."""

    id: UUID = Field(default_factory=uuid4, description="Unique citation identifier")
    source_id: UUID = Field(..., description="Referenced source")
    evidence_id: UUID | None = Field(default=None, description="Optional supporting evidence ID")
    inline_marker: str = Field(default="[1]", description="Marker in text, e.g. [1]")
    formatted_citation: str = Field(..., description="APA / IEEE / Chicago citation string")
    verified: bool = Field(default=False, description="Whether citation was verified by critic")
    verification_notes: str | None = Field(default=None, description="Critic verification notes")


class ResearchTask(BaseModel):
    """Atomic task in a research plan executed by an agent or tool."""

    id: UUID = Field(default_factory=uuid4, description="Unique task identifier")
    plan_id: UUID | None = Field(default=None, description="Parent research plan ID")
    title: str = Field(..., description="Short task title")
    task_type: str = Field(
        default="literature_search",
        description=(
            "Type: literature_search, paper_ingestion, rag_query, "
            "experiment_design, experiment_run, critique, report_generation"
        ),
    )
    assigned_agent: str | None = Field(default=None, description="Agent responsible for execution")
    status: str = Field(
        default="pending", description="Status: pending, in_progress, completed, failed"
    )
    output: dict[str, Any] | None = Field(default=None, description="Task execution output data")
    created_at: datetime = Field(default_factory=utc_now)


class ResearchPlan(BaseModel):
    """Structured plan orchestrating tasks to answer a research question."""

    id: UUID = Field(default_factory=uuid4, description="Unique plan identifier")
    question_id: UUID = Field(..., description="Reference to ResearchQuestion")
    objectives: list[str] = Field(default_factory=list, description="Target objectives")
    tasks: list[ResearchTask] = Field(default_factory=list, description="Ordered tasks")
    status: str = Field(
        default="created", description="Status: created, executing, completed, failed"
    )
    created_at: datetime = Field(default_factory=utc_now)


class Experiment(BaseModel):
    """Hypothesis-driven experiment executed locally in a sandboxed environment."""

    id: UUID = Field(default_factory=uuid4, description="Unique experiment identifier")
    question_id: UUID = Field(..., description="Parent research question ID")
    title: str = Field(..., description="Experiment title")
    hypothesis: str = Field(..., description="Hypothesis being evaluated")
    code: str = Field(..., description="Python script/protocol to execute")
    environment: str = Field(default="python_sandbox", description="Execution environment tag")
    status: str = Field(
        default="pending", description="Status: pending, running, completed, failed"
    )
    stdout: str | None = Field(default=None, description="Captured stdout")
    stderr: str | None = Field(default=None, description="Captured stderr")
    metrics: dict[str, float] = Field(
        default_factory=dict, description="Extracted numerical metrics"
    )
    artifacts: list[str] = Field(default_factory=list, description="Paths to generated plots/files")
    created_at: datetime = Field(default_factory=utc_now)


class ResearchResult(BaseModel):
    """Final synthesized research deliverable with traceable evidence and citations."""

    id: UUID = Field(default_factory=uuid4, description="Unique result identifier")
    question_id: UUID = Field(..., description="Associated research question ID")
    title: str = Field(..., description="Report title")
    summary: str = Field(..., description="Executive summary of findings")
    findings: list[str] = Field(default_factory=list, description="Key conclusions")
    citations: list[Citation] = Field(default_factory=list, description="Verified citations")
    experiments: list[UUID] = Field(default_factory=list, description="Associated experiment IDs")
    report_markdown: str = Field(..., description="Full synthesized research paper / report")
    created_at: datetime = Field(default_factory=utc_now)
