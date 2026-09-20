"""Paper ingestion, parsing, chunking, and pipeline coordination package."""

from backend.ingestion.chunker import StructureAwareChunker
from backend.ingestion.models import DocumentChunk, IngestionResult, ParsedDocument, ParsedPage
from backend.ingestion.pdf_downloader import (
    InvalidPDFContentError,
    PDFDownloader,
    PDFDownloadError,
    PDFSizeLimitExceededError,
)
from backend.ingestion.pdf_parser import (
    CorruptPDFError,
    EncryptedPDFError,
    PDFParser,
    PDFParserError,
)
from backend.ingestion.pipeline import IngestionPipeline

__all__ = [
    "CorruptPDFError",
    "DocumentChunk",
    "EncryptedPDFError",
    "IngestionPipeline",
    "IngestionResult",
    "InvalidPDFContentError",
    "PDFDownloader",
    "PDFDownloadError",
    "PDFParser",
    "PDFParserError",
    "PDFSizeLimitExceededError",
    "ParsedDocument",
    "ParsedPage",
    "StructureAwareChunker",
]
