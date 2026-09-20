"""Hybrid retrieval fusing dense vector similarity and sparse BM25 scores via RRF."""

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.rag.models import BM25SearchResult, HybridCandidate, VectorSearchResult

logger = get_logger("rag.hybrid")


class HybridRetriever:
    """Combines dense FAISS and sparse BM25 rankings using Reciprocal Rank Fusion."""

    def __init__(
        self,
        rrf_k: int | None = None,
        weight_dense: float = 1.0,
        weight_sparse: float = 1.0,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.k = rrf_k or self.settings.rrf_k
        self.weight_dense = weight_dense
        self.weight_sparse = weight_sparse

    def fuse(
        self,
        dense_results: list[VectorSearchResult],
        sparse_results: list[BM25SearchResult],
        chunk_text_lookup: dict[str, str] | int | None = None,
        top_k: int | None = None,
        top_n: int = 15,
    ) -> list[HybridCandidate]:
        """Apply Reciprocal Rank Fusion (RRF) to merge dense and sparse rankings.

        Args:
            dense_results: Ordered vector search results.
            sparse_results: Ordered BM25 search results.
            chunk_text_lookup: Optional text lookup dict or positional top_n integer.
            top_k: Alias for top_n.
            top_n: Number of fused candidates to return.

        Returns:
            List of HybridCandidate objects sorted by descending fused score.
        """
        lookup: dict[str, str] = {}
        if isinstance(chunk_text_lookup, int):
            top_n = chunk_text_lookup
        elif isinstance(chunk_text_lookup, dict):
            lookup = chunk_text_lookup

        if top_k is not None:
            top_n = top_k

        combined_scores: dict[str, float] = {}
        dense_meta: dict[str, VectorSearchResult] = {}
        sparse_meta: dict[str, BM25SearchResult] = {}

        # 1. Score dense candidates
        for item in dense_results:
            dense_meta[item.chunk_id] = item
            score = self.weight_dense / (self.k + item.rank)
            combined_scores[item.chunk_id] = combined_scores.get(item.chunk_id, 0.0) + score

        # 2. Score sparse candidates
        for item in sparse_results:
            sparse_meta[item.chunk_id] = item
            score = self.weight_sparse / (self.k + item.rank)
            combined_scores[item.chunk_id] = combined_scores.get(item.chunk_id, 0.0) + score

        # 3. Sort candidates by fused RRF score
        sorted_chunk_ids = sorted(
            combined_scores.keys(),
            key=lambda cid: combined_scores[cid],
            reverse=True,
        )

        candidates: list[HybridCandidate] = []
        for cid in sorted_chunk_ids[:top_n]:
            d_item = dense_meta.get(cid)
            s_item = sparse_meta.get(cid)

            # Extract unified text and metadata
            meta = (d_item.metadata if d_item else {}) or (s_item.metadata if s_item else {})
            text = lookup.get(cid) or meta.get("text", "")

            candidates.append(
                HybridCandidate(
                    chunk_id=cid,
                    combined_score=float(combined_scores[cid]),
                    semantic_score=d_item.score if d_item else None,
                    semantic_rank=d_item.rank if d_item else None,
                    bm25_score=s_item.score if s_item else None,
                    bm25_rank=s_item.rank if s_item else None,
                    chunk_text=text,
                    metadata=meta,
                )
            )

        logger.info(
            "RRF fused %d dense and %d sparse into %d top candidates (k=%d)",
            len(dense_results),
            len(sparse_results),
            len(candidates),
            self.k,
        )
        return candidates
