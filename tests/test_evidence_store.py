"""Unit tests for SQLiteEvidenceStore."""

from pathlib import Path
from uuid import uuid4

from backend.core.models import Evidence
from backend.evidence.store import SQLiteEvidenceStore


def test_evidence_store_crud(tmp_path: Path):
    db_path = tmp_path / "test_evidence.db"
    store = SQLiteEvidenceStore(db_path=db_path)

    source_id = uuid4()
    evidence1 = Evidence(
        chunk_id="chunk-abc-1",
        source_id=source_id,
        source_title="Transformer Paper",
        content="Self-attention allows parallelization across sequence tokens.",
        confidence_score=0.92,
        section="Architecture",
        page_numbers=[1, 2],
        provenance_summary="Transformer Paper (pp. 1-2, Architecture)",
    )
    evidence2 = Evidence(
        chunk_id="chunk-abc-2",
        source_id=source_id,
        source_title="Transformer Paper",
        content="Positional encodings provide sequence order information.",
        confidence_score=0.75,
        section="Architecture",
        page_numbers=[3],
        provenance_summary="Transformer Paper (p. 3, Architecture)",
    )

    # Insert batch
    saved_ids = store.save_evidence_batch([evidence1, evidence2])
    assert len(saved_ids) == 2
    assert store.count == 2

    # Get by ID
    retrieved = store.get_evidence(evidence1.id)
    assert retrieved is not None
    assert retrieved.chunk_id == "chunk-abc-1"
    assert retrieved.confidence_score == 0.92
    assert retrieved.page_numbers == [1, 2]
    assert retrieved.source_title == "Transformer Paper"

    # Query all
    all_ev = store.query_evidence()
    assert len(all_ev) == 2

    # Query with confidence filter
    high_conf = store.query_evidence(min_confidence=0.8)
    assert len(high_conf) == 1
    assert high_conf[0].chunk_id == "chunk-abc-1"

    # Query by source_id
    by_src = store.query_evidence(source_id=source_id)
    assert len(by_src) == 2

    # Query with unknown source_id
    unknown = store.query_evidence(source_id=uuid4())
    assert len(unknown) == 0


def test_evidence_store_upsert(tmp_path: Path):
    db_path = tmp_path / "test_upsert.db"
    store = SQLiteEvidenceStore(db_path=db_path)

    ev1 = Evidence(
        chunk_id="same-chunk",
        content="Original content",
        confidence_score=0.5,
    )
    store.save_evidence(ev1)
    assert store.count == 1

    # Upsert with higher score and new content
    ev2 = Evidence(
        chunk_id="same-chunk",
        content="Updated content",
        confidence_score=0.95,
    )
    store.save_evidence(ev2)
    assert store.count == 1  # Count should not increase due to upsert

    saved = store.query_evidence()
    assert len(saved) == 1
    assert saved[0].content == "Updated content"
    assert saved[0].confidence_score == 0.95
