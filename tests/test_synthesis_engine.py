"""Unit tests for SynthesisEngine end-to-end report generation."""

import pytest

from backend.core.models import Evidence, Source
from backend.synthesis.engine import SynthesisEngine
from backend.synthesis.models import ReportSpec


@pytest.mark.asyncio
async def test_synthesis_engine_end_to_end() -> None:
    engine = SynthesisEngine(max_revisions=2)
    src = Source(
        title="Attention Is All You Need",
        authors=["Vaswani, A."],
        publication_date="2017",
        url="https://arxiv.org/abs/1706.03762",
    )
    ev = Evidence(
        source_id=src.id,
        content="The Transformer model architecture eschews recurrence and relies entirely on self-attention mechanisms.",
        section="1. Introduction",
        page_number=2,
    )
    spec = ReportSpec(
        question="How do self-attention mechanisms operate without recurrence?",
        discipline="Computer Science",
    )

    result = await engine.synthesize(
        spec=spec,
        verified_evidence=[ev],
        sources=[src],
    )

    assert result.report_id is not None
    assert result.validation.is_valid is True
    assert result.validation.validation_status in ["PASSED", "WARNING"]
    assert len(result.claims) >= 1
    assert len(result.sections) >= 4  # Abstract, Intro, Related Work, Conclusion, References
    assert "## Abstract" in result.report_markdown
    assert "## References" in result.report_markdown
    assert "[1]" in result.report_markdown
    assert len(result.artifacts) >= 2  # report.md and report.json


@pytest.mark.asyncio
async def test_synthesis_engine_with_experiments() -> None:
    engine = SynthesisEngine()
    src = Source(title="Linear Models", authors=["Author, L."])
    ev = Evidence(source_id=src.id, content="Linear models provide baseline interpretability.")
    spec = ReportSpec(
        question="Benchmark evaluation of regression models",
        include_experiments=True,
    )
    exp_run = {
        "id": "11111111-1111-1111-1111-111111111111",
        "run_id": "11111111-1111-1111-1111-111111111111",
        "spec": {"target_routine": "linear_regression_benchmark"},
        "status": "completed",
        "metrics": {"mse": 0.042, "r2_score": 0.958},
    }

    result = await engine.synthesize(
        spec=spec,
        verified_evidence=[ev],
        sources=[src],
        experiment_results=[exp_run],
    )

    assert any(c.origin == "experiment" for c in result.claims)
    assert any("Empirical Experiments" in s.title for s in result.sections)
    assert result.validation.is_valid is True


@pytest.mark.asyncio
async def test_synthesis_engine_no_experiments_omits_experiment_section() -> None:
    engine = SynthesisEngine()
    src = Source(title="Theory Paper", authors=["Theorist, T."])
    ev = Evidence(
        source_id=src.id, content="Theoretical complexity analysis confirms upper bounds."
    )
    spec = ReportSpec(
        question="Theoretical complexity analysis",
        include_experiments=False,
    )

    result = await engine.synthesize(
        spec=spec,
        verified_evidence=[ev],
        sources=[src],
        experiment_results=[],
    )

    # Must NOT fabricate empirical results section when no experiments performed
    assert not any("Empirical Experiments" in s.title for s in result.sections)
    assert result.validation.is_valid is True
