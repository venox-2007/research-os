"""Unit tests for HybridRetriever and Reciprocal Rank Fusion."""

from backend.rag.hybrid import HybridRetriever
from backend.rag.models import BM25SearchResult, VectorSearchResult


def test_rrf_fusion_both_modalities():
    retriever = HybridRetriever(rrf_k=60)

    dense_results = [
        VectorSearchResult(chunk_id="chunk-1", score=0.95, rank=1),
        VectorSearchResult(chunk_id="chunk-2", score=0.85, rank=2),
    ]
    sparse_results = [
        BM25SearchResult(chunk_id="chunk-2", score=12.5, rank=1),
        BM25SearchResult(chunk_id="chunk-3", score=8.0, rank=2),
    ]
    lookup = {
        "chunk-1": "Text of chunk 1",
        "chunk-2": "Text of chunk 2",
        "chunk-3": "Text of chunk 3",
    }

    fused = retriever.fuse(dense_results, sparse_results, lookup, top_k=3)

    assert len(fused) == 3
    # chunk-2 appears in both: 1/(60+2) + 1/(60+1) = 1/62 + 1/61 ~= 0.016129 + 0.016393 = 0.03252
    # chunk-1 appears in dense: 1/(60+1) = 0.016393
    # chunk-3 appears in sparse: 1/(60+2) = 0.016129
    # So chunk-2 should be rank 1!
    assert fused[0].chunk_id == "chunk-2"
    assert fused[0].semantic_rank == 2
    assert fused[0].bm25_rank == 1
    assert fused[0].chunk_text == "Text of chunk 2"

    assert fused[1].chunk_id == "chunk-1"
    assert fused[2].chunk_id == "chunk-3"


def test_rrf_fusion_empty_inputs():
    retriever = HybridRetriever(rrf_k=60)
    assert retriever.fuse([], [], {}) == []


def test_rrf_truncates_to_top_k():
    retriever = HybridRetriever(rrf_k=60)
    dense_results = [
        VectorSearchResult(chunk_id=f"c-{i}", score=0.9 - i * 0.01, rank=i) for i in range(1, 15)
    ]
    lookup = {f"c-{i}": f"Text {i}" for i in range(1, 15)}
    fused = retriever.fuse(dense_results, [], lookup, top_k=5)
    assert len(fused) == 5
