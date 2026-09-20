"""Unit tests for the IR retrieval evaluation suite."""

import pytest

from backend.rag.evaluation import (
    RetrievalEvaluator,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_recall_at_k():
    relevant = {"doc1", "doc2", "doc3"}
    retrieved = ["doc1", "doc4", "doc2", "doc5"]

    assert recall_at_k(retrieved, relevant, k=1) == pytest.approx(1 / 3)
    assert recall_at_k(retrieved, relevant, k=2) == pytest.approx(1 / 3)
    assert recall_at_k(retrieved, relevant, k=3) == pytest.approx(2 / 3)
    assert recall_at_k(retrieved, relevant, k=4) == pytest.approx(2 / 3)
    assert recall_at_k(retrieved, set(), k=5) == 0.0


def test_precision_at_k():
    relevant = {"doc1", "doc2"}
    retrieved = ["doc1", "doc3", "doc2", "doc4"]

    assert precision_at_k(retrieved, relevant, k=1) == 1.0
    assert precision_at_k(retrieved, relevant, k=2) == 0.5
    assert precision_at_k(retrieved, relevant, k=4) == 0.5
    assert precision_at_k(retrieved, relevant, k=0) == 0.0


def test_mean_reciprocal_rank():
    relevant = {"doc2", "doc3"}
    assert mean_reciprocal_rank(["doc1", "doc2", "doc3"], relevant) == 0.5
    assert mean_reciprocal_rank(["doc2", "doc1"], relevant) == 1.0
    assert mean_reciprocal_rank(["doc4", "doc5"], relevant) == 0.0
    assert mean_reciprocal_rank([], relevant) == 0.0


def test_ndcg_at_k():
    # Graded relevance
    grades = {"doc1": 3.0, "doc2": 2.0, "doc3": 1.0}

    # Perfect ranking
    perfect = ["doc1", "doc2", "doc3"]
    assert pytest.approx(ndcg_at_k(perfect, grades, k=3), rel=1e-3) == 1.0

    # Sub-optimal ranking
    imperfect = ["doc3", "doc2", "doc1"]
    score = ndcg_at_k(imperfect, grades, k=3)
    assert 0.0 < score < 1.0

    # Empty cases
    assert ndcg_at_k([], grades, k=3) == 0.0
    assert ndcg_at_k(["doc1"], {}, k=3) == 0.0


def test_retrieval_evaluator_run():
    evaluator = RetrievalEvaluator(mock_mode=True)
    report = evaluator.evaluate()

    assert report.queries_count == len(evaluator.queries)
    assert report.corpus_size == len(evaluator.chunks)
    assert "BM25 Keyword" in report.methods
    assert "Dense Vector" in report.methods
    assert "Hybrid (RRF)" in report.methods
    assert "Hybrid + Reranker" in report.methods

    # All metrics should be in [0.0, 1.0]
    for _method_name, metrics in report.methods.items():
        assert 0.0 <= metrics.recall_at_10 <= 1.0
        assert 0.0 <= metrics.precision_at_5 <= 1.0
        assert 0.0 <= metrics.mrr <= 1.0
        assert 0.0 <= metrics.ndcg_at_10 <= 1.0

    assert "| Retrieval Strategy |" in report.markdown_table
