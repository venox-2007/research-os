"""Persistent, traceable SQLite evidence repository linking claims back to source coordinates."""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Evidence

logger = get_logger("evidence.store")


class CallableInt(int):
    """Integer that can also be called like a method for backward compatibility."""

    def __call__(self) -> int:
        return int(self)


class SQLiteEvidenceStore:
    """Zero-cost local SQLite evidence repository for full citation provenance."""

    def __init__(self, db_path: Path | str | None = None, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.db_path = Path(db_path) if db_path else self.settings.evidence_db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a connection with row factory enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=15.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Initialize evidence table schema if not already present."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence (
                    id TEXT PRIMARY KEY,
                    source_id TEXT,
                    chunk_id TEXT,
                    source_title TEXT,
                    content TEXT NOT NULL,
                    section TEXT,
                    start_page INTEGER,
                    end_page INTEGER,
                    confidence_score REAL DEFAULT 1.0,
                    extraction_method TEXT DEFAULT 'hybrid_rag',
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_source ON evidence (source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_ev_chunk ON evidence (chunk_id)")
            conn.commit()

    def add_evidence(
        self,
        source_id: UUID | str | None = None,
        content: str = "",
        chunk_id: str | None = None,
        source_title: str | None = None,
        section: str | None = None,
        page_number: int | None = None,
        end_page: int | None = None,
        confidence_score: float = 1.0,
        extraction_method: str = "hybrid_rag",
        evidence_id: UUID | None = None,
    ) -> Evidence:
        """Record a verified evidence excerpt into the store.

        Returns:
            Normalized Evidence domain object.
        """
        eid = evidence_id or uuid4()
        sid = UUID(str(source_id)) if source_id else None
        now_iso = datetime.now(UTC).isoformat()

        clean_content = content.strip()
        if not clean_content:
            raise ValueError("Evidence content cannot be empty")

        with self._get_connection() as conn:
            # If chunk_id exists, check if already present to deduplicate/upsert
            if chunk_id:
                existing = conn.execute(
                    "SELECT id FROM evidence WHERE chunk_id = ?", (chunk_id,)
                ).fetchone()
                if existing:
                    eid = UUID(existing["id"])

            conn.execute(
                """
                INSERT OR REPLACE INTO evidence (
                    id, source_id, chunk_id, source_title, content,
                    section, start_page, end_page, confidence_score,
                    extraction_method, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(eid),
                    str(sid) if sid else None,
                    chunk_id,
                    source_title,
                    clean_content,
                    section,
                    page_number,
                    end_page or page_number,
                    float(confidence_score),
                    extraction_method,
                    now_iso,
                ),
            )
            conn.commit()

        logger.info(
            "Saved evidence %s for chunk %s (source %s)",
            str(eid)[:8],
            chunk_id,
            str(sid)[:8] if sid else "None",
        )

        page_nums = []
        if page_number is not None:
            if end_page is not None and end_page > page_number:
                page_nums = list(range(page_number, end_page + 1))
            else:
                page_nums = [page_number]

        return Evidence(
            id=eid,
            source_id=sid,
            chunk_id=chunk_id,
            source_title=source_title,
            content=clean_content,
            section=section,
            page_number=page_number,
            page_numbers=page_nums,
            confidence_score=confidence_score,
            extraction_method=extraction_method,
        )

    def save_evidence(self, evidence: Evidence) -> UUID:
        """Save or update an Evidence domain object."""
        start_page = evidence.page_number
        end_page = None
        if evidence.page_numbers:
            start_page = evidence.page_numbers[0]
            end_page = evidence.page_numbers[-1]
        ev = self.add_evidence(
            source_id=evidence.source_id,
            content=evidence.content,
            chunk_id=evidence.chunk_id,
            source_title=evidence.source_title,
            section=evidence.section,
            page_number=start_page,
            end_page=end_page,
            confidence_score=evidence.confidence_score,
            extraction_method=evidence.extraction_method,
            evidence_id=evidence.id,
        )
        return ev.id

    def save_evidence_batch(self, batch: list[Evidence]) -> list[UUID]:
        """Save a batch of Evidence objects."""
        return [self.save_evidence(ev) for ev in batch]

    def query_evidence(
        self,
        source_id: UUID | str | None = None,
        min_confidence: float | None = None,
        limit: int = 100,
    ) -> list[Evidence]:
        """Query evidence with optional source_id and confidence filters."""
        query = "SELECT * FROM evidence WHERE 1=1"
        params: list[Any] = []
        if source_id is not None:
            query += " AND source_id = ?"
            params.append(str(source_id))
        if min_confidence is not None:
            query += " AND confidence_score >= ?"
            params.append(float(min_confidence))
        query += " ORDER BY confidence_score DESC, created_at DESC LIMIT ?"
        params.append(max(1, min(limit, 500)))

        with self._get_connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._row_to_evidence(r) for r in rows]

    def get_evidence(self, evidence_id: UUID | str) -> Evidence | None:
        """Fetch an individual evidence record by UUID."""
        str_id = str(evidence_id)
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM evidence WHERE id = ?", (str_id,)).fetchone()
            if not row:
                return None
            return self._row_to_evidence(row)

    def get_by_source(self, source_id: UUID | str) -> list[Evidence]:
        """Retrieve all evidence snippets associated with a specific paper Source."""
        return self.query_evidence(source_id=source_id)

    def get_by_chunk(self, chunk_id: str) -> list[Evidence]:
        """Retrieve evidence linked to a specific DocumentChunk."""
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM evidence WHERE chunk_id = ?", (chunk_id,)).fetchall()
            return [self._row_to_evidence(r) for r in rows]

    def list_all(self, limit: int = 100) -> list[Evidence]:
        """List recently recorded evidence items."""
        return self.query_evidence(limit=limit)

    @property
    def count(self) -> CallableInt:
        """Return total count of recorded evidence records."""
        with self._get_connection() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM evidence").fetchone()[0]
            return CallableInt(cnt)

    def clear(self) -> None:
        """Purge all records (primarily for testing)."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM evidence")
            conn.commit()

    def _row_to_evidence(self, row: sqlite3.Row) -> Evidence:
        """Convert SQLite database row into Evidence domain object."""
        start_p = row["start_page"]
        end_p = row["end_page"]
        page_nums = []
        if start_p is not None:
            if end_p is not None and end_p > start_p:
                page_nums = list(range(start_p, end_p + 1))
            else:
                page_nums = [start_p]

        return Evidence(
            id=UUID(row["id"]),
            source_id=UUID(row["source_id"]) if row["source_id"] else None,
            chunk_id=row["chunk_id"],
            source_title=row["source_title"],
            content=row["content"],
            section=row["section"],
            page_number=start_p,
            page_numbers=page_nums,
            confidence_score=float(row["confidence_score"]),
            extraction_method=row["extraction_method"],
        )
