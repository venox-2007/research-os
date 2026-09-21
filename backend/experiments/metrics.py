"""Modular metrics calculation and statistical analysis layer."""

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from backend.experiments.models import MetricResult


def accuracy_score(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
    """Compute standard classification accuracy."""
    if len(y_true) == 0:
        return 0.0
    correct = sum(1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == yp)
    return round(correct / len(y_true), 4)


def precision_score(y_true: Sequence[int], y_pred: Sequence[int], pos_label: int = 1) -> float:
    """Compute binary classification precision."""
    tp = sum(
        1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == pos_label and yp == pos_label
    )
    fp = sum(
        1 for yt, yp in zip(y_true, y_pred, strict=False) if yt != pos_label and yp == pos_label
    )
    if tp + fp == 0:
        return 0.0
    return round(tp / (tp + fp), 4)


def recall_score(y_true: Sequence[int], y_pred: Sequence[int], pos_label: int = 1) -> float:
    """Compute binary classification recall."""
    tp = sum(
        1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == pos_label and yp == pos_label
    )
    fn = sum(
        1 for yt, yp in zip(y_true, y_pred, strict=False) if yt == pos_label and yp != pos_label
    )
    if tp + fn == 0:
        return 0.0
    return round(tp / (tp + fn), 4)


def f1_score(y_true: Sequence[int], y_pred: Sequence[int], pos_label: int = 1) -> float:
    """Compute harmonic mean of precision and recall."""
    prec = precision_score(y_true, y_pred, pos_label=pos_label)
    rec = recall_score(y_true, y_pred, pos_label=pos_label)
    if prec + rec == 0.0:
        return 0.0
    return round(2.0 * (prec * rec) / (prec + rec), 4)


def mean_absolute_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute Mean Absolute Error (MAE)."""
    if len(y_true) == 0:
        return 0.0
    errors = [abs(float(yt) - float(yp)) for yt, yp in zip(y_true, y_pred, strict=False)]
    return round(sum(errors) / len(errors), 4)


def mean_squared_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute Mean Squared Error (MSE)."""
    if len(y_true) == 0:
        return 0.0
    sq_errors = [(float(yt) - float(yp)) ** 2 for yt, yp in zip(y_true, y_pred, strict=False)]
    return round(sum(sq_errors) / len(sq_errors), 4)


def root_mean_squared_error(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute Root Mean Squared Error (RMSE)."""
    mse = mean_squared_error(y_true, y_pred)
    return round(math.sqrt(mse), 4)


def r2_score(y_true: Sequence[float], y_pred: Sequence[float]) -> float:
    """Compute coefficient of determination ($R^2$)."""
    if len(y_true) == 0:
        return 0.0
    y_mean = sum(float(yt) for yt in y_true) / len(y_true)
    ss_tot = sum((float(yt) - y_mean) ** 2 for yt in y_true)
    ss_res = sum((float(yt) - float(yp)) ** 2 for yt, yp in zip(y_true, y_pred, strict=False))
    if ss_tot == 0.0:
        return 1.0 if ss_res == 0.0 else 0.0
    return round(1.0 - (ss_res / ss_tot), 4)


def compute_summary_statistics(values: Sequence[float]) -> dict[str, float]:
    """Compute basic statistical descriptors: mean, std, median, IQR."""
    if not values:
        return {"mean": 0.0, "std": 0.0, "median": 0.0, "min": 0.0, "max": 0.0}
    arr = np.array([float(v) for v in values])
    return {
        "mean": round(float(np.mean(arr)), 4),
        "std": round(float(np.std(arr)), 4),
        "median": round(float(np.median(arr)), 4),
        "min": round(float(np.min(arr)), 4),
        "max": round(float(np.max(arr)), 4),
        "p25": round(float(np.percentile(arr, 25)), 4),
        "p75": round(float(np.percentile(arr, 75)), 4),
    }


def compute_bootstrap_ci(
    values: Sequence[float],
    n_bootstraps: int = 500,
    ci: float = 0.95,
    seed: int = 42,
) -> tuple[float, float]:
    """Calculate non-parametric bootstrap confidence intervals for the mean."""
    if len(values) < 2:
        val = float(values[0]) if values else 0.0
        return (val, val)

    rng = np.random.default_rng(seed)
    arr = np.array([float(v) for v in values])
    n = len(arr)
    boot_means = np.empty(n_bootstraps)

    for i in range(n_bootstraps):
        sample = rng.choice(arr, size=n, replace=True)
        boot_means[i] = np.mean(sample)

    alpha = (1.0 - ci) / 2.0
    lower = round(float(np.percentile(boot_means, alpha * 100)), 4)
    upper = round(float(np.percentile(boot_means, (1.0 - alpha) * 100)), 4)
    return (lower, upper)


def paired_t_test(baseline: Sequence[float], proposed: Sequence[float]) -> dict[str, Any]:
    """Compute paired Student's t-test comparing two models across matched evaluations."""
    if len(baseline) != len(proposed) or len(baseline) < 2:
        return {"t_stat": 0.0, "p_value": 1.0, "significant": False}

    diffs = np.array([float(p) - float(b) for b, p in zip(baseline, proposed, strict=False)])
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, ddof=1)

    if std_diff == 0.0:
        return {
            "t_stat": 0.0,
            "p_value": 1.0 if mean_diff == 0.0 else 0.0,
            "mean_diff": round(float(mean_diff), 4),
            "significant": mean_diff != 0.0,
        }

    n = len(diffs)
    t_stat = float(mean_diff / (std_diff / math.sqrt(n)))

    # Approximation of two-tailed p-value using standard normal/t distribution
    # For large n, t ~ z; for small n, use basic approximation
    # p ~ 2 * (1 - normal_cdf(|t|))
    z = abs(t_stat)
    p_value = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0))))

    return {
        "t_stat": round(t_stat, 4),
        "p_value": round(float(p_value), 5),
        "mean_diff": round(float(mean_diff), 4),
        "significant": bool(p_value < 0.05),
    }


def build_metric_result(
    name: str,
    value: float,
    unit: str | None = None,
    split: str = "test",
    confidence_interval: tuple[float, float] | None = None,
    higher_is_better: bool = True,
    metadata: dict[str, Any] | None = None,
) -> MetricResult:
    """Factory helper to construct a strongly-typed MetricResult."""
    return MetricResult(
        name=name,
        value=round(float(value), 4),
        unit=unit,
        split=split,
        confidence_interval=confidence_interval,
        higher_is_better=higher_is_better,
        metadata=metadata or {},
    )
