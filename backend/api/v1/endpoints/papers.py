"""API endpoints for academic paper search, acquisition, and ingestion."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.core.config import Settings, get_settings
from backend.core.models import Source
from backend.ingestion.models import DocumentChunk, IngestionResult
from backend.ingestion.pipeline import IngestionPipeline
from backend.tools.arxiv import ArxivClient
from backend.tools.semantic_scholar import SemanticScholarClient

router = APIRouter(prefix="/papers", tags=["Papers"])


class PaperIngestRequest(BaseModel):
    """Payload to trigger paper ingestion."""

    url: str | None = Field(default=None, description="Direct URL to paper PDF or abstract")
    title: str | None = Field(default=None, description="Optional preferred title")
    source: Source | None = Field(default=None, description="Pre-existing Source object")
    force: bool = Field(default=False, description="Whether to bypass cache and force re-download")


@router.get("/search", response_model=list[Source], summary="Search academic papers")
async def search_papers(
    query: str = Query(..., min_length=2, description="Research query or keywords"),
    provider: str = Query(default="arxiv", description="Provider: arxiv or semantic_scholar"),
    limit: int = Query(default=10, ge=1, le=50, description="Max results"),
    settings: Settings = Depends(get_settings),
) -> list[Source]:
    """Search academic databases (arXiv, Semantic Scholar) and return normalized sources."""
    normalized_provider = provider.lower().strip()

    if normalized_provider == "arxiv":
        client = ArxivClient(settings=settings)
        return await client.search(query=query, max_results=limit)

    if normalized_provider in {"semantic_scholar", "s2"}:
        s2_client = SemanticScholarClient(settings=settings)
        return await s2_client.search(query=query, limit=limit)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported provider '{provider}'. Must be 'arxiv' or 'semantic_scholar'",
    )


@router.post("/ingest", response_model=IngestionResult, summary="Ingest academic paper")
async def ingest_paper(
    payload: PaperIngestRequest,
    settings: Settings = Depends(get_settings),
) -> IngestionResult:
    """Download, parse, chunk, and cache an academic paper from a URL or Source."""
    pipeline = IngestionPipeline(settings=settings)

    try:
        if payload.source:
            return await pipeline.ingest_source(payload.source, force=payload.force)

        if payload.url:
            return await pipeline.ingest_url(
                url=payload.url,
                title=payload.title,
                force=payload.force,
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'url' or 'source' must be supplied for ingestion",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {exc}",
        ) from exc


@router.get(
    "/{doc_id}/chunks",
    response_model=list[DocumentChunk],
    summary="Get chunks for ingested paper",
)
async def get_paper_chunks(
    doc_id: str,
    settings: Settings = Depends(get_settings),
) -> list[DocumentChunk]:
    """Retrieve structured chunks for a previously ingested paper by document ID."""
    clean_id = doc_id.replace("..", "").replace("/", "").replace("\\", "")
    chunks_file = settings.chunks_dir / f"{clean_id}_chunks.json"

    if not chunks_file.exists():
        # Also try with 'doc_' prefix if not provided
        alt_file = settings.chunks_dir / f"doc_{clean_id}_chunks.json"
        if alt_file.exists():
            chunks_file = alt_file
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chunks for document '{doc_id}' not found in cache",
            )

    try:
        with open(chunks_file, encoding="utf-8") as f:
            raw_data = json.load(f)
        return [DocumentChunk.model_validate(c) for c in raw_data]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed loading chunks for '{doc_id}': {exc}",
        ) from exc
