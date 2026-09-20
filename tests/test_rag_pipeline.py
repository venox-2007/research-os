"""Integration tests for RAGPipeline and RAGIndexer."""

import json
from pathlib import Path
from uuid import uuid4

import pytest

from backend.core.config import Settings
from backend.rag.indexer import RAGIndexer
from backend.rag.pipeline import RAGPipeline


@pytest.fixture
def rag_pipeline_env(tmp_path: Path) -> tuple[Settings, RAGPipeline, RAGIndexer]:
    settings = Settings(
        data_dir=tmp_path / "data",
        cache_dir=tmp_path / "cache",
        experiments_dir=tmp_path / "experiments",
    )
    settings.ensure_directories()

    # Create dummy chunks in data/chunks/
    source_id = uuid4()
    chunks_data = [
        {
            "chunk_id": "chunk-101",
            "document_id": "doc-test-1",
            "source_id": str(source_id),
            "text": "LoRA freezes foundation model parameters and inserts trainable low rank matrices.",
            "section": "Methods",
            "start_page": 2,
            "end_page": 2,
            "char_count": 82,
            "estimated_tokens": 18,
            "metadata": {"paper_title": "LoRA Paper"},
        },
        {
            "chunk_id": "chunk-102",
            "document_id": "doc-test-1",
            "source_id": str(source_id),
            "text": "FlashAttention uses GPU on-chip SRAM tiling to compute attention with linear memory I/O.",
            "section": "Architecture",
            "start_page": 3,
            "end_page": 4,
            "char_count": 88,
            "estimated_tokens": 19,
            "metadata": {"paper_title": "FlashAttention Paper"},
        },
    ]

    for c in chunks_data:
        chunk_file = settings.chunks_dir / f"{c['chunk_id']}.json"
        chunk_file.write_text(json.dumps(c), encoding="utf-8")

    pipeline = RAGPipeline(settings=settings, mock_mode=True)
    indexer = RAGIndexer(settings=settings, pipeline=pipeline)
    return settings, pipeline, indexer


def test_indexer_and_pipeline_search(rag_pipeline_env):
    settings, pipeline, indexer = rag_pipeline_env

    # Run indexing
    stats = indexer.index_all()
    assert stats["indexed_chunks"] == 2
    assert stats["dense_index_size"] == 2
    assert stats["bm25_index_size"] == 2

    # Query RAG pipeline
    result = pipeline.query("LoRA low rank matrices", top_k=2)
    assert len(result.results) >= 1
    top_candidate = result.results[0]
    assert top_candidate.chunk_id == "chunk-101"
    assert top_candidate.section == "Methods"
    assert top_candidate.start_page == 2
    assert top_candidate.end_page == 2

    # Diagnostics verification
    assert result.diagnostics.fused_candidates_count >= 1
    assert result.diagnostics.total_time_ms >= 0.0

    # Verify evidence was saved to evidence store
    evidence_items = pipeline.evidence_store.query_evidence()
    assert len(evidence_items) >= 1
    assert any(e.chunk_id == "chunk-101" for e in evidence_items)


def test_incremental_indexing(rag_pipeline_env):
    settings, pipeline, indexer = rag_pipeline_env

    stats1 = indexer.index_all()
    assert stats1["indexed_chunks"] == 2

    # Running index_incremental without new files should index 0 chunks
    stats2 = indexer.index_incremental()
    assert stats2["indexed_chunks"] == 0

    # Add a 3rd chunk
    new_chunk = {
        "chunk_id": "chunk-103",
        "document_id": "doc-test-1",
        "source_id": str(uuid4()),
        "text": "Direct Preference Optimization removes the need for reinforcement learning in alignment.",
        "section": "Introduction",
        "start_page": 1,
        "end_page": 1,
        "char_count": 89,
        "estimated_tokens": 14,
        "metadata": {},
    }
    (settings.chunks_dir / "chunk-103.json").write_text(json.dumps(new_chunk), encoding="utf-8")

    stats3 = indexer.index_incremental()
    assert stats3["indexed_chunks"] == 1
    assert stats3["dense_index_size"] == 3
