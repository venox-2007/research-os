"""Data models for document parsing, structure detection, and chunking."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from backend.core.models import Source


class ParsedPage(BaseModel):
    """Structured text and diagnostic status for an individual document page."""

    page_number: int = Field(..., description="1-indexed physical page number")
    text: str = Field(default="", description="Extracted textual content from page")
    char_count: int = Field(default=0, description="Total characters extracted")
    is_blank: bool = Field(
        default=False, description="Whether the page contains zero readable text"
    )
    is_scanned: bool = Field(
        default=False,
        description="Whether page appears to be an image/scan with negligible text",
    )


class ParsedDocument(BaseModel):
    """Structured representation of an extracted academic paper."""

    document_id: str = Field(..., description="Unique deterministic identifier for document")
    source_id: UUID = Field(..., description="Linked Source UUID")
    title: str = Field(..., description="Extracted or matched title")
    total_pages: int = Field(default=0, description="Total page count")
    pages: list[ParsedPage] = Field(default_factory=list, description="Ordered pages")
    metadata: dict = Field(default_factory=dict, description="Extracted PDF metadata")
    extraction_status: str = Field(
        default="success",
        description="Status: success, partial, scanned_only, failed",
    )

    @property
    def full_text(self) -> str:
        """Combine readable text across all pages separated by double newlines."""
        return "\n\n".join(p.text for p in self.pages if not p.is_blank)


class DocumentChunk(BaseModel):
    """Structure-aware semantic chunk ready for RAG indexing and citation tracking."""

    chunk_id: str = Field(..., description="Unique deterministic chunk ID")
    document_id: str = Field(..., description="Parent document ID")
    source_id: UUID = Field(..., description="Origin Source UUID")
    section: str | None = Field(default=None, description="Academic section title if identified")
    start_page: int = Field(..., description="Starting 1-indexed page number")
    end_page: int = Field(..., description="Ending 1-indexed page number")
    text: str = Field(..., description="Chunk content")
    char_count: int = Field(..., description="Character count")
    estimated_tokens: int = Field(..., description="Estimated token count (~4 chars/token)")
    metadata: dict = Field(default_factory=dict, description="Contextual chunk metadata")


class IngestionResult(BaseModel):
    """Deliverable output of the complete ingestion pipeline."""

    source: Source = Field(..., description="Normalized source information")
    document: ParsedDocument = Field(..., description="Extracted page-level document")
    chunks: list[DocumentChunk] = Field(default_factory=list, description="Assembled chunks")
    pdf_path: str | None = Field(default=None, description="Local cached PDF file path")
    cached: bool = Field(default=False, description="Whether paper was loaded from existing cache")
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when ingestion concluded",
    )
