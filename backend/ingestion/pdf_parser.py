"""PyMuPDF-based page-level academic PDF extractor with scanned-page detection."""

from pathlib import Path
from uuid import UUID, uuid4

import pymupdf

from backend.core.logging import get_logger
from backend.ingestion.models import ParsedDocument, ParsedPage

logger = get_logger("ingestion.parser")


class PDFParserError(Exception):
    """Base exception for PDF parsing failures."""

    pass


class EncryptedPDFError(PDFParserError):
    """Raised when encountering a password-protected PDF."""

    pass


class CorruptPDFError(PDFParserError):
    """Raised when PDF syntax is corrupted or unreadable by PyMuPDF."""

    pass


class PDFParser:
    """Extracts structured, page-bounded text from academic PDF documents."""

    def __init__(self, min_scanned_threshold_chars: int = 40) -> None:
        self.scanned_threshold = min_scanned_threshold_chars

    def parse(
        self,
        file_path: Path | str,
        source_id: UUID | None = None,
        preferred_title: str | None = None,
    ) -> ParsedDocument:
        """Parse PDF file into a structured ParsedDocument with page boundaries preserved.

        Args:
            file_path: Path to the local PDF file.
            source_id: Optional UUID of the parent Source.
            preferred_title: Fallback title if PDF metadata lacks a clean title.

        Returns:
            ParsedDocument containing ordered ParsedPage entries.
        """
        path = Path(file_path)
        if not path.exists():
            raise PDFParserError(f"PDF file not found at: {path}")

        linked_source_id = source_id or uuid4()
        doc_id = f"doc_{path.stem}"

        try:
            doc = pymupdf.open(str(path))
        except Exception as exc:
            logger.error("Failed to open PDF %s: %s", path.name, exc)
            raise CorruptPDFError(f"Corrupt or invalid PDF file: {exc}") from exc

        try:
            if doc.is_encrypted:
                logger.warning("PDF %s is encrypted / password-protected", path.name)
                raise EncryptedPDFError(f"Cannot parse encrypted PDF '{path.name}'")

            metadata = doc.metadata or {}
            raw_title = metadata.get("title", "")
            title = (
                raw_title.strip()
                if raw_title and len(raw_title.strip()) > 3
                else (preferred_title or path.stem)
            )

            total_pages = len(doc)
            parsed_pages: list[ParsedPage] = []
            scanned_pages_count = 0
            empty_pages_count = 0

            for idx, page in enumerate(doc):
                page_number = idx + 1
                try:
                    text = page.get_text("text").strip()
                except Exception as exc:
                    logger.warning(
                        "Error on page %d of %s: %s",
                        page_number,
                        path.name,
                        exc,
                    )
                    text = ""

                char_count = len(text)
                is_blank = char_count == 0

                # Scanned detection: negligible text despite having images
                has_images = bool(page.get_images())
                is_scanned = char_count < self.scanned_threshold and has_images

                if is_scanned:
                    scanned_pages_count += 1
                elif is_blank:
                    empty_pages_count += 1

                parsed_pages.append(
                    ParsedPage(
                        page_number=page_number,
                        text=text,
                        char_count=char_count,
                        is_blank=is_blank,
                        is_scanned=is_scanned,
                    )
                )

            # Determine extraction status
            if total_pages == 0:
                status = "failed"
            elif scanned_pages_count == total_pages:
                status = "scanned_only"
            elif scanned_pages_count > 0 or empty_pages_count > (total_pages // 2):
                status = "partial"
            else:
                status = "success"

            logger.info(
                "Parsed %s: %d pages (status: %s, scanned: %d, empty: %d)",
                path.name,
                total_pages,
                status,
                scanned_pages_count,
                empty_pages_count,
            )

            return ParsedDocument(
                document_id=doc_id,
                source_id=linked_source_id,
                title=title,
                total_pages=total_pages,
                pages=parsed_pages,
                metadata={
                    "author": metadata.get("author"),
                    "creator": metadata.get("creator"),
                    "producer": metadata.get("producer"),
                    "creationDate": metadata.get("creationDate"),
                    "format": metadata.get("format"),
                    "file_size_bytes": path.stat().st_size,
                },
                extraction_status=status,
            )

        finally:
            doc.close()
