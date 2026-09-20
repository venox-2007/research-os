"""Deterministic offline unit tests for the PyMuPDF PDF parser."""

from pathlib import Path

import pymupdf
import pytest

from backend.ingestion.pdf_parser import CorruptPDFError, PDFParser, PDFParserError


def create_synthetic_pdf(
    output_path: Path, num_pages: int = 3, include_blank: bool = False
) -> Path:
    """Generate a clean synthetic PDF file programmatically using PyMuPDF."""
    doc = pymupdf.open()

    for i in range(1, num_pages + 1):
        page = doc.new_page(width=595, height=842)  # A4
        if include_blank and i == 2:
            # Leave page 2 completely empty
            continue
        page.insert_text(
            point=(50, 72),
            text=f"Section {i} Heading\nParagraph content on page {i} of paper.",
            fontsize=12,
        )

    doc.save(str(output_path))
    doc.close()
    return output_path


def test_pdf_parser_multi_page_extraction(tmp_path: Path) -> None:
    """Verify multi-page PDF is parsed with page boundaries, text, and metadata preserved."""
    pdf_path = create_synthetic_pdf(tmp_path / "synthetic.pdf", num_pages=3)
    parser = PDFParser()
    doc = parser.parse(pdf_path, preferred_title="Synthetic Paper")

    assert doc.title == "Synthetic Paper"
    assert doc.total_pages == 3
    assert len(doc.pages) == 3
    assert doc.extraction_status == "success"

    # Verify page 1
    assert doc.pages[0].page_number == 1
    assert "Section 1 Heading" in doc.pages[0].text
    assert not doc.pages[0].is_blank
    assert not doc.pages[0].is_scanned

    # Verify page 3
    assert doc.pages[2].page_number == 3
    assert "page 3" in doc.pages[2].text


def test_pdf_parser_empty_page_handling(tmp_path: Path) -> None:
    """Verify empty pages are detected and marked is_blank=True."""
    pdf_path = create_synthetic_pdf(tmp_path / "with_blank.pdf", num_pages=3, include_blank=True)
    parser = PDFParser()
    doc = parser.parse(pdf_path)

    assert doc.pages[1].page_number == 2
    assert doc.pages[1].is_blank is True
    assert doc.pages[1].char_count == 0


def test_pdf_parser_corrupt_file(tmp_path: Path) -> None:
    """Verify corrupted PDF files trigger CorruptPDFError."""
    corrupt_file = tmp_path / "corrupted.pdf"
    corrupt_file.write_bytes(b"This is definitely not a valid PDF file structure")

    parser = PDFParser()
    with pytest.raises(CorruptPDFError):
        parser.parse(corrupt_file)


def test_pdf_parser_nonexistent_file() -> None:
    """Verify missing file raises PDFParserError."""
    parser = PDFParser()
    with pytest.raises(PDFParserError):
        parser.parse("non_existent_path_xyz.pdf")
