"""Reproducibility verification and environment fingerprinting engine."""

import platform
import sys
from typing import Any

import numpy as np
import sklearn

from backend.core.logging import get_logger
from backend.experiments.models import ExperimentSpec
from backend.experiments.runner import SafeExperimentRunner

logger = get_logger("experiments.reproducibility")


def get_environment_profile() -> dict[str, str]:
    """Capture precise hardware, OS, Python, and mathematical dependency versions."""
    return {
        "python_version": sys.version.split()[0],
        "os_platform": platform.platform(),
        "os_system": platform.system(),
        "architecture": platform.machine(),
        "numpy_version": np.__version__,
        "sklearn_version": sklearn.__version__,
    }


async def verify_reproducibility(
    runner: SafeExperimentRunner,
    spec: ExperimentSpec,
    n_runs: int = 2,
    tolerance: float = 1e-5,
) -> dict[str, Any]:
    """Execute identical experiment runs and verify numerical equivalence of metrics."""
    logger.info("Executing reproducibility audit for spec '%s' across %d runs", spec.title, n_runs)

    runs_results = []
    for run_idx in range(n_runs):
        res = await runner.run(spec)
        if res.status != "completed":
            return {
                "is_reproducible": False,
                "error": f"Run {run_idx + 1} failed with status '{res.status}'",
                "max_metric_delta": 1.0,
                "runs_evaluated": run_idx + 1,
            }
        runs_results.append(res)

    # Compare summary metrics of all runs to the first run
    base_metrics = runs_results[0].summary_metrics
    max_delta = 0.0
    differences: dict[str, list[float]] = {}

    for metric_name, base_val in base_metrics.items():
        all_vals = [r.summary_metrics.get(metric_name, 0.0) for r in runs_results]
        differences[metric_name] = all_vals
        for val in all_vals[1:]:
            delta = abs(val - base_val)
            if delta > max_delta:
                max_delta = delta

    is_reproducible = max_delta <= tolerance
    logger.info(
        "Reproducibility verdict: %s (max delta: %.2e, tolerance: %.2e)",
        "PASS" if is_reproducible else "FAIL",
        max_delta,
        tolerance,
    )

    return {
        "is_reproducible": is_reproducible,
        "max_metric_delta": round(float(max_delta), 7),
        "tolerance": tolerance,
        "runs_evaluated": n_runs,
        "metrics_comparison": differences,
        "environment_profile": get_environment_profile(),
    }
