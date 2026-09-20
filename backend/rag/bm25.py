"""Sparse lexical search using BM25Okapi with academic text tokenization."""

import json
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.ingestion.models import DocumentChunk
from backend.rag.models import BM25SearchResult

logger = get_logger("rag.bm25")

# Minimal English/academic stopword set to keep index lean
DEFAULT_STOPWORDS = {
    "a",
    "an",
    "the",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "this",
    "that",
    "these",
    "those",
    "and",
    "or",
    "but",
    "if",
    "because",
    "so",
    "than",
    "too",
    "very",
    "can",
    "will",
    "just",
    "should",
}


class BM25Index:
    """In-memory BM25Okapi index with local JSON serialization."""

    def __init__(
        self,
        index_dir: Path | str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.index_dir = Path(index_dir) if index_dir else self.settings.indices_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.bm25: BM25Okapi | None = None
        self.chunk_ids: list[str] = []
        self.chunk_metadata: dict[str, dict[str, Any]] = {}
        self.tokenized_corpus: list[list[str]] = []

    @property
    def total_documents(self) -> int:
        """Return number of documents in current BM25 index."""
        return len(self.chunk_ids)

    @property
    def count(self) -> int:
        """Alias for total_documents."""
        return self.total_documents

    def build(
        self,
        chunk_ids: list[str],
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        """Build BM25 index directly from raw chunk IDs, texts, and optional metadatas."""
        self.chunk_ids = []
        self.tokenized_corpus = []
        self.chunk_metadata = {}
        metas = metadatas or [{} for _ in chunk_ids]
        for cid, doc, meta in zip(chunk_ids, documents, metas, strict=False):
            tokens = self.tokenize(doc)
            self.chunk_ids.append(cid)
            self.tokenized_corpus.append(tokens)
            entry = {"chunk_id": cid, "text": doc, "metadata": meta}
            entry.update(meta)
            self.chunk_metadata[cid] = entry
        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
        return len(self.chunk_ids)

    def tokenize(self, text: str) -> list[str]:
        """Convert text to lowercased words stripping symbols and common stopwords."""
        words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
        return [w for w in words if w not in DEFAULT_STOPWORDS]

    def index_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Add chunks to the BM25 index and build/rebuild the model.

        Args:
            chunks: List of DocumentChunk models to index.

        Returns:
            Total count of chunks now indexed.
        """
        if not chunks:
            return self.total_documents

        for chunk in chunks:
            if chunk.chunk_id not in self.chunk_metadata:
                tokens = self.tokenize(chunk.text)
                self.chunk_ids.append(chunk.chunk_id)
                self.tokenized_corpus.append(tokens)
                self.chunk_metadata[chunk.chunk_id] = {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "source_id": str(chunk.source_id),
                    "section": chunk.section,
                    "start_page": chunk.start_page,
                    "end_page": chunk.end_page,
                    "text": chunk.text,
                    "metadata": chunk.metadata,
                }

        if self.tokenized_corpus:
            self.bm25 = BM25Okapi(self.tokenized_corpus)
            logger.info("Built BM25 index over %d chunks", len(self.tokenized_corpus))

        return len(self.chunk_ids)

    def search(self, query: str, top_k: int = 10) -> list[BM25SearchResult]:
        """Execute sparse lexical search for a given keyword query.

        Args:
            query: Keyword query phrase.
            top_k: Max results to retrieve.

        Returns:
            List of BM25SearchResult items ordered by relevance score.
        """
        if not self.bm25 or not self.chunk_ids:
            return []

        tokens = self.tokenize(query)
        if not tokens:
            return []

        scores = self.bm25.get_scores(tokens)
        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        results: list[BM25SearchResult] = []
        rank = 1
        for idx, score in scored_indices:
            doc_tokens = set(self.tokenized_corpus[idx])
            has_match = any(t in doc_tokens for t in tokens)
            if not has_match and score <= 0:
                continue

            chunk_id = self.chunk_ids[idx]
            meta = self.chunk_metadata.get(chunk_id, {})
            results.append(
                BM25SearchResult(
                    chunk_id=chunk_id,
                    score=float(max(0.01, score)) if has_match and score <= 0 else float(score),
                    rank=rank,
                    metadata=meta,
                )
            )
            rank += 1
            if len(results) >= top_k:
                break

        return results

    def save(self, directory: Path | str | None = None) -> None:
        """Persist BM25 corpus and metadata mapping to disk."""
        target_dir = Path(directory) if directory else self.index_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        meta_file = target_dir / "bm25_metadata.json"

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "chunk_ids": self.chunk_ids,
                    "tokenized_corpus": self.tokenized_corpus,
                    "metadata": self.chunk_metadata,
                },
                f,
                indent=2,
            )
        logger.info("Saved BM25 corpus (%d docs) to %s", len(self.chunk_ids), target_dir)

    def load(self, directory: Path | str | None = None) -> bool:
        """Load BM25 corpus and rebuild the index."""
        target_dir = Path(directory) if directory else self.index_dir
        meta_file = target_dir / "bm25_metadata.json"

        if not meta_file.exists():
            logger.info("No BM25 index found at %s", target_dir)
            return False

        try:
            with open(meta_file, encoding="utf-8") as f:
                data = json.load(f)

            self.chunk_ids = data.get("chunk_ids", [])
            self.tokenized_corpus = data.get("tokenized_corpus", [])
            self.chunk_metadata = data.get("metadata", {})

            if self.tokenized_corpus:
                self.bm25 = BM25Okapi(self.tokenized_corpus)

            logger.info("Loaded BM25 index with %d docs from %s", len(self.chunk_ids), target_dir)
            return True
        except Exception as exc:
            logger.error("Failed to load BM25 index from %s: %s", target_dir, exc)
            return False

    def clear(self) -> None:
        """Clear the in-memory index."""
        self.bm25 = None
        self.chunk_ids.clear()
        self.tokenized_corpus.clear()
        self.chunk_metadata.clear()
