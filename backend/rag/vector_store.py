"""Local FAISS vector index with metadata persistence and cosine similarity search."""

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.ingestion.models import DocumentChunk
from backend.rag.models import VectorSearchResult

logger = get_logger("rag.vector_store")


class FAISSVectorStore:
    """In-process FAISS IndexFlatIP store with local JSON metadata mapping."""

    def __init__(
        self,
        dimension: int = 384,
        index_dir: Path | str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.dimension = dimension
        self.index_dir = Path(index_dir) if index_dir else self.settings.indices_dir
        self.index_dir.mkdir(parents=True, exist_ok=True)

        self.index: faiss.IndexFlatIP = faiss.IndexFlatIP(self.dimension)
        self.chunk_ids: list[str] = []
        self.chunk_metadata: dict[str, dict[str, Any]] = {}

    @property
    def total_vectors(self) -> int:
        """Return the number of vectors stored in the index."""
        return self.index.ntotal

    @property
    def count(self) -> int:
        """Alias for total_vectors."""
        return self.total_vectors

    def add_embeddings(
        self,
        embeddings: Any,
        chunk_ids: list[str],
        chunk_texts: list[str] | None = None,
        metadatas: list[dict[str, Any]] | None = None,
    ) -> int:
        """Add arbitrary precomputed embeddings with IDs and metadata."""
        if len(chunk_ids) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunk_ids)} IDs provided but got {len(embeddings)} vectors"
            )
        if not chunk_ids:
            return 0
        vectors = np.array(embeddings, dtype=np.float32)
        if len(vectors.shape) == 1:
            vectors = vectors.reshape(1, -1)
        if vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Dimension mismatch: vector dimension {vectors.shape[1]} does not match index {self.dimension}"
            )
        self.index.add(vectors)
        texts = chunk_texts or ["" for _ in chunk_ids]
        metas = metadatas or [{} for _ in chunk_ids]
        for cid, txt, meta in zip(chunk_ids, texts, metas, strict=False):
            self.chunk_ids.append(cid)
            entry = {"chunk_id": cid, "text": txt, "metadata": meta}
            entry.update(meta)
            self.chunk_metadata[cid] = entry
        return len(chunk_ids)

    def add_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: np.ndarray,
    ) -> int:
        """Add chunks and their normalized embedding vectors to the FAISS index.

        Args:
            chunks: List of DocumentChunk models.
            embeddings: 2D numpy array of shape (len(chunks), dimension).

        Returns:
            Number of newly added chunks.
        """
        if not chunks:
            return 0

        if len(chunks) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(chunks)} chunks provided but got {len(embeddings)} vectors"
            )

        # Filter out existing chunk IDs to prevent duplicate vectors
        new_indices: list[int] = []
        for i, chunk in enumerate(chunks):
            if chunk.chunk_id not in self.chunk_metadata:
                new_indices.append(i)

        if not new_indices:
            logger.info("All %d chunks are already indexed in FAISS.", len(chunks))
            return 0

        subset_chunks = [chunks[i] for i in new_indices]
        subset_vectors = embeddings[new_indices].astype(np.float32)

        # Ensure vectors match dimension
        if subset_vectors.shape[1] != self.dimension:
            raise ValueError(
                f"Vector dimension {subset_vectors.shape[1]} does not match index {self.dimension}"
            )

        self.index.add(subset_vectors)

        for chunk in subset_chunks:
            self.chunk_ids.append(chunk.chunk_id)
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

        logger.info(
            "Added %d vectors to FAISS index. Total indexed: %d",
            len(subset_chunks),
            self.total_vectors,
        )
        return len(subset_chunks)

    def search(
        self,
        query_vector: np.ndarray,
        top_k: int = 10,
    ) -> list[VectorSearchResult]:
        """Perform cosine similarity search against the index.

        Args:
            query_vector: 1D or 2D array representing the normalized query.
            top_k: Number of nearest neighbors to retrieve.

        Returns:
            List of VectorSearchResult items ordered by similarity.
        """
        if self.total_vectors == 0:
            return []

        # Format to 2D array
        vec = query_vector.reshape(1, -1).astype(np.float32)
        k = min(top_k, self.total_vectors)

        scores, indices = self.index.search(vec, k)
        results: list[VectorSearchResult] = []

        for rank, (score, idx) in enumerate(zip(scores[0], indices[0], strict=False), start=1):
            if idx < 0 or idx >= len(self.chunk_ids):
                continue
            chunk_id = self.chunk_ids[idx]
            meta = self.chunk_metadata.get(chunk_id, {})
            results.append(
                VectorSearchResult(
                    chunk_id=chunk_id,
                    score=float(score),
                    rank=rank,
                    metadata=meta,
                )
            )

        return results

    def save(self, directory: Path | str | None = None) -> None:
        """Persist the FAISS binary index and metadata mapping to disk."""
        target_dir = Path(directory) if directory else self.index_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        index_file = target_dir / "faiss.index"
        meta_file = target_dir / "faiss_metadata.json"

        faiss.write_index(self.index, str(index_file))

        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "chunk_ids": self.chunk_ids,
                    "metadata": self.chunk_metadata,
                    "dimension": self.dimension,
                },
                f,
                indent=2,
            )

        logger.info("Saved FAISS index (%d vectors) to %s", self.total_vectors, target_dir)

    def load(self, directory: Path | str | None = None) -> bool:
        """Load an existing FAISS index and metadata from disk."""
        target_dir = Path(directory) if directory else self.index_dir
        index_file = target_dir / "faiss.index"
        meta_file = target_dir / "faiss_metadata.json"

        if not index_file.exists() or not meta_file.exists():
            logger.info("No existing FAISS index found at %s", target_dir)
            return False

        try:
            self.index = faiss.read_index(str(index_file))
            with open(meta_file, encoding="utf-8") as f:
                data = json.load(f)

            self.chunk_ids = data.get("chunk_ids", [])
            self.chunk_metadata = data.get("metadata", {})
            self.dimension = data.get("dimension", self.dimension)

            logger.info("Loaded FAISS index from %s (%d vectors)", target_dir, self.total_vectors)
            return True
        except Exception as exc:
            logger.error("Failed to load FAISS index from %s: %s", target_dir, exc)
            return False

    def clear(self) -> None:
        """Reset the index and memory state."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.chunk_ids.clear()
        self.chunk_metadata.clear()
