"""Tests for core domain Pydantic models."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.core.models import (
    Citation,
    Evidence,
    Experiment,
    ResearchPlan,
    ResearchQuestion,
    ResearchResult,
    ResearchTask,
    Source,
)


def test_research_question_creation_and_validation() -> None:
    """Verify ResearchQuestion validation rules."""
    q = ResearchQuestion(
        query="What are the scaling laws for small language models under 3B parameters?",
        discipline="Machine Learning",
        constraints=["focus on post-2023 papers", "evaluate reasoning tasks"],
    )
    assert q.id is not None
    assert q.status == "submitted"
    assert len(q.constraints) == 2
    assert q.discipline == "Machine Learning"

    # Verify min_length constraint
    with pytest.raises(ValidationError):
        ResearchQuestion(query="a")


def test_source_model() -> None:
    """Verify Source model serialization and fields."""
    s = Source(
        title="Attention Is All You Need",
        authors=["Vaswani et al."],
        publication_date="2017",
        url="https://arxiv.org/abs/1706.03762",
        source_type="arxiv",
    )
    assert s.title == "Attention Is All You Need"
    assert s.authors == ["Vaswani et al."]
    data = s.model_dump()
    assert data["source_type"] == "arxiv"
    reconstructed = Source.model_validate(data)
    assert reconstructed.id == s.id


def test_evidence_model() -> None:
    """Verify Evidence model linking to Source with confidence score."""
    source_id = uuid4()
    ev = Evidence(
        source_id=source_id,
        content=(
            "The dominant sequence transduction models are based on "
            "complex recurrent or convolutional networks."
        ),
        section="1 Introduction",
        page_number=1,
        confidence_score=0.95,
    )
    assert ev.source_id == source_id
    assert ev.confidence_score == 0.95

    # Invalid confidence score out of range
    with pytest.raises(ValidationError):
        Evidence(source_id=source_id, content="test", confidence_score=1.5)


def test_citation_model() -> None:
    """Verify Citation model links and verification flag."""
    source_id = uuid4()
    evidence_id = uuid4()
    cit = Citation(
        source_id=source_id,
        evidence_id=evidence_id,
        inline_marker="[1]",
        formatted_citation="Vaswani, A. et al. (2017). Attention Is All You Need. NeurIPS.",
        verified=True,
    )
    assert cit.verified is True
    assert cit.inline_marker == "[1]"


def test_research_task_and_plan() -> None:
    """Verify ResearchPlan with nested tasks."""
    question_id = uuid4()
    plan = ResearchPlan(
        question_id=question_id,
        objectives=["Review literature", "Run validation benchmark"],
    )
    task1 = ResearchTask(
        plan_id=plan.id,
        title="Search arXiv for 3B parameter benchmarks",
        task_type="literature_search",
    )
    plan.tasks.append(task1)
    assert len(plan.tasks) == 1
    assert plan.tasks[0].task_type == "literature_search"


def test_experiment_model() -> None:
    """Verify Experiment model structure and metrics tracking."""
    q_id = uuid4()
    exp = Experiment(
        question_id=q_id,
        title="Perplexity Benchmark",
        hypothesis="Model quantization from fp16 to int4 reduces perplexity by less than 5%",
        code="print('running quantization benchmark')",
        metrics={"perplexity_fp16": 12.4, "perplexity_int4": 12.8},
    )
    assert exp.status == "pending"
    assert exp.metrics["perplexity_int4"] == 12.8


def test_research_result_model() -> None:
    """Verify final synthesized ResearchResult model."""
    q_id = uuid4()
    res = ResearchResult(
        question_id=q_id,
        title="Synthesis: 3B SLM Scaling Laws",
        summary=(
            "Smaller models show superior inference-time scaling when trained on "
            "curated synthetic data."
        ),
        findings=[
            "Data quality exceeds model scale below 3B parameters",
            "Quantization impact is minimal on MMLU",
        ],
        report_markdown="# Comprehensive Analysis\n...",
    )
    assert len(res.findings) == 2
    assert res.title.startswith("Synthesis")
