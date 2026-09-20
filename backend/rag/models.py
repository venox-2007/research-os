"""Pydantic domain models and diagnostic structures for the RAG subsystem."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class VectorSearchResult(BaseModel):
    """Result from dense FAISS similarity search."""

    chunk_id: str = Field(..., description="Unique document chunk identifier")
    score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    rank: int = Field(default=0, description="1-indexed rank in vector search results")
    metadata: dict[str, Any] = Field(default_factory=dict)


class BM25SearchResult(BaseModel):
    """Result from sparse BM25 keyword retrieval."""

    chunk_id: str = Field(..., description="Unique document chunk identifier")
    score: float = Field(..., description="BM25 relevance score")
    rank: int = Field(default=0, description="1-indexed rank in BM25 search results")
    metadata: dict[str, Any] = Field(default_factory=dict)


class HybridCandidate(BaseModel):
    """Fused candidate combining dense and sparse rankings via Reciprocal Rank Fusion."""

    chunk_id: str = Field(..., description="Unique document chunk identifier")
    combined_score: float = Field(..., description="Fused RRF score")
    semantic_score: float | None = Field(default=None, description="Raw dense similarity score")
    semantic_rank: int | None = Field(default=None, description="Rank in dense vector search")
    bm25_score: float | None = Field(default=None, description="Raw BM25 score")
    bm25_rank: int | None = Field(default=None, description="Rank in sparse BM25 search")
    chunk_text: str = Field(..., description="Text content of the candidate chunk")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RerankedCandidate(BaseModel):
    """Final ranked candidate scored by the Cross-Encoder reranker."""

    chunk_id: str = Field(..., description="Unique document chunk identifier")
    rerank_score: float = Field(..., description="Cross-encoder relevance logit/score")
    hybrid_score: float = Field(..., description="Prior fused RRF score")
    chunk_text: str = Field(..., description="Chunk content")
    start_page: int = Field(default=1, description="Starting page coordinate")
    end_page: int = Field(default=1, description="Ending page coordinate")
    section: str | None = Field(default=None, description="Academic section title")
    source_id: UUID | None = Field(default=None, description="Parent Source UUID")
    source_title: str | None = Field(default=None, description="Parent Source title")
    metadata: dict[str, Any] = Field(default_factory=dict)


class RAGDiagnostics(BaseModel):
    """Performance and telemetry metrics captured during retrieval."""

    dense_candidates_count: int = 0
    sparse_candidates_count: int = 0
    fused_candidates_count: int = 0
    reranked_count: int = 0
    dense_time_ms: float = 0.0
    sparse_time_ms: float = 0.0
    fusion_time_ms: float = 0.0
    rerank_time_ms: float = 0.0
    total_time_ms: float = 0.0
    device_used: str = "cpu"
    embedding_model: str = ""
    reranker_model: str = ""


class RAGQueryResult(BaseModel):
    """Deliverable output of the complete RAG pipeline."""

    query: str = Field(..., description="Original search query")
    results: list[RerankedCandidate] = Field(
        default_factory=list, description="Top ranked evidence chunks"
    )
    diagnostics: RAGDiagnostics = Field(default_factory=RAGDiagnostics)
