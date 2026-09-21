"""Unit tests for deterministic reproducibility verification."""

from uuid import uuid4

import pytest

from backend.experiments.models import ExperimentSpec
from backend.experiments.reproducibility import get_environment_profile, verify_reproducibility
from backend.experiments.runner import get_experiment_runner


def test_environment_profile_capture() -> None:
    """Verify captured environment profile fields."""
    profile = get_environment_profile()
    assert "python_version" in profile
    assert "numpy_version" in profile
    assert "sklearn_version" in profile
    assert "os_platform" in profile


@pytest.mark.asyncio
async def test_deterministic_reproducibility_verification() -> None:
    """Verify that repeated runs with the same spec and seed produce identical metrics."""
    runner = get_experiment_runner()
    spec = ExperimentSpec(
        experiment_id=uuid4(),
        title="Reproducibility Verification",
        hypothesis="Fixed seed guarantees identical output",
        objective="Numerical equivalence check",
        function_name="linear_regression_benchmark",
        dataset_id="synthetic_regression",
        parameters={"alpha": 1.0},
        random_seed=42,
    )

    audit = await verify_reproducibility(runner, spec, n_runs=2, tolerance=1e-5)
    assert audit["is_reproducible"] is True
    assert audit["max_metric_delta"] == pytest.approx(0.0, abs=1e-5)
    assert audit["runs_evaluated"] == 2
