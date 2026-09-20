"""Local Cross-Encoder reranking engine for high-precision evidence scoring."""

from functools import lru_cache
from uuid import UUID

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.rag.models import HybridCandidate, RerankedCandidate

logger = get_logger("rag.reranker")


class LocalReranker:
    """Local cross-encoder scoring pairs of (query, candidate_chunk)."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        mock_mode: bool | None = None,
    ) -> None:
        self.settings = get_settings()
        self.model_name = model_name or self.settings.reranker_model
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else (self.settings.app_env == "testing" or self.settings.llm_provider == "mock")
        )
        self._model = None

        if device and device != "auto":
            self.device = device
        else:
            try:
                import torch

                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"

        if not self.mock_mode and self.model_name != "mock":
            self._load_model()

    def _load_model(self) -> None:
        """Load sentence-transformers CrossEncoder onto resolved device."""
        try:
            from sentence_transformers import CrossEncoder

            logger.info("Loading reranker '%s' on %s...", self.model_name, self.device)
            self._model = CrossEncoder(self.model_name, device=self.device)
            logger.info("Reranker '%s' initialized", self.model_name)
        except Exception as exc:
            logger.warning(
                "Could not load CrossEncoder ('%s'): %s. Using deterministic fallback.",
                self.model_name,
                exc,
            )
            self.mock_mode = True

    def rerank(
        self,
        query: str,
        candidates: list[HybridCandidate],
        top_k: int = 5,
        top_n: int | None = None,
    ) -> list[RerankedCandidate]:
        """Rerank hybrid candidates using query-chunk cross-attention scores.

        Args:
            query: User's original research question.
            candidates: Top candidates from hybrid RRF fusion.
            top_k: Final number of evidence chunks to retain.
            top_n: Alias for top_k.

        Returns:
            List of RerankedCandidate objects ordered by relevance.
        """
        if top_n is not None:
            top_k = top_n

        if not candidates or not query.strip():
            return []

        clean_query = query.strip()

        if self.mock_mode or self.model_name == "mock" or self._model is None:
            # Deterministic scoring based on keyword overlap + RRF score
            scored_candidates = []
            q_words = set(clean_query.lower().split())
            for c in candidates:
                c_words = set(c.chunk_text.lower().split())
                overlap = len(q_words & c_words) / max(1, len(q_words))
                sim_score = c.combined_score * 10.0 + overlap
                scored_candidates.append((sim_score, c))
            scored_candidates.sort(key=lambda x: x[0], reverse=True)
        else:
            pairs = [[clean_query, c.chunk_text] for c in candidates]
            scores = self._model.predict(pairs)
            scored_candidates = [(float(scores[i]), candidates[i]) for i in range(len(candidates))]
            scored_candidates.sort(key=lambda x: x[0], reverse=True)

        results: list[RerankedCandidate] = []
        for score, candidate in scored_candidates[:top_k]:
            meta = candidate.metadata
            src_id_str = meta.get("source_id")
            source_id = UUID(src_id_str) if src_id_str else None

            results.append(
                RerankedCandidate(
                    chunk_id=candidate.chunk_id,
                    rerank_score=score,
                    hybrid_score=candidate.combined_score,
                    chunk_text=candidate.chunk_text,
                    start_page=meta.get("start_page", 1),
                    end_page=meta.get("end_page", 1),
                    section=meta.get("section"),
                    source_id=source_id,
                    source_title=meta.get("document_title") or meta.get("title"),
                    metadata=meta,
                )
            )

        logger.info(
            "Reranked %d candidates down to top %d evidence chunks", len(candidates), len(results)
        )
        return results


@lru_cache(maxsize=1)
def get_reranker(model_name: str | None = None, mock_mode: bool | None = None) -> LocalReranker:
    """Singleton getter for LocalReranker."""
    settings = get_settings()
    name = model_name or settings.reranker_model
    return LocalReranker(model_name=name, mock_mode=mock_mode)
