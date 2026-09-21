"""Unit tests for synthesis domain models and Pydantic schemas."""

from uuid import uuid4

from backend.synthesis.models import (
    CitationReference,
    ClaimEvidence,
    ReportSection,
    ReportSpec,
    ReportValidation,
    ResearchClaim,
    SynthesisResult,
)


def test_report_spec_defaults() -> None:
    spec = ReportSpec(question="What are the efficiency trade-offs of hybrid RAG?")
    assert spec.question == "What are the efficiency trade-offs of hybrid RAG?"
    assert spec.target_audience == "academic"
    assert spec.format == "markdown"
    assert spec.include_experiments is True
    assert spec.max_sections == 15


def test_research_claim_model() -> None:
    ev_id = uuid4()
    src_id = uuid4()
    claim = ResearchClaim(
        claim_text="Hybrid RAG outperforms dense-only search on technical vocabulary.",
        claim_type="finding",
        origin="literature",
        supporting_evidence_ids=[ev_id],
        source_ids=[src_id],
        page_references=[4],
        section_references=["3.2 Retrieval Accuracy"],
        support_status="SUPPORTED",
        confidence=0.95,
    )
    assert claim.claim_type == "finding"
    assert claim.origin == "literature"
    assert claim.support_status == "SUPPORTED"
    assert claim.confidence == 0.95
    assert claim.supporting_evidence_ids == [ev_id]
    assert claim.page_references == [4]


def test_claim_evidence_model() -> None:
    claim_id = uuid4()
    ev_id = uuid4()
    ce = ClaimEvidence(
        claim_id=claim_id,
        evidence_id=ev_id,
        snippet="Hybrid search achieves 94% recall.",
        relevance_score=0.9,
    )
    assert ce.claim_id == claim_id
    assert ce.evidence_id == ev_id
    assert ce.relevance_score == 0.9


def test_citation_reference_model() -> None:
    src_id = uuid4()
    cit = CitationReference(
        key="[1]",
        source_id=src_id,
        title="Attention Is All You Need",
        authors=["Vaswani, A."],
        year=2017,
        venue="NeurIPS",
        formatted_citation="[1] Vaswani, A., 'Attention Is All You Need', NeurIPS, 2017.",
        is_available=True,
    )
    assert cit.key == "[1]"
    assert cit.year == 2017
    assert cit.is_available is True


def test_report_section_hierarchy() -> None:
    c_id = uuid4()
    sub = ReportSection(
        title="Lexical BM25", section_type="subsection", content="BM25 scoring.", claim_ids=[c_id]
    )
    sec = ReportSection(
        title="Related Work",
        section_type="related_work",
        content="Overview of retrieval.",
        subsections=[sub],
        order=2,
    )
    assert sec.order == 2
    assert len(sec.subsections) == 1
    assert sec.subsections[0].title == "Lexical BM25"


def test_report_validation_metrics() -> None:
    val = ReportValidation(
        is_valid=True,
        total_claims=10,
        supported_claims=9,
        partially_supported_claims=1,
        unsupported_claims=0,
        contradicted_claims=0,
        citation_coverage=1.0,
        evidence_coverage=0.85,
        unsupported_claim_rate=0.0,
        provenance_completeness=1.0,
        contradiction_count=0,
        citation_correctness=1.0,
        validation_status="PASSED",
    )
    assert val.is_valid is True
    assert val.unsupported_claim_rate == 0.0
    assert val.validation_status == "PASSED"


def test_synthesis_result_serialization() -> None:
    spec = ReportSpec(question="Is hybrid RAG scalable?")
    val = ReportValidation(is_valid=True, validation_status="PASSED")
    res = SynthesisResult(
        spec=spec,
        title="Scalability of Hybrid RAG",
        abstract="Executive abstract",
        validation=val,
        report_markdown="# Scalability of Hybrid RAG\n\nAbstract text",
        report_json={"key": "value"},
    )
    dumped = res.model_dump(mode="json")
    assert dumped["title"] == "Scalability of Hybrid RAG"
    assert dumped["validation"]["validation_status"] == "PASSED"
