"""Unit tests for ProvenanceGraph and lineage tracking."""

from backend.core.models import Evidence, Source
from backend.synthesis.models import ResearchClaim
from backend.synthesis.provenance import ProvenanceGraph


def test_provenance_graph_registration() -> None:
    graph = ProvenanceGraph(question="How does self-attention work?")
    src = Source(
        title="Attention Is All You Need", authors=["Vaswani, A."], publication_date="2017"
    )
    ev = Evidence(
        source_id=src.id,
        content="Self-attention relates different positions of a single sequence.",
        section="3.2",
        page_number=3,
    )
    graph.register_source(src)
    graph.register_evidence(ev)

    claim = ResearchClaim(
        claim_text="Self-attention processes sequences in parallel.",
        claim_type="finding",
        supporting_evidence_ids=[ev.id],
        source_ids=[src.id],
        support_status="SUPPORTED",
    )
    graph.add_claim(claim)

    # Retrieval tests
    retrieved_ev = graph.get_evidence_for_claim(claim.id)
    retrieved_src = graph.get_sources_for_claim(claim.id)
    assert len(retrieved_ev) == 1
    assert retrieved_ev[0].content == ev.content
    assert len(retrieved_src) == 1
    assert retrieved_src[0].title == "Attention Is All You Need"


def test_provenance_chain_generation() -> None:
    graph = ProvenanceGraph(question="Hybrid search advantages")
    src = Source(title="BM25 and Vector Search", authors=["Expert, A."])
    ev = Evidence(
        source_id=src.id,
        content="Hybrid search combines lexical and semantic advantages.",
        section="4. Analysis",
        page_number=5,
    )
    graph.register_source(src)
    graph.register_evidence(ev)

    claim = ResearchClaim(
        claim_text="Hybrid search achieves superior robustness.",
        claim_type="finding",
        supporting_evidence_ids=[ev.id],
        source_ids=[src.id],
    )
    graph.add_claim(claim)

    chain = graph.get_provenance_chain(claim.id)
    assert chain["claim_id"] == str(claim.id)
    assert "Question" in chain["lineage_string"]
    assert "Evidence" in chain["lineage_string"]
    assert "BM25 and Vector Search" in chain["lineage_string"]


def test_provenance_unsupported_claim_detection() -> None:
    graph = ProvenanceGraph(question="Test question")
    claim_unsupported = ResearchClaim(
        claim_text="Quantum models outperform classical computers on this benchmark.",
        claim_type="finding",
        supporting_evidence_ids=[],
        source_ids=[],
    )
    graph.add_claim(claim_unsupported)

    unsupported = graph.detect_unsupported_claims()
    assert len(unsupported) == 1
    assert unsupported[0].id == claim_unsupported.id


def test_provenance_duplicate_claim_detection() -> None:
    graph = ProvenanceGraph(question="Duplicate detection")
    claim1 = ResearchClaim(
        claim_text="Dense embeddings capture semantic similarity between natural language passages.",
        claim_type="finding",
    )
    claim2 = ResearchClaim(
        claim_text="Dense embeddings capture semantic similarity between natural language text passages.",
        claim_type="finding",
    )
    graph.add_claim(claim1)
    graph.add_claim(claim2)

    duplicates = graph.detect_duplicate_claims(similarity_threshold=0.80)
    assert len(duplicates) == 1
    c1, c2, sim = duplicates[0]
    assert sim >= 0.80


def test_provenance_contradiction_detection() -> None:
    graph = ProvenanceGraph(question="Contradiction query")
    claim_contra = ResearchClaim(
        claim_text="Findings diverge on whether BM25 or dense retrieval achieves lower latency.",
        claim_type="comparison",
        is_contradicted=True,
        contradiction_notes="Study A says dense is 2x faster, Study B says BM25 is 5x faster.",
    )
    graph.add_claim(claim_contra)

    contras = graph.detect_contradictory_evidence()
    assert len(contras) == 1
    assert "Study A says dense is 2x faster" in contras[0]["contradiction_notes"]


def test_provenance_completeness_ratio() -> None:
    graph = ProvenanceGraph(question="Completeness ratio")
    src = Source(title="Source 1")
    ev = Evidence(source_id=src.id, content="Content")
    graph.register_source(src)
    graph.register_evidence(ev)

    claim_valid = ResearchClaim(
        claim_text="Valid claim",
        supporting_evidence_ids=[ev.id],
        source_ids=[src.id],
    )
    claim_invalid = ResearchClaim(
        claim_text="Invalid claim",
        supporting_evidence_ids=[],
        source_ids=[],
    )
    graph.add_claim(claim_valid)
    graph.add_claim(claim_invalid)

    ratio = graph.compute_provenance_completeness()
    assert ratio == 0.5
