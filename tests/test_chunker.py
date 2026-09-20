"""Deterministic offline unit tests for the structure-aware chunker."""

from uuid import uuid4

from backend.ingestion.chunker import StructureAwareChunker
from backend.ingestion.models import ParsedDocument, ParsedPage


def test_chunker_section_detection_and_page_preservation() -> None:
    """Verify academic section headings are identified and page numbers tracked."""
    doc = ParsedDocument(
        document_id="doc_paper_1",
        source_id=uuid4(),
        title="Attention Is All You Need",
        total_pages=3,
        pages=[
            ParsedPage(
                page_number=1,
                text=(
                    "Abstract\n"
                    "Recurrent neural networks have been established as state of the art.\n\n"
                    "1 Introduction\n"
                    "Recurrent models typically factor computation along the symbol positions."
                ),
                char_count=180,
            ),
            ParsedPage(
                page_number=2,
                text=(
                    "2 Methodology\n"
                    "The Transformer relies entirely on self-attention mechanisms.\n\n"
                    "3 Experiments\n"
                    "We trained on the standard WMT 2014 English-German dataset."
                ),
                char_count=200,
            ),
            ParsedPage(
                page_number=3,
                text=(
                    "4 Conclusion\n"
                    "We presented the Transformer, a sequence model based on attention.\n\n"
                    "References\n"
                    "[1] Bahdanau, D., Cho, K., & Bengio, Y. (2014)."
                ),
                char_count=210,
            ),
        ],
    )

    chunker = StructureAwareChunker(target_chunk_chars=1000)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 5
    detected_sections = [c.section for c in chunks if c.section]
    assert "Abstract" in detected_sections
    assert "Introduction" in detected_sections
    assert "Methodology" in detected_sections
    assert "Conclusion" in detected_sections

    # Check page preservation
    abstract_chunk = next(c for c in chunks if c.section == "Abstract")
    assert abstract_chunk.start_page == 1
    assert abstract_chunk.end_page == 1
    assert "Recurrent neural networks" in abstract_chunk.text

    conclusion_chunk = next(c for c in chunks if c.section == "Conclusion")
    assert conclusion_chunk.start_page == 3
    assert conclusion_chunk.end_page == 3

    # Check deterministic chunk ID formatting
    assert chunks[0].chunk_id == "doc_paper_1_c001"
    assert chunks[1].chunk_id == "doc_paper_1_c002"


def test_chunker_fallback_for_papers_without_sections() -> None:
    """Verify papers without standard headings fallback to sliding-window chunks without error."""
    doc = ParsedDocument(
        document_id="doc_essay",
        source_id=uuid4(),
        title="Unstructured Essay",
        total_pages=2,
        pages=[
            ParsedPage(
                page_number=1,
                text="General discussion of artificial intelligence without section numbers.",
                char_count=80,
            ),
            ParsedPage(
                page_number=2,
                text="Empirical observations and final thoughts continued on the second page.",
                char_count=90,
            ),
        ],
    )

    chunker = StructureAwareChunker(target_chunk_chars=500)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 1
    # Section should be None since no academic headings were matched
    assert all(c.section is None for c in chunks)
    assert chunks[0].document_id == "doc_essay"
    assert chunks[0].start_page == 1


def test_chunker_large_section_split_with_overlap() -> None:
    """Verify long sections are divided into multiple chunks respecting target size."""
    long_paragraph = " ".join([f"Word{i}" for i in range(400)])  # ~2500 chars
    doc = ParsedDocument(
        document_id="doc_long",
        source_id=uuid4(),
        title="Long Section Document",
        total_pages=1,
        pages=[
            ParsedPage(
                page_number=1,
                text=f"1 Methodology\n{long_paragraph}",
                char_count=len(long_paragraph) + 15,
            )
        ],
    )

    chunker = StructureAwareChunker(target_chunk_chars=800, chunk_overlap_chars=100)
    chunks = chunker.chunk(doc)

    assert len(chunks) > 1
    assert all(c.section == "Methodology" for c in chunks)
    assert all(c.char_count <= 950 for c in chunks)
    assert all(c.start_page == 1 for c in chunks)
