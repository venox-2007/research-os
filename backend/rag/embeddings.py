"""Local sentence-transformers embedding engine with batching and normalization."""

from functools import lru_cache

import numpy as np

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger("rag.embeddings")


class EmbeddingError(Exception):
    """Base exception for embedding failures."""

    pass


class LocalEmbedder:
    """Zero-cost local embedding generator utilizing sentence-transformers."""

    def __init__(
        self,
        model_name: str | None = None,
        device: str | None = None,
        batch_size: int = 32,
        mock_mode: bool | None = None,
    ) -> None:
        self.settings = get_settings()
        self.model_name = model_name or self.settings.embedding_model
        self.device = device or self.settings.device
        self.batch_size = batch_size
        self.mock_mode = (
            mock_mode
            if mock_mode is not None
            else (self.settings.app_env == "testing" or self.settings.llm_provider == "mock")
        )
        self._model = None

        # Resolve device
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
        """Load sentence-transformers model onto resolved device."""
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(
                "Loading embedding model '%s' onto device '%s'...", self.model_name, self.device
            )
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Embedding model '%s' loaded successfully", self.model_name)
        except Exception as exc:
            logger.warning(
                "Could not load SentenceTransformer ('%s'): %s. Falling back to deterministic mock embedding mode.",
                self.model_name,
                exc,
            )
            self.mock_mode = True

    def embed_query(self, query: str) -> np.ndarray:
        """Encode a single query string into a 1D normalized float32 vector."""
        clean_query = query.strip()
        if not clean_query:
            raise EmbeddingError("Cannot embed empty query string")

        matrix = self.embed_documents([clean_query])
        return matrix[0]

    def embed_text(self, text: str) -> np.ndarray:
        """Encode a single text passage into a 1D normalized float32 vector."""
        return self.embed_query(text)

    def embed_texts(self, texts: list[str], batch_size: int | None = None) -> list[np.ndarray]:
        """Encode a list of text passages into a list of normalized vectors."""
        if not texts:
            return []
        arr = self.embed_documents(texts, batch_size=batch_size)
        return [arr[i] for i in range(len(arr))]

    def embed_documents(self, texts: list[str], batch_size: int | None = None) -> np.ndarray:
        """Encode a list of text passages into a 2D normalized float32 array.

        Args:
            texts: List of text passages to embed.
            batch_size: Optional override for batch size.

        Returns:
            np.ndarray of shape (len(texts), embedding_dim) with unit L2 norm.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        bs = batch_size or self.batch_size

        if self.mock_mode or self.model_name == "mock":
            return self._generate_mock_embeddings(texts)

        try:
            embeddings = self._model.encode(
                texts,
                batch_size=bs,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            return embeddings.astype(np.float32)
        except Exception as exc:
            logger.error("Embedding generation failed: %s", exc)
            raise EmbeddingError(f"Embedding failed: {exc}") from exc

    def _generate_mock_embeddings(self, texts: list[str], dim: int = 384) -> np.ndarray:
        """Generate deterministic normalized pseudo-embeddings for tests and offline fallback."""
        vectors = []
        for text in texts:
            # Deterministic seed from text
            seed = hash(text.strip().lower()) % (2**32)
            rng = np.random.default_rng(seed)
            vec = rng.standard_normal(dim).astype(np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.vstack(vectors)

    @property
    def dimension(self) -> int:
        """Return the vector dimensionality."""
        if self._model is not None and hasattr(self._model, "get_sentence_embedding_dimension"):
            return self._model.get_sentence_embedding_dimension()
        return 384


@lru_cache(maxsize=1)
def get_embedder(model_name: str | None = None, mock_mode: bool | None = None) -> LocalEmbedder:
    """Singleton getter for LocalEmbedder avoiding redundant model initialization."""
    settings = get_settings()
    name = model_name or settings.embedding_model
    return LocalEmbedder(model_name=name, mock_mode=mock_mode)
