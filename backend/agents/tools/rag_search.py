"""Tool exposing the Milestone 3 Hybrid RAG retrieval pipeline to research agents."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from backend.agents.tools.base import BaseResearchTool
from backend.core.config import Settings, get_settings
from backend.core.models import Evidence
from backend.rag.pipeline import RAGPipeline


class RAGSearchInput(BaseModel):
    """Input parameters for the hybrid RAG search tool."""

    query: str = Field(
        ..., min_length=2, description="Target query or research concept to retrieve"
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of top evidence chunks to retain"
    )


class RAGSearchTool(BaseResearchTool):
    """Retrieves high-precision evidence using dense FAISS + sparse BM25 + Cross-Encoder reranking."""

    name: str = "search_rag"
    description: str = (
        "Search the ingested scientific literature using hybrid dense/sparse retrieval and reranking. "
        "Returns verified excerpts with exact paper, section, and page coordinates."
    )
    args_schema: type[BaseModel] = RAGSearchInput

    def __init__(
        self,
        pipeline: RAGPipeline | None = None,
        settings: Settings | None = None,
        mock_mode: bool | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.pipeline = pipeline or RAGPipeline(
            settings=self.settings,
            mock_mode=mock_mode,
        )

    async def _execute(self, query: str, top_k: int = 5) -> dict[str, Any]:
        """Execute hybrid search and format findings with full provenance coordinates."""
        query_result = self.pipeline.search(
            query=query,
            top_k=top_k,
            save_to_evidence_store=True,
        )

        evidence_items: list[dict[str, Any]] = []
        for candidate in query_result.results:
            # Query the stored Evidence from the SQLite evidence store to obtain UUID
            stored = self.pipeline.evidence_store.get_by_chunk(candidate.chunk_id)
            ev_id = stored[0].id if stored else None

            evidence_obj = Evidence(
                id=ev_id or UUID(int=0),
                source_id=candidate.source_id,
                chunk_id=candidate.chunk_id,
                source_title=candidate.source_title,
                content=candidate.chunk_text,
                section=candidate.section,
                page_number=candidate.start_page,
                page_numbers=list(range(candidate.start_page, candidate.end_page + 1))
                if candidate.end_page >= candidate.start_page
                else [candidate.start_page],
                confidence_score=max(0.0, min(1.0, candidate.rerank_score)),
                extraction_method="hybrid_rag_tool",
            )
            evidence_items.append(evidence_obj.model_dump(mode="json"))

        return {
            "query": query,
            "evidence_count": len(evidence_items),
            "evidence": evidence_items,
            "diagnostics": query_result.diagnostics.model_dump(mode="json"),
        }
