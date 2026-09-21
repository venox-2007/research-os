"""REST API endpoints for research report synthesis, claim inspection, and validation."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.api.v1.endpoints.research import _RUNS_DB
from backend.core.logging import get_logger
from backend.core.models import Evidence, Source
from backend.experiments.artifacts import get_artifact_store
from backend.experiments.datasets import SecurityError
from backend.synthesis.engine import SynthesisEngine
from backend.synthesis.models import (
    ReportArtifact,
    ReportSpec,
    ReportValidation,
    ResearchClaim,
    SynthesisResult,
)

logger = get_logger("api.reports")

router = APIRouter(prefix="/reports", tags=["Reports & Synthesis"])

# In-memory store for generated synthesis reports
_REPORTS_DB: dict[UUID, SynthesisResult] = {}


class ReportGenerateRequest(BaseModel):
    """Payload to request autonomous report synthesis."""

    question: str = Field(..., min_length=3, description="Target scientific question")
    title: str | None = Field(default=None, description="Optional custom paper title")
    discipline: str | None = Field(default=None, description="Discipline or domain")
    constraints: list[str] = Field(
        default_factory=list, description="Target constraints or guidelines"
    )
    research_run_id: UUID | None = Field(
        default=None, description="Optional parent research run ID to import evidence from"
    )
    verified_evidence: list[Evidence] = Field(
        default_factory=list, description="Explicit verified evidence items"
    )
    sources: list[Source] = Field(
        default_factory=list, description="Explicit primary academic sources"
    )
    experiment_specs: list[dict[str, Any]] = Field(
        default_factory=list, description="Associated experiment specifications"
    )
    experiment_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Empirical experiment execution records"
    )
    contradictions: list[str] = Field(
        default_factory=list, description="Known empirical contradictions"
    )
    research_notes: list[str] = Field(
        default_factory=list, description="Supplementary research notes"
    )
    max_revisions: int = Field(default=2, ge=0, le=5, description="Maximum self-revision attempts")


class ReportSummaryResponse(BaseModel):
    """Summary metadata for a synthesized report."""

    report_id: UUID
    title: str
    question: str
    discipline: str | None
    abstract: str
    total_claims: int
    citation_coverage: float
    evidence_coverage: float
    unsupported_claim_rate: float
    provenance_completeness: float
    validation_status: str
    artifacts_count: int


@router.post(
    "/generate",
    response_model=SynthesisResult,
    status_code=status.HTTP_201_CREATED,
    summary="Synthesize evidence-grounded research report",
)
async def generate_report(payload: ReportGenerateRequest) -> SynthesisResult:
    """Transform verified literature evidence and empirical experiment results

    into a publication-ready academic report.
    """
    evidence_pool = list(payload.verified_evidence)
    source_pool = list(payload.sources)
    exp_specs = list(payload.experiment_specs)
    exp_results = list(payload.experiment_results)
    contra_pool = list(payload.contradictions)
    notes_pool = list(payload.research_notes)

    # Pull from prior research run if specified
    if payload.research_run_id:
        prior_run = _RUNS_DB.get(payload.research_run_id)
        if not prior_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Prior research run '{payload.research_run_id}' not found.",
            )
        evidence_pool.extend(prior_run.verified_evidence)
        source_pool.extend(prior_run.sources)
        exp_specs.extend(prior_run.experiment_specs)
        exp_results.extend(prior_run.experiment_results)
        contra_pool.extend(prior_run.contradictions)
        notes_pool.extend(prior_run.research_notes)

    spec = ReportSpec(
        question=payload.question,
        title=payload.title,
        discipline=payload.discipline,
        constraints=payload.constraints,
        include_experiments=bool(exp_results),
    )

    engine = SynthesisEngine(max_revisions=payload.max_revisions)
    result = await engine.synthesize(
        spec=spec,
        verified_evidence=evidence_pool,
        sources=source_pool,
        experiment_specs=exp_specs,
        experiment_results=exp_results,
        contradictions=contra_pool,
        research_notes=notes_pool,
    )

    _REPORTS_DB[result.report_id] = result
    logger.info("Successfully synthesized and saved report '%s'", result.report_id)
    return result


@router.get(
    "/{report_id}",
    response_model=SynthesisResult,
    summary="Retrieve full synthesized report",
)
async def get_report(report_id: UUID) -> SynthesisResult:
    """Retrieve full synthesized report deliverable including sections, claims, and artifacts."""
    report = _REPORTS_DB.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return report


@router.get(
    "/{report_id}/claims",
    response_model=list[ResearchClaim],
    summary="Retrieve verified claims and evidence links",
)
async def get_report_claims(report_id: UUID) -> list[ResearchClaim]:
    """Retrieve all structured claims and their verification statuses for a report."""
    report = _REPORTS_DB.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return report.claims


@router.get(
    "/{report_id}/validation",
    response_model=ReportValidation,
    summary="Retrieve report audit validation report",
)
async def get_report_validation(report_id: UUID) -> ReportValidation:
    """Retrieve the multi-stage quality control audit report for a synthesized document."""
    report = _REPORTS_DB.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return report.validation


@router.get(
    "/{report_id}/artifacts",
    response_model=list[ReportArtifact],
    summary="List generated report artifacts",
)
async def list_report_artifacts(report_id: UUID) -> list[ReportArtifact]:
    """List all generated report file artifacts (Markdown, JSON, plots)."""
    report = _REPORTS_DB.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )
    return report.artifacts


@router.get(
    "/{report_id}/artifacts/{filename}",
    summary="Download a report artifact file",
)
async def download_report_artifact(report_id: UUID, filename: str) -> FileResponse:
    """Securely download a specific report artifact file by name."""
    report = _REPORTS_DB.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID '{report_id}' not found.",
        )

    store = get_artifact_store()
    try:
        file_path = store._safe_resolve_file(run_id=report_id, filename=filename)
    except SecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact file '{filename}' not found for report '{report_id}'.",
        )

    media_type = "text/markdown" if filename.endswith(".md") else "application/json"
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename,
    )
