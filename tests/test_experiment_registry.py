"""Unit tests for ExperimentRegistry whitelisting and approved functions."""

from backend.experiments.datasets import get_dataset_registry
from backend.experiments.registry import get_experiment_registry


def test_default_registry_functions() -> None:
    """Verify standard scientific routines are registered."""
    registry = get_experiment_registry()
    assert registry.has_function("linear_regression_benchmark")
    assert registry.has_function("classification_eval")
    assert registry.has_function("ranking_evaluation")
    assert registry.has_function("ablation_parameter_sweep")
    assert registry.has_function("statistical_significance_test")
    assert not registry.has_function("unregistered_malicious_script")


def test_registry_manifest_metadata() -> None:
    """Verify introspection schema for approved routines."""
    registry = get_experiment_registry()
    manifest = registry.list_functions()
    assert len(manifest) >= 5
    names = {f["name"] for f in manifest}
    assert "linear_regression_benchmark" in names


def test_execute_approved_routine_directly() -> None:
    """Verify executing registered routine with synthetic data produces metrics."""
    registry = get_experiment_registry()
    datasets = get_dataset_registry()

    func = registry.get_function("linear_regression_benchmark")
    assert func is not None

    rows = datasets.load_rows("synthetic_regression")
    output = func(rows, {"alpha": 1.0}, 42)

    assert "metrics" in output
    assert "summary_metrics" in output
    assert output["summary_metrics"]["r2_score"] > 0.8
    assert "plots" in output
