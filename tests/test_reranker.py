"""Unit tests for LocalReranker."""

from backend.rag.models import HybridCandidate
from backend.rag.reranker import LocalReranker, get_reranker


def test_mock_reranker_scoring():
    reranker = LocalReranker(mock_mode=True)
    candidates = [
        HybridCandidate(
            chunk_id="c-unrelated",
            combined_score=0.03,
            chunk_text="Quantum computing fundamentals and qubits.",
        ),
        HybridCandidate(
            chunk_id="c-match",
            combined_score=0.02,
            chunk_text="Low-Rank Adaptation LoRA fine-tuning for large language models.",
        ),
    ]

    results = reranker.rerank(query="LoRA fine-tuning LLM", candidates=candidates, top_n=2)
    assert len(results) == 2
    # In mock mode, keyword overlap boosts score. "c-match" overlaps with LoRA, fine-tuning, models.
    assert results[0].chunk_id == "c-match"
    assert results[0].rerank_score > results[1].rerank_score


def test_mock_reranker_empty():
    reranker = LocalReranker(mock_mode=True)
    assert reranker.rerank("any query", []) == []


def test_get_reranker_cached_singleton():
    r1 = get_reranker("test-model", mock_mode=True)
    r2 = get_reranker("test-model", mock_mode=True)
    assert r1 is r2
