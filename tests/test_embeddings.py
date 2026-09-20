"""Unit tests for LocalEmbedder and embedding generation."""

import numpy as np
import pytest

from backend.rag.embeddings import LocalEmbedder, get_embedder


def test_mock_embedder_dimension():
    embedder = LocalEmbedder(mock_mode=True)
    assert embedder.dimension == 384
    assert embedder.device == "cpu"


def test_mock_embed_single_text():
    embedder = LocalEmbedder(mock_mode=True)
    vector = embedder.embed_text("Self-attention enables parallel sequence processing.")
    assert len(vector) == 384
    # Check L2 normalization: norm should be approximately 1.0
    norm = np.linalg.norm(vector)
    assert pytest.approx(norm, rel=1e-3) == 1.0


def test_mock_embed_multiple_texts():
    embedder = LocalEmbedder(mock_mode=True)
    texts = [
        "First academic chunk on LoRA fine-tuning.",
        "Second chunk explaining FlashAttention memory tiling.",
        "Third chunk on BM25 probabilistic relevance scoring.",
    ]
    vectors = embedder.embed_texts(texts, batch_size=2)
    assert len(vectors) == 3
    for vec in vectors:
        assert len(vec) == 384
        assert pytest.approx(np.linalg.norm(vec), rel=1e-3) == 1.0


def test_mock_embed_empty_list():
    embedder = LocalEmbedder(mock_mode=True)
    vectors = embedder.embed_texts([])
    assert vectors == []


def test_mock_embed_query():
    embedder = LocalEmbedder(mock_mode=True)
    vec = embedder.embed_query("Query about transformers")
    assert len(vec) == 384
    assert pytest.approx(np.linalg.norm(vec), rel=1e-3) == 1.0


def test_deterministic_mock_embeddings():
    embedder = LocalEmbedder(mock_mode=True)
    vec1 = embedder.embed_text("Deterministic academic text")
    vec2 = embedder.embed_text("Deterministic academic text")
    assert np.allclose(vec1, vec2)

    vec_diff = embedder.embed_text("Completely different academic text")
    assert not np.allclose(vec1, vec_diff)


def test_get_embedder_cached_singleton():
    emb1 = get_embedder("all-MiniLM-L6-v2", mock_mode=True)
    emb2 = get_embedder("all-MiniLM-L6-v2", mock_mode=True)
    assert emb1 is emb2
