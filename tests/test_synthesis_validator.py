"""Unit tests for ReportValidator assessing quality control metrics."""

from backend.core.models import Evidence, Source
from backend.synthesis.citations import CitationManager
from backend.synthesis.models import ReportSection, ResearchClaim
from backend.synthesis.provenance import ProvenanceGraph
from backend.synthesis.validator import ReportValidator


def test_validator_perfect_report() -> None:
    src = Source(title="Source One", authors=["Author A."], publication_date="2022")
    ev = Evidence(
        source_id=src.id,
        content="Dense embeddings represent semantic text similarity effectively.",
        section="Methods",
        page_number=2,
    )
    graph = ProvenanceGraph(question="Test question")
    graph.register_source(src)
    graph.register_evidence(ev)

    claim = ResearchClaim(
        claim_text="Dense embeddings represent semantic text similarity effectively.",
        supporting_evidence_ids=[ev.id],
        source_ids=[src.id],
        page_references=[2],
    )
    graph.add_claim(claim)

    mgr = CitationManager()
    mgr.register_source(src)

    sections = [
        ReportSection(
            title="Abstract", section_type="abstract", content="Executive abstract text."
        ),
        ReportSection(
            title="1. Introduction",
            section_type="introduction",
            content="Intro text.",
            claim_ids=[claim.id],
        ),
        ReportSection(title="2. Conclusion", section_type="conclusion", content="Conclusion text."),
        ReportSection(
            title="References", section_type="references", content=mgr.render_references_markdown()
        ),
    ]

    validator = ReportValidator(
        provenance_graph=graph,
        citation_manager=mgr,
        sources=[src],
        available_evidence=[ev],
    )
    res = validator.validate_report(sections=sections, claims=[claim])

    assert res.is_valid is True
    assert res.validation_status == "PASSED"
    assert res.unsupported_claim_rate == 0.0
    assert res.citation_coverage == 1.0
    assert res.evidence_coverage == 1.0
    assert res.citation_correctness == 1.0
    assert res.contradiction_count == 0


def test_validator_fails_on_unsupported_claim() -> None:
    graph = ProvenanceGraph(question="Test question")
    claim_bad = ResearchClaim(
        claim_text="Unsupported statement asserting unproven results.",
        supporting_evidence_ids=[],
        source_ids=[],
    )
    graph.add_claim(claim_bad)

    mgr = CitationManager()
    sections = [
        ReportSection(title="Abstract", section_type="abstract", content="Abstract text."),
        ReportSection(
            title="1. Introduction",
            section_type="introduction",
            content="Intro.",
            claim_ids=[claim_bad.id],
        ),
        ReportSection(title="2. Conclusion", section_type="conclusion", content="Conclusion."),
        ReportSection(title="References", section_type="references", content="References."),
    ]

    validator = ReportValidator(
        provenance_graph=graph,
        citation_manager=mgr,
        sources=[],
        max_unsupported_rate=0.0,
    )
    res = validator.validate_report(sections=sections, claims=[claim_bad])

    assert res.is_valid is False
    assert res.validation_status == "FAILED"
    assert res.unsupported_claims == 1
    assert res.unsupported_claim_rate == 1.0
    assert claim_bad.id in res.unsupported_claim_ids


def test_validator_fails_on_fabricated_citation() -> None:
    graph = ProvenanceGraph(question="Test question")
    mgr = CitationManager()
    # Register a citation that has no matching source in sources list
    phantom_src = Source(title="Phantom Paper")
    mgr.register_source(phantom_src)

    validator = ReportValidator(
        provenance_graph=graph,
        citation_manager=mgr,
        sources=[],  # Empty known sources!
    )
    sections = [
        ReportSection(title="Abstract", section_type="abstract", content="Abstract text."),
        ReportSection(title="1. Introduction", section_type="introduction", content="Intro."),
        ReportSection(title="2. Conclusion", section_type="conclusion", content="Conclusion."),
        ReportSection(title="References", section_type="references", content="References."),
    ]
    res = validator.validate_report(sections=sections, claims=[])

    assert res.is_valid is False
    assert res.validation_status == "FAILED"
    assert res.citation_correctness == 0.0
    assert any("Fabricated citation detected" in iss for iss in res.issues)
