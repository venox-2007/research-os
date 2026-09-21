"""Strongly typed Pydantic models for ResearchOS synthesis and reporting engine."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


ClaimType = Literal[
    "background",
    "finding",
    "comparison",
    "methodological",
    "experiment_result",
    "limitation",
    "conclusion",
]

ClaimOrigin = Literal["literature", "experiment"]

SupportStatus = Literal[
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "UNSUPPORTED",
    "CONTRADICTED",
    "UNVERIFIED",
]

ValidationStatus = Literal["PASSED", "WARNING", "FAILED"]

ReportArtifactType = Literal["markdown", "json", "latex", "plot", "summary"]


class ReportSpec(BaseModel):
    """Specification guiding synthesis and generation of the final research report."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier for report spec")
    question: str = Field(..., min_length=3, description="Target research question")
    title: str | None = Field(default=None, description="Optional custom paper title")
    discipline: str | None = Field(default=None, description="Domain or academic field")
    target_audience: str = Field(
        default="academic",
        description="Target audience (academic, technical, executive)",
    )
    format: str = Field(default="markdown", description="Report format (markdown, latex, json)")
    max_sections: int = Field(default=15, ge=1, le=30, description="Max sections in outline")
    focus_areas: list[str] = Field(
        default_factory=list, description="Specific subtopics or methodologies to emphasize"
    )
    include_experiments: bool = Field(
        default=True, description="Whether to incorporate empirical experiment findings"
    )
    constraints: list[str] = Field(
        default_factory=list, description="Explicit synthesis or formatting constraints"
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResearchClaim(BaseModel):
    """Atomic factual statement synthesized from literature or empirical experiment results."""

    id: UUID = Field(default_factory=uuid4, description="Unique claim identifier")
    claim_text: str = Field(
        ..., min_length=3, description="The substantive factual claim statement"
    )
    claim_type: ClaimType = Field(
        default="finding",
        description="Type of claim (background, finding, comparison, methodological, etc.)",
    )
    origin: ClaimOrigin = Field(
        default="literature",
        description="Origin of claim: literature or experiment",
    )
    supporting_evidence_ids: list[UUID] = Field(
        default_factory=list,
        description="Foreign IDs of supporting Evidence objects",
    )
    source_ids: list[UUID] = Field(
        default_factory=list,
        description="Foreign IDs of referenced primary Sources",
    )
    page_references: list[int] = Field(
        default_factory=list,
        description="1-indexed page coordinates where supporting evidence appears",
    )
    section_references: list[str] = Field(
        default_factory=list,
        description="Academic sections from which evidence was extracted",
    )
    support_status: SupportStatus = Field(
        default="UNVERIFIED",
        description="Verification state: SUPPORTED, PARTIALLY_SUPPORTED, UNSUPPORTED, CONTRADICTED, UNVERIFIED",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score of the claim support assessment",
    )
    is_contradicted: bool = Field(
        default=False,
        description="True if contradictory findings exist in the evidence base",
    )
    contradiction_notes: str | None = Field(
        default=None,
        description="Details regarding conflicting evidence if applicable",
    )
    experiment_run_id: UUID | None = Field(
        default=None,
        description="Foreign ID of parent ExperimentRun if origin is experiment",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ClaimEvidence(BaseModel):
    """Detailed link between a claim and an individual evidence excerpt."""

    id: UUID = Field(default_factory=uuid4, description="Unique link identifier")
    claim_id: UUID = Field(..., description="Referenced ResearchClaim ID")
    evidence_id: UUID = Field(..., description="Referenced Evidence ID")
    source_id: UUID | None = Field(default=None, description="Referenced Source ID")
    snippet: str = Field(..., min_length=1, description="Verbatim quote or supporting excerpt")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    verification_justification: str | None = Field(
        default=None, description="Rationale for evidence alignment"
    )


class CitationReference(BaseModel):
    """Canonical citation reference representation mapped to a bibliography entry."""

    key: str = Field(..., description="Inline citation key or marker (e.g. '[1]', '[2]')")
    source_id: UUID = Field(..., description="Foreign ID of referenced Source")
    title: str = Field(..., description="Source paper or document title")
    authors: list[str] = Field(default_factory=list, description="Author list")
    year: str | int | None = Field(default=None, description="Publication year")
    venue: str | None = Field(default=None, description="Journal, conference, or repository venue")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    url: str | None = Field(default=None, description="Direct URL to publication")
    paper_id: str | None = Field(default=None, description="arXiv ID, S2 ID, or doc ID")
    formatted_citation: str = Field(..., description="Rendered bibliographic entry string")
    is_available: bool = Field(
        default=True,
        description="Whether complete metadata was available (false if missing/incomplete)",
    )


class ReportSection(BaseModel):
    """Structured report section containing synthesized text, claims, and citations."""

    id: UUID = Field(default_factory=uuid4, description="Unique section identifier")
    title: str = Field(..., description="Section title heading")
    section_type: str = Field(
        default="body",
        description="Semantic section type (abstract, background, methodology, results, etc.)",
    )
    content: str = Field(default="", description="Rendered prose content of the section")
    claim_ids: list[UUID] = Field(
        default_factory=list, description="IDs of claims asserted in this section"
    )
    citation_keys: list[str] = Field(
        default_factory=list, description="Citation keys referenced in this section"
    )
    order: int = Field(default=0, description="Display order index")
    subsections: list["ReportSection"] = Field(
        default_factory=list, description="Nested child sections"
    )


class ReportArtifact(BaseModel):
    """Report artifact registered with safe ArtifactStore."""

    id: UUID = Field(default_factory=uuid4, description="Unique artifact identifier")
    report_id: UUID = Field(..., description="Parent report ID")
    artifact_type: ReportArtifactType = Field(..., description="Artifact category")
    filename: str = Field(..., description="Artifact filename on disk")
    file_path: str = Field(..., description="Absolute path to artifact file")
    file_hash: str = Field(..., description="SHA-256 hash of file content")
    size_bytes: int = Field(default=0, ge=0, description="Size in bytes")
    mime_type: str = Field(default="text/plain", description="MIME content type")


class ReportValidation(BaseModel):
    """Quantitative quality audit report for the synthesized document."""

    is_valid: bool = Field(
        default=False, description="True if report meets strict empirical standards"
    )
    total_claims: int = Field(default=0, ge=0, description="Total factual claims evaluated")
    supported_claims: int = Field(default=0, ge=0, description="Claims with full verified support")
    partially_supported_claims: int = Field(
        default=0, ge=0, description="Claims with partial support"
    )
    unsupported_claims: int = Field(default=0, ge=0, description="Claims lacking valid evidence")
    contradicted_claims: int = Field(
        default=0, ge=0, description="Claims with conflicting evidence"
    )
    citation_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Proportion of factual claims containing at least one verified citation",
    )
    evidence_coverage: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Proportion of verified evidence incorporated into claims",
    )
    unsupported_claim_rate: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of unsupported claims to total claims",
    )
    provenance_completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Proportion of claims with full traceable lineage to primary sources",
    )
    contradiction_count: int = Field(
        default=0, ge=0, description="Number of unresolved contradictions"
    )
    citation_correctness: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Proportion of citations verified against real sources without hallucination",
    )
    validation_status: ValidationStatus = Field(
        default="PASSED",
        description="High-level audit status: PASSED, WARNING, or FAILED",
    )
    issues: list[str] = Field(default_factory=list, description="Descriptive audit failure items")
    unsupported_claim_ids: list[UUID] = Field(
        default_factory=list, description="IDs of claims failing support verification"
    )
    contradicted_claim_ids: list[UUID] = Field(
        default_factory=list, description="IDs of contradicted claims"
    )
    unresolved_questions: list[str] = Field(
        default_factory=list, description="Subquestions requiring further investigation"
    )


class SynthesisResult(BaseModel):
    """Complete synthesized research deliverable with full provenance and artifacts."""

    id: UUID = Field(default_factory=uuid4, description="Unique result identifier")
    report_id: UUID = Field(default_factory=uuid4, description="Canonical report ID")
    spec: ReportSpec = Field(..., description="Specification used to synthesize report")
    title: str = Field(..., description="Final paper title")
    abstract: str = Field(..., description="Synthesized executive abstract")
    sections: list[ReportSection] = Field(default_factory=list, description="Report sections")
    claims: list[ResearchClaim] = Field(default_factory=list, description="All asserted claims")
    citations: list[CitationReference] = Field(
        default_factory=list, description="All cited references"
    )
    validation: ReportValidation = Field(..., description="Audit validation assessment")
    report_markdown: str = Field(..., description="Rendered Markdown report")
    report_json: dict[str, Any] = Field(default_factory=dict, description="Machine-readable report")
    artifacts: list[ReportArtifact] = Field(
        default_factory=list, description="Saved file artifacts"
    )
    created_at: datetime = Field(default_factory=utc_now)
