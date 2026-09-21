"""Unit tests for citation formatting and bibliography generation."""

from backend.core.models import Source
from backend.synthesis.citations import CitationFormatter, CitationManager


def test_format_apa_complete() -> None:
    src = Source(
        title="Attention Is All You Need",
        authors=["Vaswani, A.", "Shazeer, N."],
        publication_date="2017-06-12",
        url="https://arxiv.org/abs/1706.03762",
        metadata={"venue": "NeurIPS"},
    )
    formatted, is_complete = CitationFormatter.format_apa(src)
    assert is_complete is True
    assert "Vaswani, A. & Shazeer, N." in formatted
    assert "(2017)" in formatted
    assert "*Attention Is All You Need*" in formatted
    assert "*NeurIPS*" in formatted


def test_format_ieee_complete() -> None:
    src = Source(
        title="Attention Is All You Need",
        authors=["Vaswani, A.", "Shazeer, N."],
        publication_date="2017",
        metadata={"venue": "NeurIPS"},
    )
    formatted, is_complete = CitationFormatter.format_ieee(src, index=1)
    assert is_complete is True
    assert "[1] Vaswani, A., Shazeer, N." in formatted
    assert '"Attention Is All You Need"' in formatted
    assert "*NeurIPS*" in formatted
    assert "2017" in formatted


def test_missing_metadata_anti_hallucination() -> None:
    src = Source(
        title="Anonymous Manuscript",
        authors=[],  # Missing authors
        publication_date=None,  # Missing date
    )
    formatted_apa, complete_apa = CitationFormatter.format_apa(src)
    assert complete_apa is False
    assert "[Author Unknown]" in formatted_apa
    assert "(n.d.)" in formatted_apa

    formatted_ieee, complete_ieee = CitationFormatter.format_ieee(src, index=2)
    assert complete_ieee is False
    assert "[2] [Author Unknown]" in formatted_ieee
    assert "n.d." in formatted_ieee


def test_citation_manager_registration_and_rendering() -> None:
    mgr = CitationManager(style="ieee")
    src1 = Source(title="Paper One", authors=["Alice, A."], publication_date="2021")
    src2 = Source(title="Paper Two", authors=["Bob, B."], publication_date="2022")

    ref1 = mgr.register_source(src1)
    ref2 = mgr.register_source(src2)

    assert ref1.key == "[1]"
    assert ref2.key == "[2]"

    # Duplicate registration returns existing reference
    ref1_again = mgr.register_source(src1)
    assert ref1_again.key == "[1]"

    md = mgr.render_references_markdown()
    assert "## References" in md
    assert "[1] Alice, A." in md
    assert "[2] Bob, B." in md
