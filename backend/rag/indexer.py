"""Indexer for building, persisting, and incrementally updating FAISS and BM25 indices."""

import json
from typing import Any

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.ingestion.models import DocumentChunk
from backend.rag.bm25 import BM25Index
from backend.rag.embeddings import LocalEmbedder, get_embedder
from backend.rag.vector_store import FAISSVectorStore

logger = get_logger("rag.indexer")


class RAGIndexer:
    """Coordinates indexing of document chunks into FAISS and BM25."""

    def __init__(
        self,
        settings: Settings | None = None,
        embedder: LocalEmbedder | None = None,
        vector_store: FAISSVectorStore | None = None,
        bm25_index: BM25Index | None = None,
        pipeline: Any | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        if pipeline is not None:
            self.embedder = pipeline.embedder
            self.vector_store = pipeline.vector_store
            self.bm25_index = pipeline.bm25_index
        else:
            self.embedder = embedder or get_embedder()
            self.vector_store = vector_store or FAISSVectorStore(
                dimension=self.embedder.dimension,
                index_dir=self.settings.indices_dir,
            )
            self.bm25_index = bm25_index or BM25Index(index_dir=self.settings.indices_dir)

        # Attempt to load pre-existing indices
        self.vector_store.load()
        self.bm25_index.load()

    def index_chunks(
        self,
        chunks: list[DocumentChunk],
        rebuild: bool = False,
    ) -> dict[str, int]:
        """Index a list of chunks into both FAISS and BM25.

        Args:
            chunks: List of DocumentChunk items.
            rebuild: If True, clear existing indices and re-index all chunks.

        Returns:
            Dictionary with counts of indexed and skipped chunks.
        """
        if rebuild:
            logger.info("Rebuilding indices from scratch...")
            self.vector_store.clear()
            self.bm25_index.clear()

        # Deduplicate chunks against existing indices
        new_chunks = [c for c in chunks if c.chunk_id not in self.vector_store.chunk_metadata]

        if not new_chunks:
            logger.info("No new chunks to index. All %d chunks already present.", len(chunks))
            return {
                "new_indexed": 0,
                "indexed_chunks": 0,
                "skipped_existing": len(chunks),
                "total": self.vector_store.total_vectors,
                "dense_index_size": self.vector_store.total_vectors,
                "bm25_index_size": self.bm25_index.total_documents,
            }

        logger.info(
            "Encoding %d new chunks with '%s'...", len(new_chunks), self.embedder.model_name
        )
        texts = [c.text for c in new_chunks]
        embeddings = self.embedder.embed_documents(texts)

        # Update FAISS
        added_faiss = self.vector_store.add_chunks(new_chunks, embeddings)

        # Update BM25
        self.bm25_index.index_chunks(new_chunks)

        # Persist indices to disk
        self.save()

        return {
            "new_indexed": added_faiss,
            "indexed_chunks": added_faiss,
            "skipped_existing": len(chunks) - len(new_chunks),
            "total": self.vector_store.total_vectors,
            "dense_index_size": self.vector_store.total_vectors,
            "bm25_index_size": self.bm25_index.total_documents,
        }

    def index_cached_chunks(self, rebuild: bool = False) -> dict[str, int]:
        """Scan data/chunks directory and index all available chunks from M2."""
        chunks_dir = self.settings.chunks_dir
        if not chunks_dir.exists():
            logger.warning("Chunks directory %s does not exist", chunks_dir)
            return {
                "new_indexed": 0,
                "indexed_chunks": 0,
                "skipped_existing": 0,
                "total": 0,
                "dense_index_size": 0,
                "bm25_index_size": 0,
            }

        discovered_chunks: list[DocumentChunk] = []
        for file in sorted(chunks_dir.glob("*.json")):
            try:
                with open(file, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        discovered_chunks.append(DocumentChunk.model_validate(item))
                elif isinstance(data, dict):
                    discovered_chunks.append(DocumentChunk.model_validate(data))
            except Exception as exc:
                logger.warning("Error reading %s: %s", file.name, exc)

        logger.info("Discovered %d chunks in %s", len(discovered_chunks), chunks_dir)
        return self.index_chunks(discovered_chunks, rebuild=rebuild)

    def index_all(self) -> dict[str, int]:
        """Convenience method to index all cached chunks from scratch."""
        return self.index_cached_chunks(rebuild=True)

    def index_incremental(self) -> dict[str, int]:
        """Convenience method to incrementally index newly added cached chunks."""
        return self.index_cached_chunks(rebuild=False)

    def save(self) -> None:
        """Persist both FAISS and BM25 indices to indices_dir."""
        self.vector_store.save()
        self.bm25_index.save()
