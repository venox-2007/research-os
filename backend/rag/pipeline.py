"""End-to-end RAG retrieval pipeline coordinating semantic search, BM25, RRF, and reranking."""

import time

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.evidence.store import SQLiteEvidenceStore
from backend.rag.bm25 import BM25Index
from backend.rag.embeddings import LocalEmbedder, get_embedder
from backend.rag.hybrid import HybridRetriever
from backend.rag.models import RAGDiagnostics, RAGQueryResult, RerankedCandidate
from backend.rag.reranker import LocalReranker, get_reranker
from backend.rag.vector_store import FAISSVectorStore

logger = get_logger("rag.pipeline")


class RAGPipeline:
    """Full-featured hybrid retrieval pipeline for academic literature exploration."""

    def __init__(
        self,
        settings: Settings | None = None,
        embedder: LocalEmbedder | None = None,
        vector_store: FAISSVectorStore | None = None,
        bm25_index: BM25Index | None = None,
        hybrid_retriever: HybridRetriever | None = None,
        reranker: LocalReranker | None = None,
        evidence_store: SQLiteEvidenceStore | None = None,
        mock_mode: bool | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else (self.settings.app_env == "testing" or self.settings.llm_provider == "mock")
        )
        self.embedder = embedder or get_embedder(mock_mode=self.mock_mode)
        self.vector_store = vector_store or FAISSVectorStore(
            dimension=self.embedder.dimension,
            index_dir=self.settings.indices_dir,
        )
        self.bm25_index = bm25_index or BM25Index(index_dir=self.settings.indices_dir)
        self.hybrid_retriever = hybrid_retriever or HybridRetriever(rrf_k=self.settings.rrf_k)
        self.reranker = reranker or get_reranker(mock_mode=self.mock_mode)
        self.evidence_store = evidence_store or SQLiteEvidenceStore(settings=self.settings)

        # Load persisted indices if available
        self.vector_store.load()
        self.bm25_index.load()

    def search(
        self,
        query: str,
        top_k: int | None = None,
        top_n_rerank: int | None = None,
        use_reranker: bool = True,
        save_to_evidence_store: bool = True,
    ) -> RAGQueryResult:
        """Execute full hybrid retrieval pipeline.

        Args:
            query: Research question or search query.
            top_k: Number of final evidence chunks to return.
            top_n_rerank: Number of hybrid candidates to pass to reranker.
            use_reranker: Whether to perform cross-encoder reranking.
            save_to_evidence_store: If True, persist top evidence to SQLite store.

        Returns:
            RAGQueryResult with structured evidence candidates and diagnostics.
        """
        clean_query = query.strip()
        k_final = top_k or self.settings.top_k_retrieval
        n_rerank = top_n_rerank or self.settings.top_n_rerank

        diagnostics = RAGDiagnostics(
            embedding_model=self.embedder.model_name,
            reranker_model=self.reranker.model_name if use_reranker else "none",
            device_used=self.embedder.device,
        )
        t_start = time.perf_counter()

        if not clean_query or self.vector_store.total_vectors == 0:
            logger.info(
                "Empty query or empty index (vectors: %d). Returning empty result.",
                self.vector_store.total_vectors,
            )
            return RAGQueryResult(query=clean_query, results=[], diagnostics=diagnostics)

        # 1. Dense FAISS Search
        t_dense_start = time.perf_counter()
        query_vector = self.embedder.embed_query(clean_query)
        dense_candidates = self.vector_store.search(query_vector, top_k=n_rerank)
        diagnostics.dense_time_ms = (time.perf_counter() - t_dense_start) * 1000.0
        diagnostics.dense_candidates_count = len(dense_candidates)

        # 2. Sparse BM25 Search
        t_sparse_start = time.perf_counter()
        sparse_candidates = self.bm25_index.search(clean_query, top_k=n_rerank)
        diagnostics.sparse_time_ms = (time.perf_counter() - t_sparse_start) * 1000.0
        diagnostics.sparse_candidates_count = len(sparse_candidates)

        # 3. Reciprocal Rank Fusion (RRF)
        t_fusion_start = time.perf_counter()
        fused_candidates = self.hybrid_retriever.fuse(
            dense_results=dense_candidates,
            sparse_results=sparse_candidates,
            top_n=n_rerank,
        )
        diagnostics.fusion_time_ms = (time.perf_counter() - t_fusion_start) * 1000.0
        diagnostics.fused_candidates_count = len(fused_candidates)

        # 4. Cross-Encoder Reranking
        t_rerank_start = time.perf_counter()
        if use_reranker and fused_candidates:
            final_results = self.reranker.rerank(
                query=clean_query,
                candidates=fused_candidates,
                top_k=k_final,
            )
        else:
            final_results = [
                RerankedCandidate(
                    chunk_id=c.chunk_id,
                    rerank_score=c.combined_score,
                    hybrid_score=c.combined_score,
                    chunk_text=c.chunk_text,
                    start_page=c.metadata.get("start_page", 1),
                    end_page=c.metadata.get("end_page", 1),
                    section=c.metadata.get("section"),
                    metadata=c.metadata,
                )
                for c in fused_candidates[:k_final]
            ]
        diagnostics.rerank_time_ms = (time.perf_counter() - t_rerank_start) * 1000.0
        diagnostics.reranked_count = len(final_results)
        diagnostics.total_time_ms = (time.perf_counter() - t_start) * 1000.0

        # 5. Optionally persist evidence to SQLite store
        if save_to_evidence_store and self.evidence_store:
            for item in final_results:
                src_id = item.source_id or item.metadata.get("source_id")
                if src_id:
                    self.evidence_store.add_evidence(
                        source_id=src_id,
                        chunk_id=item.chunk_id,
                        source_title=item.source_title,
                        content=item.chunk_text,
                        section=item.section,
                        page_number=item.start_page,
                        end_page=item.end_page,
                        confidence_score=max(0.0, min(1.0, item.rerank_score)),
                        extraction_method="hybrid_rrf_reranked",
                    )

        logger.info(
            "Query '%s' retrieved %d evidence chunks in %.1fms",
            clean_query[:40],
            len(final_results),
            diagnostics.total_time_ms,
        )
        return RAGQueryResult(
            query=clean_query,
            results=final_results,
            diagnostics=diagnostics,
        )

    # Convenience alias for search
    query = search
