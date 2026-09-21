"""Unit tests for metric calculations, bootstrap confidence intervals, and statistical tests."""

import pytest

from backend.experiments.metrics import (
    accuracy_score,
    compute_bootstrap_ci,
    compute_summary_statistics,
    f1_score,
    mean_absolute_error,
    paired_t_test,
    precision_score,
    r2_score,
    recall_score,
    root_mean_squared_error,
)


def test_classification_metrics() -> None:
    """Verify precision, recall, f1, and accuracy computations."""
    y_true = [1, 1, 0, 0, 1, 0]
    y_pred = [1, 0, 0, 0, 1, 1]

    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    assert acc == pytest.approx(4 / 6, abs=0.01)
    assert prec == pytest.approx(2 / 3, abs=0.01)
    assert rec == pytest.approx(2 / 3, abs=0.01)
    assert f1 == pytest.approx(2 / 3, abs=0.01)


def test_regression_metrics() -> None:
    """Verify MAE, RMSE, and R2 computations."""
    y_true = [3.0, -0.5, 2.0, 7.0]
    y_pred = [2.5, 0.0, 2.0, 8.0]

    mae = mean_absolute_error(y_true, y_pred)
    rmse = root_mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    assert mae == 0.5
    assert rmse == pytest.approx(0.612, abs=0.01)
    assert r2 > 0.9


def test_summary_and_bootstrap_statistics() -> None:
    """Verify statistical summary and bootstrap confidence interval computation."""
    data = [10.0, 12.0, 11.0, 14.0, 13.0, 12.0, 15.0]
    stats = compute_summary_statistics(data)
    assert stats["mean"] == pytest.approx(12.43, abs=0.05)
    assert stats["min"] == 10.0
    assert stats["max"] == 15.0

    lower, upper = compute_bootstrap_ci(data, n_bootstraps=200, seed=42)
    assert lower < upper
    assert lower <= stats["mean"] <= upper


def test_paired_t_test() -> None:
    """Verify paired Student's t-test detects statistically significant differences."""
    baseline = [0.70, 0.72, 0.69, 0.71, 0.73]
    proposed = [0.85, 0.88, 0.84, 0.86, 0.87]

    res = paired_t_test(baseline, proposed)
    assert res["significant"] is True
    assert res["p_value"] < 0.01
    assert res["mean_diff"] > 0.1
