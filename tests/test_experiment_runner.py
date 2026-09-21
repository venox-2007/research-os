"""Unit tests for SafeExperimentRunner execution and telemetry."""

from pathlib import Path
from uuid import uuid4

import pytest

from backend.experiments.artifacts import ArtifactStore
from backend.experiments.datasets import DatasetRegistry
from backend.experiments.models import ExperimentSpec
from backend.experiments.registry import ExperimentRegistry
from backend.experiments.runner import SafeExperimentRunner


@pytest.mark.asyncio
async def test_safe_runner_successful_execution(tmp_path: Path) -> None:
    """Verify end-to-end execution of approved spec produces metrics and artifacts."""
    datasets = DatasetRegistry(base_dir=tmp_path / "datasets")
    artifacts = ArtifactStore(base_dir=tmp_path / "artifacts")
    registry = ExperimentRegistry()
    runner = SafeExperimentRunner(registry=registry, datasets=datasets, artifacts=artifacts)

    spec = ExperimentSpec(
        experiment_id=uuid4(),
        title="Regression Test Run",
        hypothesis="Features predict continuous target",
        objective="Assess R^2",
        function_name="linear_regression_benchmark",
        dataset_id="synthetic_regression",
        parameters={"alpha": 0.5},
        random_seed=42,
    )

    result = await runner.run(spec)
    assert result.status == "completed"
    assert len(result.metrics) >= 3
    assert "r2_score" in result.summary_metrics
    assert result.summary_metrics["r2_score"] > 0.8
    assert len(result.artifacts) >= 2

    # Verify run record in runner
    run_record = runner.get_run(result.run_id)
    assert run_record is not None
    assert run_record.status == "completed"
    assert run_record.duration_ms > 0


@pytest.mark.asyncio
async def test_safe_runner_missing_dataset(tmp_path: Path) -> None:
    """Verify runner fails gracefully when target dataset does not exist."""
    datasets = DatasetRegistry(base_dir=tmp_path / "datasets")
    runner = SafeExperimentRunner(datasets=datasets)

    spec = ExperimentSpec(
        experiment_id=uuid4(),
        title="Missing Dataset Probe",
        hypothesis="None",
        objective="None",
        function_name="linear_regression_benchmark",
        dataset_id="nonexistent_dataset",
    )

    result = await runner.run(spec)
    assert result.status == "failed"
    assert "not found" in result.provenance.get("error", "").lower()
