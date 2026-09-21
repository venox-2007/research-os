"""Unit tests for ExperimentPlanner task translation and catalog validation."""

import pytest

from backend.experiments.planner import ExperimentPlanner


@pytest.mark.asyncio
async def test_planner_formulates_retrieval_spec() -> None:
    """Verify planner maps IR task to ranking_evaluation."""
    planner = ExperimentPlanner()
    spec = await planner.plan_experiment(
        task_title="Evaluate hybrid RAG vs BM25 ranking precision and MRR",
        hypothesis="Hybrid fusion yields superior MRR on benchmark queries.",
    )
    assert spec.function_name == "ranking_evaluation"
    assert spec.dataset_id == "synthetic_retrieval"
    assert spec.is_executable is True
    assert "mrr" in spec.metrics_to_evaluate


@pytest.mark.asyncio
async def test_planner_formulates_classification_spec() -> None:
    """Verify planner maps classification task to classification_eval."""
    planner = ExperimentPlanner()
    spec = await planner.plan_experiment(
        task_title="Train model to detect and classify anomalous instances",
        hypothesis="Regularized classifier achieves F1 > 0.8.",
    )
    assert spec.function_name == "classification_eval"
    assert spec.dataset_id == "synthetic_classification"
    assert spec.is_executable is True
    assert "f1_score" in spec.metrics_to_evaluate


@pytest.mark.asyncio
async def test_planner_formulates_ablation_spec() -> None:
    """Verify planner maps sensitivity task to ablation_parameter_sweep."""
    planner = ExperimentPlanner()
    spec = await planner.plan_experiment(
        task_title="Perform regularization sensitivity sweep and parameter tuning",
    )
    assert spec.function_name == "ablation_parameter_sweep"
    assert spec.is_executable is True
