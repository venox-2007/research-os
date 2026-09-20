"""Unit tests for FAISSVectorStore."""

from pathlib import Path

import pytest

from backend.rag.embeddings import LocalEmbedder
from backend.rag.vector_store import FAISSVectorStore


def test_faiss_add_and_search():
    store = FAISSVectorStore(dimension=384)
    embedder = LocalEmbedder(mock_mode=True)

    texts = [
        "First document about neural language models.",
        "Second document about stochastic gradient descent.",
        "Third document about sparse retrieval methods.",
    ]
    chunk_ids = ["doc-1", "doc-2", "doc-3"]
    metadatas = [{"title": "Doc 1"}, {"title": "Doc 2"}, {"title": "Doc 3"}]
    embeddings = embedder.embed_texts(texts)

    store.add_embeddings(embeddings, chunk_ids, texts, metadatas)
    assert store.count == 3

    # Query with the exact first text
    q_vec = embedder.embed_query("First document about neural language models.")
    results = store.search(q_vec, top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "doc-1"
    assert results[0].score >= results[1].score
    assert results[0].rank == 1
    assert results[1].rank == 2


def test_faiss_empty_store():
    store = FAISSVectorStore(dimension=384)
    q_vec = [0.1] * 384
    results = store.search(q_vec, top_k=5)
    assert results == []


def test_faiss_persistence(tmp_path: Path):
    store = FAISSVectorStore(dimension=384)
    embedder = LocalEmbedder(mock_mode=True)

    texts = ["Test document persistence in FAISS index."]
    chunk_ids = ["persist-1"]
    embeddings = embedder.embed_texts(texts)

    store.add_embeddings(embeddings, chunk_ids, texts, [{"source": "test"}])
    assert store.count == 1

    # Save to disk
    store.save(tmp_path)
    assert (tmp_path / "faiss.index").exists()
    assert (tmp_path / "faiss_metadata.json").exists()

    # Reload into a fresh instance
    loaded_store = FAISSVectorStore(dimension=384)
    loaded = loaded_store.load(tmp_path)
    assert loaded is True
    assert loaded_store.count == 1

    # Search in loaded store
    q_vec = embedder.embed_query("Test document persistence in FAISS index.")
    results = loaded_store.search(q_vec, top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "persist-1"
    assert results[0].metadata["source"] == "test"


def test_faiss_invalid_dimension():
    store = FAISSVectorStore(dimension=384)
    with pytest.raises(ValueError, match="Dimension mismatch"):
        store.add_embeddings([[0.1, 0.2]], ["bad-dim"], ["text"])
