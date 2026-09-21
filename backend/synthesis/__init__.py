"""Research synthesis, citation verification, and final report generation package."""

from backend.synthesis.citations import CitationFormatter, CitationManager
from backend.synthesis.engine import SynthesisEngine
from backend.synthesis.graph import build_synthesis_graph, run_synthesis
from backend.synthesis.models import (
    CitationReference,
    ClaimEvidence,
    ClaimOrigin,
    ClaimType,
    ReportArtifact,
    ReportSection,
    ReportSpec,
    ReportValidation,
    ResearchClaim,
    SupportStatus,
    SynthesisResult,
    ValidationStatus,
)
from backend.synthesis.provenance import ProvenanceGraph
from backend.synthesis.validator import ReportValidator
from backend.synthesis.verifier import CitationVerifier

__all__ = [
    "CitationFormatter",
    "CitationManager",
    "CitationReference",
    "CitationVerifier",
    "ClaimEvidence",
    "ClaimOrigin",
    "ClaimType",
    "ProvenanceGraph",
    "ReportArtifact",
    "ReportSection",
    "ReportSpec",
    "ReportValidation",
    "ReportValidator",
    "ResearchClaim",
    "SupportStatus",
    "SynthesisEngine",
    "SynthesisResult",
    "ValidationStatus",
    "build_synthesis_graph",
    "run_synthesis",
]
