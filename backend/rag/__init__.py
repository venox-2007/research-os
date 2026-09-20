"""Hybrid Retrieval-Augmented Generation (RAG) subsystem."""

from backend.rag.bm25 import BM25Index
from backend.rag.embeddings import EmbeddingError, LocalEmbedder, get_embedder
from backend.rag.hybrid import HybridRetriever
from backend.rag.indexer import RAGIndexer
from backend.rag.models import (
    BM25SearchResult,
    HybridCandidate,
    RAGDiagnostics,
    RAGQueryResult,
    RerankedCandidate,
    VectorSearchResult,
)
from backend.rag.pipeline import RAGPipeline
from backend.rag.reranker import LocalReranker, get_reranker
from backend.rag.vector_store import FAISSVectorStore

__all__ = [
    "BM25Index",
    "BM25SearchResult",
    "EmbeddingError",
    "FAISSVectorStore",
    "HybridCandidate",
    "HybridRetriever",
    "LocalEmbedder",
    "LocalReranker",
    "RAGDiagnostics",
    "RAGIndexer",
    "RAGPipeline",
    "RAGQueryResult",
    "RerankedCandidate",
    "VectorSearchResult",
    "get_embedder",
    "get_reranker",
]
