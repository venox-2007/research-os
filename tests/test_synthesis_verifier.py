"""Unit tests for CitationVerifier auditing claims, coordinates, and experiment results."""

from uuid import uuid4

from backend.core.models import Evidence, Source
from backend.synthesis.citations import CitationManager
from backend.synthesis.models import ResearchClaim
from backend.synthesis.provenance import ProvenanceGraph
from backend.synthesis.verifier import CitationVerifier


def test_verifier_supported_literature_claim() -> None:
    graph = ProvenanceGraph(question="Test question")
    src = Source(
        title="Dense Passage Retrieval", authors=["Karpukhin, V."], publication_date="2020"
    )
    ev = Evidence(
        source_id=src.id,
        content="Dense passage retrieval outperforms traditional sparse vector space models on open-domain QA.",
        section="Abstract",
        page_number=1,
        confidence_score=0.95,
    )
    graph.register_source(src)
    graph.register_evidence(ev)

    claim = ResearchClaim(
        claim_text="Dense passage retrieval outperforms traditional sparse models on open-domain question answering.",
        supporting_evidence_ids=[ev.id],
        source_ids=[src.id],
        page_references=[1],
    )
    graph.add_claim(claim)

    mgr = CitationManager()
    mgr.register_source(src)
    verifier = CitationVerifier(provenance_graph=graph, citation_manager=mgr, sources=[src])

    report = verifier.verify_claim(claim)
    assert report.status == "SUPPORTED"
    assert report.confidence >= 0.90
    assert len(report.issues) == 0


def test_verifier_unsupported_claim_no_evidence() -> None:
    graph = ProvenanceGraph(question="Test question")
    claim = ResearchClaim(
        claim_text="An untested claim without any evidence backing.",
        supporting_evidence_ids=[],
        source_ids=[],
    )
    graph.add_claim(claim)

    mgr = CitationManager()
    verifier = CitationVerifier(provenance_graph=graph, citation_manager=mgr, sources=[])

    report = verifier.verify_claim(claim)
    assert report.status == "UNSUPPORTED"
    assert report.confidence == 0.0
    assert "no supporting evidence" in report.issues[0].lower()


def test_verifier_unregistered_source() -> None:
    graph = ProvenanceGraph(question="Test question")
    fake_src_id = uuid4()
    ev = Evidence(
        source_id=fake_src_id,
        content="Some content pointing to missing source.",
    )
    graph.register_evidence(ev)

    claim = ResearchClaim(
        claim_text="Some content pointing to missing source.",
        supporting_evidence_ids=[ev.id],
        source_ids=[fake_src_id],
    )
    graph.add_claim(claim)

    mgr = CitationManager()
    verifier = CitationVerifier(provenance_graph=graph, citation_manager=mgr, sources=[])

    report = verifier.verify_claim(claim)
    assert report.status == "UNSUPPORTED"
    assert any("non-existent source_id" in iss for iss in report.issues)


def test_verifier_contradicted_claim() -> None:
    graph = ProvenanceGraph(question="Test question")
    claim = ResearchClaim(
        claim_text="Sparse BM25 always has lower latency than dense search.",
        is_contradicted=True,
        contradiction_notes="Studies report dense vector search on GPU is 3x faster than CPU BM25.",
    )
    graph.add_claim(claim)

    mgr = CitationManager()
    verifier = CitationVerifier(provenance_graph=graph, citation_manager=mgr, sources=[])

    report = verifier.verify_claim(claim)
    assert report.status == "CONTRADICTED"
    assert report.is_contradicted is True
    assert "GPU is 3x faster" in report.contradiction_details


def test_verifier_experiment_claim_success() -> None:
    graph = ProvenanceGraph(question="Test question")
    exp_run_id = uuid4()
    exp_run = {
        "id": str(exp_run_id),
        "run_id": str(exp_run_id),
        "status": "completed",
        "spec": {"target_routine": "classification_eval"},
        "metrics": {"accuracy": 0.942, "f1_score": 0.938},
    }
    graph.register_experiment({"id": "spec1", "target_routine": "classification_eval"}, exp_run)

    claim = ResearchClaim(
        claim_text="Evaluation of classification_eval achieved accuracy of 0.942.",
        claim_type="experiment_result",
        origin="experiment",
        experiment_run_id=exp_run_id,
    )
    graph.add_claim(claim, experiment_run_id=exp_run_id)

    mgr = CitationManager()
    verifier = CitationVerifier(
        provenance_graph=graph, citation_manager=mgr, experiment_runs=[exp_run]
    )

    report = verifier.verify_claim(claim)
    assert report.status == "SUPPORTED"
    assert report.confidence == 1.0


def test_verifier_experiment_claim_missing_run() -> None:
    graph = ProvenanceGraph(question="Test question")
    missing_run_id = uuid4()
    claim = ResearchClaim(
        claim_text="Phantom experiment claim.",
        origin="experiment",
        experiment_run_id=missing_run_id,
    )
    graph.add_claim(claim, experiment_run_id=missing_run_id)

    mgr = CitationManager()
    verifier = CitationVerifier(provenance_graph=graph, citation_manager=mgr, experiment_runs=[])

    report = verifier.verify_claim(claim)
    assert report.status == "UNSUPPORTED"
    assert any("does not exist" in iss for iss in report.issues)
