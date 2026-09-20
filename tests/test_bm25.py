"""Unit tests for BM25Index."""

from pathlib import Path

from backend.rag.bm25 import BM25Index


def test_bm25_build_and_search():
    index = BM25Index()
    docs = [
        "Low-rank adaptation LoRA decomposes weight updates into rank r matrices.",
        "FlashAttention utilizes GPU SRAM tiling to minimize high bandwidth memory reads.",
        "Decoupled weight decay in AdamW optimizes learning rate schedules.",
    ]
    chunk_ids = ["c-lora", "c-flash", "c-adamw"]
    metadatas = [{"section": "Methods"}, {"section": "GPU"}, {"section": "Optimization"}]

    index.build(chunk_ids, docs, metadatas)
    assert index.count == 3

    # Exact keyword search
    results = index.search("LoRA adaptation rank matrices", top_k=2)
    assert len(results) >= 1
    assert results[0].chunk_id == "c-lora"
    assert results[0].score > 0.0
    assert results[0].rank == 1


def test_bm25_empty_query_or_index():
    index = BM25Index()
    assert index.search("anything") == []

    index.build(["c1"], ["Some text"], [{}])
    assert index.search("") == []
    assert index.search("   ") == []


def test_bm25_no_matches():
    index = BM25Index()
    index.build(["c1"], ["Quantum entanglement in optical lattices"], [{}])
    results = index.search("transformer attention mechanism")
    assert results == []


def test_bm25_persistence(tmp_path: Path):
    index = BM25Index()
    docs = ["Academic paper discussing transformer self-attention."]
    chunk_ids = ["c-trans"]
    index.build(chunk_ids, docs, [{"title": "Attention Paper"}])

    index.save(tmp_path)
    assert (tmp_path / "bm25_metadata.json").exists()

    loaded_index = BM25Index()
    success = loaded_index.load(tmp_path)
    assert success is True
    assert loaded_index.count == 1

    results = loaded_index.search("transformer attention", top_k=1)
    assert len(results) == 1
    assert results[0].chunk_id == "c-trans"
    assert results[0].metadata["title"] == "Attention Paper"
