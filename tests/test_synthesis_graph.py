"""Unit tests for LangGraph stateful synthesis workflow."""

import pytest

from backend.core.models import Evidence, Source
from backend.synthesis.graph import build_synthesis_graph, run_synthesis
from backend.synthesis.models import ReportSpec


def test_build_synthesis_graph_compilation() -> None:
    graph = build_synthesis_graph()
    assert graph is not None


@pytest.mark.asyncio
async def test_run_synthesis_graph_execution() -> None:
    src = Source(
        title="Attention Is All You Need", authors=["Vaswani, A."], publication_date="2017"
    )
    ev = Evidence(
        source_id=src.id,
        content="The Transformer model architecture eschews recurrence and relies entirely on self-attention mechanisms.",
        section="1. Introduction",
        page_number=2,
    )
    spec = ReportSpec(question="How do transformer architectures handle sequences?")

    result = await run_synthesis(
        spec=spec,
        verified_evidence=[ev],
        sources=[src],
        max_revisions=2,
    )

    assert result.report_id is not None
    assert result.validation.is_valid is True
    assert len(result.claims) >= 1
    assert len(result.sections) >= 4
    assert len(result.artifacts) >= 2
    assert "## Abstract" in result.report_markdown
    assert "## References" in result.report_markdown
