"""API endpoints for indexing document chunks and performing hybrid RAG retrieval."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.core.config import Settings, get_settings
from backend.core.models import Evidence
from backend.evidence.store import SQLiteEvidenceStore
from backend.rag.indexer import RAGIndexer
from backend.rag.models import RAGQueryResult
from backend.rag.pipeline import RAGPipeline

router = APIRouter(tags=["RAG"])


class RAGIndexRequest(BaseModel):
    """Payload to trigger chunk indexing."""

    rebuild: bool = Field(default=False, description="Whether to rebuild indices from scratch")


class RAGSearchRequest(BaseModel):
    """Payload to execute hybrid retrieval."""

    query: str = Field(..., min_length=2, description="Research query or hypothesis phrase")
    top_k: int | None = Field(default=5, ge=1, le=50, description="Final evidence count")
    top_n_rerank: int | None = Field(
        default=15, ge=1, le=100, description="Candidate pool to rerank"
    )
    use_reranker: bool = Field(default=True, description="Enable cross-encoder reranking")
    save_evidence: bool = Field(
        default=True, description="Persist retrieved items to EvidenceStore"
    )


@router.post("/rag/index", summary="Index document chunks")
async def index_chunks(
    payload: RAGIndexRequest,
    settings: Settings = Depends(get_settings),
) -> dict:
    """Scan cached document chunks and index into FAISS and BM25."""
    try:
        indexer = RAGIndexer(settings=settings)
        stats = indexer.index_cached_chunks(rebuild=payload.rebuild)
        return {
            "status": "success",
            "rebuild": payload.rebuild,
            **stats,
        }
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Indexing failed: {exc}",
        ) from exc


@router.post("/rag/search", response_model=RAGQueryResult, summary="Execute hybrid RAG retrieval")
async def search_rag(
    payload: RAGSearchRequest,
    settings: Settings = Depends(get_settings),
) -> RAGQueryResult:
    """Perform dense FAISS + sparse BM25 hybrid retrieval with cross-encoder reranking."""
    try:
        pipeline = RAGPipeline(settings=settings)
        return pipeline.search(
            query=payload.query,
            top_k=payload.top_k,
            top_n_rerank=payload.top_n_rerank,
            use_reranker=payload.use_reranker,
            save_to_evidence_store=payload.save_evidence,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG search failed: {exc}",
        ) from exc


@router.get("/rag/stats", summary="Get RAG index stats")
async def get_rag_stats(settings: Settings = Depends(get_settings)) -> dict:
    """Return runtime metadata on active vector and keyword indices."""
    pipeline = RAGPipeline(settings=settings)
    return {
        "dense_index_count": pipeline.vector_store.total_vectors,
        "bm25_index_count": pipeline.bm25_index.total_documents,
        "evidence_count": pipeline.evidence_store.count,
        "faiss_total_vectors": pipeline.vector_store.total_vectors,
        "bm25_total_documents": pipeline.bm25_index.total_documents,
        "embedding_model": pipeline.embedder.model_name,
        "reranker_model": pipeline.reranker.model_name,
        "device": pipeline.embedder.device,
        "indices_dir": str(settings.indices_dir),
    }


@router.get("/evidence/{evidence_id}", response_model=Evidence, summary="Get evidence by ID")
async def get_evidence_item(
    evidence_id: UUID,
    settings: Settings = Depends(get_settings),
) -> Evidence:
    """Fetch verified evidence snippet by unique identifier."""
    store = SQLiteEvidenceStore(settings=settings)
    item = store.get_evidence(evidence_id)
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence with ID '{evidence_id}' not found",
        )
    return item


@router.get("/evidence", response_model=list[Evidence], summary="List recent evidence")
async def list_recent_evidence(
    limit: int = Query(default=20, ge=1, le=100),
    settings: Settings = Depends(get_settings),
) -> list[Evidence]:
    """Retrieve recently recorded evidence items."""
    store = SQLiteEvidenceStore(settings=settings)
    return store.list_all(limit=limit)
