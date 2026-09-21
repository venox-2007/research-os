"""Unit tests for experiment domain models and schemas."""

from uuid import uuid4

from backend.experiments.models import (
    Artifact,
    DatasetSpec,
    ExperimentResult,
    ExperimentSpec,
    MetricResult,
)


def test_metric_result_model() -> None:
    """Verify MetricResult model validation and serialization."""
    metric = MetricResult(
        name="accuracy",
        value=0.925,
        unit="ratio",
        split="test",
        confidence_interval=(0.90, 0.95),
        higher_is_better=True,
    )
    assert metric.name == "accuracy"
    assert metric.value == 0.925
    assert metric.confidence_interval == (0.90, 0.95)
    data = metric.model_dump(mode="json")
    assert data["higher_is_better"] is True


def test_artifact_model() -> None:
    """Verify Artifact model validation."""
    run_id = uuid4()
    art = Artifact(
        run_id=run_id,
        name="metrics.json",
        artifact_type="json",
        file_path="data/artifacts/run_1/metrics.json",
        file_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        size_bytes=1024,
        mime_type="application/json",
    )
    assert art.run_id == run_id
    assert art.size_bytes == 1024


def test_dataset_spec_model() -> None:
    """Verify DatasetSpec properties."""
    ds = DatasetSpec(
        dataset_id="test_ds",
        name="Test Dataset",
        version="1.0",
        file_path="test_ds.csv",
        file_hash="abc123hash",
        format="csv",
        row_count=100,
        feature_columns=["f1", "f2"],
        target_column="target",
    )
    assert ds.dataset_id == "test_ds"
    assert len(ds.feature_columns) == 2


def test_experiment_spec_and_result() -> None:
    """Verify ExperimentSpec and ExperimentResult model relations."""
    spec_id = uuid4()
    run_id = uuid4()

    spec = ExperimentSpec(
        experiment_id=spec_id,
        title="Test Benchmark",
        hypothesis="Model A > Model B",
        objective="Verify performance delta",
        function_name="classification_eval",
        dataset_id="synthetic_classification",
        metrics_to_evaluate=["accuracy", "f1_score"],
    )
    assert spec.is_executable is True
    assert spec.random_seed == 42

    result = ExperimentResult(
        run_id=run_id,
        experiment_id=spec_id,
        status="completed",
        summary_metrics={"accuracy": 0.88, "f1_score": 0.87},
    )
    assert result.status == "completed"
    assert result.summary_metrics["accuracy"] == 0.88
