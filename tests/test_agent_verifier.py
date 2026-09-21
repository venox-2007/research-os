"""Unit tests for EvidenceVerifier auditing and lineage tracking."""

from uuid import uuid4

import pytest

from backend.agents.state import create_initial_research_state
from backend.agents.verifier import EvidenceVerifier
from backend.core.models import Evidence


@pytest.mark.asyncio
async def test_verifier_filters_trivial_content() -> None:
    """Verify that verifier rejects short or empty evidence snippets."""
    verifier = EvidenceVerifier()
    state = create_initial_research_state(question="How does speculative decoding work?")

    trivial_ev = Evidence(
        source_id=uuid4(),
        source_title="Empty Doc",
        content="too short",
        section="Intro",
        confidence_score=0.9,
    )
    state["retrieved_evidence"] = [trivial_ev.model_dump(mode="json")]

    update = await verifier.verify_step(state)
    assert len(update["verified_evidence"]) == 0
    assert len(update["verification_results"]) == 1
    assert update["verification_results"][0]["relevant"] is False
    assert update["verification_results"][0]["support_status"] == "unsupported"


@pytest.mark.asyncio
async def test_verifier_accepts_supported_evidence() -> None:
    """Verify verifier accepts substantial contextual evidence and maintains lineage."""
    verifier = EvidenceVerifier()
    question = "What are the computational trade-offs of hybrid RAG?"
    state = create_initial_research_state(question=question)

    substantive_ev = Evidence(
        source_id=uuid4(),
        chunk_id="chunk_hybrid_001",
        source_title="Hybrid Retrieval Analysis",
        content=(
            "Hybrid RAG combining dense semantic vectors with BM25 keyword matching achieves "
            "higher retrieval precision than dense-only retrieval, while incurring a modest 15% latency penalty."
        ),
        section="3.2 Trade-offs",
        page_number=5,
        confidence_score=0.95,
        extraction_method="hybrid_rag",
    )
    state["retrieved_evidence"] = [substantive_ev.model_dump(mode="json")]

    update = await verifier.verify_step(state)
    assert len(update["verified_evidence"]) == 1
    assert update["verified_evidence"][0]["chunk_id"] == "chunk_hybrid_001"
    assert len(update["verification_results"]) == 1
    assert update["verification_results"][0]["relevant"] is True
    assert update["verification_results"][0]["support_status"] in {
        "supported",
        "partially_supported",
    }


@pytest.mark.asyncio
async def test_verifier_detects_contradictions() -> None:
    """Verify verifier flags contradiction markers in retrieved evidence."""
    verifier = EvidenceVerifier()
    question = "Does model quantization degrade reasoning accuracy?"
    state = create_initial_research_state(question=question)

    contradictory_ev = Evidence(
        source_id=uuid4(),
        source_title="Conflicting Study on Quantization",
        content=(
            "Contrary to previous studies claiming zero degradation, our empirical evaluation "
            "shows that 4-bit quantization significantly degrades reasoning accuracy on mathematical benchmarks."
        ),
        section="Discussion",
        page_number=8,
    )
    state["retrieved_evidence"] = [contradictory_ev.model_dump(mode="json")]

    update = await verifier.verify_step(state)
    assert len(update["contradictions"]) >= 1
    assert "Conflicting Study on Quantization" in update["contradictions"][0]
