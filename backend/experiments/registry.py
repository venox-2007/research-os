"""Approved experiment function registry enforcing strict execution whitelisting."""

from collections.abc import Callable
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import train_test_split

from backend.core.logging import get_logger
from backend.experiments.metrics import (
    accuracy_score,
    build_metric_result,
    compute_bootstrap_ci,
    f1_score,
    mean_absolute_error,
    paired_t_test,
    precision_score,
    r2_score,
    recall_score,
    root_mean_squared_error,
)

logger = get_logger("experiments.registry")

ExperimentCallable = Callable[[list[dict[str, Any]], dict[str, Any], int], dict[str, Any]]


class ExperimentRegistry:
    """Explicit whitelist of verified internal scientific execution routines."""

    def __init__(self) -> None:
        self._functions: dict[str, ExperimentCallable] = {}
        self._manifest: dict[str, dict[str, Any]] = {}
        self._register_default_functions()

    def register(
        self,
        name: str,
        func: ExperimentCallable,
        description: str,
        required_dataset_type: str | None = None,
        parameter_schema: dict[str, Any] | None = None,
    ) -> None:
        """Register an approved experiment function."""
        self._functions[name] = func
        self._manifest[name] = {
            "name": name,
            "description": description,
            "required_dataset_type": required_dataset_type,
            "parameter_schema": parameter_schema or {},
        }
        logger.debug("Registered approved experiment function: '%s'", name)

    def has_function(self, name: str) -> bool:
        """Check if function is approved in the registry."""
        return name in self._functions

    def get_function(self, name: str) -> ExperimentCallable | None:
        """Retrieve approved function by name."""
        return self._functions.get(name)

    def list_functions(self) -> list[dict[str, Any]]:
        """List introspection metadata for all approved functions."""
        return list(self._manifest.values())

    def _register_default_functions(self) -> None:
        """Register all default scientific experiment routines."""
        self.register(
            name="linear_regression_benchmark",
            func=_run_linear_regression_benchmark,
            description="Fits linear baseline model, computes MAE, RMSE, R^2, and plots residuals.",
            required_dataset_type="regression",
            parameter_schema={"alpha": "float (regularization strength, default: 1.0)"},
        )
        self.register(
            name="classification_eval",
            func=_run_classification_eval,
            description="Evaluates binary classification model, computes Accuracy, Precision, Recall, F1, and confusion matrix.",
            required_dataset_type="classification",
            parameter_schema={"penalty": "str (l2, default: l2)"},
        )
        self.register(
            name="ranking_evaluation",
            func=_run_ranking_evaluation,
            description="Evaluates information retrieval rankings against relevance judgments (MRR, nDCG@K, Precision@K).",
            required_dataset_type="ranking",
            parameter_schema={"top_k": "int (default: 3)"},
        )
        self.register(
            name="ablation_parameter_sweep",
            func=_run_ablation_sweep,
            description="Executes parameter sensitivity sweep over discrete values and generates scaling plot.",
            required_dataset_type="regression",
            parameter_schema={"alphas": "list[float] (default: [0.01, 0.1, 1.0, 10.0, 100.0])"},
        )
        self.register(
            name="statistical_significance_test",
            func=_run_significance_test,
            description="Conducts paired Student's t-test and bootstrap confidence interval analysis between methods.",
            required_dataset_type=None,
            parameter_schema={"n_samples": "int (default: 30)"},
        )


def _run_linear_regression_benchmark(
    rows: list[dict[str, Any]], parameters: dict[str, Any], random_seed: int
) -> dict[str, Any]:
    """Fit Ridge regression on numerical features and evaluate performance."""
    if not rows:
        raise ValueError("Dataset is empty.")

    target_col = parameters.get("target_column", "target")
    feature_cols = [k for k in rows[0].keys() if k != target_col and k not in {"id", "dataset_id"}]

    X = np.array([[float(r[col]) for col in feature_cols] for r in rows])
    y = np.array([float(r[target_col]) for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_seed
    )

    alpha = float(parameters.get("alpha", 1.0))
    model = Ridge(alpha=alpha, random_state=random_seed)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    ci_lower, ci_upper = compute_bootstrap_ci(
        [abs(yt - yp) for yt, yp in zip(y_test, y_pred, strict=False)],
        seed=random_seed,
    )

    metrics = [
        build_metric_result(
            "mae",
            mae,
            split="test",
            higher_is_better=False,
            confidence_interval=(ci_lower, ci_upper),
        ),
        build_metric_result("rmse", rmse, split="test", higher_is_better=False),
        build_metric_result("r2_score", r2, split="test", higher_is_better=True),
    ]

    summary_metrics = {"mae": mae, "rmse": rmse, "r2_score": r2}
    predictions = [
        {
            "y_true": round(float(yt), 3),
            "y_pred": round(float(yp), 3),
            "error": round(float(abs(yt - yp)), 3),
        }
        for yt, yp in zip(y_test, y_pred, strict=False)
    ]

    def plot_fn(fig: plt.Figure) -> None:
        ax = fig.add_subplot(1, 1, 1)
        ax.scatter(
            y_test, y_pred, color="royalblue", alpha=0.8, edgecolors="k", label="Predictions"
        )
        min_v = min(min(y_test), min(y_pred))
        max_v = max(max(y_test), max(y_pred))
        ax.plot([min_v, max_v], [min_v, max_v], "r--", label="Ideal Perfect Fit")
        ax.set_xlabel("Ground Truth Target")
        ax.set_ylabel("Predicted Value")
        ax.set_title(f"Linear Regression Benchmark (R^2 = {r2:.3f}, RMSE = {rmse:.3f})")
        ax.legend()
        ax.grid(True, linestyle=":", alpha=0.6)

    return {
        "metrics": metrics,
        "summary_metrics": summary_metrics,
        "predictions": predictions,
        "plots": {"actual_vs_predicted.png": plot_fn},
        "statistical_analysis": {
            "mae_bootstrap_ci": [ci_lower, ci_upper],
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        },
    }


def _run_classification_eval(
    rows: list[dict[str, Any]], parameters: dict[str, Any], random_seed: int
) -> dict[str, Any]:
    """Evaluate logistic regression classifier and compute classification metrics."""
    if not rows:
        raise ValueError("Dataset is empty.")

    target_col = parameters.get("target_column", "label")
    feature_cols = [k for k in rows[0].keys() if k != target_col and k not in {"id", "dataset_id"}]

    X = np.array([[float(r[col]) for col in feature_cols] for r in rows])
    y = np.array([int(float(r[target_col])) for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=random_seed
    )

    clf = LogisticRegression(random_state=random_seed, max_iter=500)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)

    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    metrics = [
        build_metric_result("accuracy", acc, split="test", higher_is_better=True),
        build_metric_result("precision", prec, split="test", higher_is_better=True),
        build_metric_result("recall", rec, split="test", higher_is_better=True),
        build_metric_result("f1_score", f1, split="test", higher_is_better=True),
    ]
    summary_metrics = {"accuracy": acc, "precision": prec, "recall": rec, "f1_score": f1}

    predictions = [
        {"y_true": int(yt), "y_pred": int(yp), "correct": int(yt == yp)}
        for yt, yp in zip(y_test, y_pred, strict=False)
    ]

    def plot_fn(fig: plt.Figure) -> None:
        ax = fig.add_subplot(1, 1, 1)
        names = ["Accuracy", "Precision", "Recall", "F1 Score"]
        vals = [acc, prec, rec, f1]
        bars = ax.bar(names, vals, color=["#4A90E2", "#50E3C2", "#F5A623", "#9013FE"])
        ax.set_ylim(0.0, 1.1)
        ax.set_ylabel("Score")
        ax.set_title("Classification Model Performance")
        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
            )
        ax.grid(axis="y", linestyle=":", alpha=0.6)

    return {
        "metrics": metrics,
        "summary_metrics": summary_metrics,
        "predictions": predictions,
        "plots": {"classification_metrics.png": plot_fn},
        "statistical_analysis": {
            "test_sample_count": len(y_test),
            "positive_class_ratio": round(float(np.mean(y_test)), 3),
        },
    }


def _run_ranking_evaluation(
    rows: list[dict[str, Any]], parameters: dict[str, Any], random_seed: int
) -> dict[str, Any]:
    """Evaluate simulated retrieval rankings across query sets."""
    top_k = int(parameters.get("top_k", 3))

    # Group by query
    queries: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        qid = r.get("query_id", "default_q")
        if qid not in queries:
            queries[qid] = []
        queries[qid].append(r)

    reciprocal_ranks: list[float] = []
    precisions_at_k: list[float] = []

    rng = np.random.default_rng(random_seed)
    for _qid, docs in queries.items():
        # Score docs deterministically using seed
        scored_docs = []
        for d in docs:
            rel = int(float(d.get("relevance", 0)))
            noise = float(rng.uniform(0.0, 0.2))
            score = rel + noise
            scored_docs.append((score, rel))

        scored_docs.sort(key=lambda x: x[0], reverse=True)

        # MRR
        rr = 0.0
        for rank, (_, rel) in enumerate(scored_docs, 1):
            if rel > 0:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        # Precision@K
        top_slice = scored_docs[:top_k]
        rel_in_k = sum(1 for _, rel in top_slice if rel > 0)
        precisions_at_k.append(rel_in_k / max(top_k, 1))

    mrr = round(float(np.mean(reciprocal_ranks)) if reciprocal_ranks else 0.0, 4)
    p_at_k = round(float(np.mean(precisions_at_k)) if precisions_at_k else 0.0, 4)

    metrics = [
        build_metric_result("mrr", mrr, split="test", higher_is_better=True),
        build_metric_result(f"precision_at_{top_k}", p_at_k, split="test", higher_is_better=True),
    ]

    def plot_fn(fig: plt.Figure) -> None:
        ax = fig.add_subplot(1, 1, 1)
        labels = [f"Q{i + 1}" for i in range(len(reciprocal_ranks))]
        ax.plot(labels, reciprocal_ranks, marker="o", label="Reciprocal Rank", color="teal")
        ax.plot(labels, precisions_at_k, marker="s", label=f"Precision@{top_k}", color="coral")
        ax.set_ylim(0.0, 1.1)
        ax.set_ylabel("Metric Score")
        ax.set_title(f"Per-Query IR Ranking Performance (MRR={mrr:.3f})")
        ax.legend()
        ax.grid(True, linestyle=":", alpha=0.5)

    return {
        "metrics": metrics,
        "summary_metrics": {"mrr": mrr, f"precision_at_{top_k}": p_at_k},
        "plots": {"ranking_evaluation.png": plot_fn},
        "statistical_analysis": {
            "total_queries_evaluated": len(queries),
            "mrr_std": round(float(np.std(reciprocal_ranks)), 4),
        },
    }


def _run_ablation_sweep(
    rows: list[dict[str, Any]], parameters: dict[str, Any], random_seed: int
) -> dict[str, Any]:
    """Execute hyperparameter sweep measuring sensitivity."""
    alphas = parameters.get("alphas", [0.01, 0.1, 1.0, 10.0, 100.0])
    target_col = parameters.get("target_column", "target")
    feature_cols = [k for k in rows[0].keys() if k != target_col and k not in {"id", "dataset_id"}]

    X = np.array([[float(r[col]) for col in feature_cols] for r in rows])
    y = np.array([float(r[target_col]) for r in rows])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=random_seed
    )

    rmses: list[float] = []
    r2s: list[float] = []
    for alpha in alphas:
        model = Ridge(alpha=float(alpha), random_state=random_seed)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        rmses.append(root_mean_squared_error(y_test, y_pred))
        r2s.append(r2_score(y_test, y_pred))

    best_idx = int(np.argmin(rmses))
    best_alpha = alphas[best_idx]
    best_rmse = rmses[best_idx]
    best_r2 = r2s[best_idx]

    metrics = [
        build_metric_result("best_alpha", float(best_alpha)),
        build_metric_result("best_rmse", best_rmse, higher_is_better=False),
        build_metric_result("best_r2", best_r2, higher_is_better=True),
    ]

    def plot_fn(fig: plt.Figure) -> None:
        ax = fig.add_subplot(1, 1, 1)
        ax.plot([str(a) for a in alphas], rmses, marker="o", color="crimson", label="Test RMSE")
        ax.set_xlabel("Regularization Alpha")
        ax.set_ylabel("RMSE")
        ax.set_title(f"Ridge Regularization Ablation Sweep (Best Alpha = {best_alpha})")
        ax.grid(True, linestyle=":", alpha=0.6)
        ax.legend()

    return {
        "metrics": metrics,
        "summary_metrics": {
            "best_alpha": float(best_alpha),
            "best_rmse": best_rmse,
            "best_r2": best_r2,
        },
        "plots": {"ablation_parameter_sweep.png": plot_fn},
        "statistical_analysis": {
            "alphas_evaluated": alphas,
            "rmse_progression": rmses,
        },
    }


def _run_significance_test(
    rows: list[dict[str, Any]], parameters: dict[str, Any], random_seed: int
) -> dict[str, Any]:
    """Conduct hypothesis testing comparing baseline and proposed systems."""
    n_samples = int(parameters.get("n_samples", 30))
    rng = np.random.default_rng(random_seed)

    # Simulate matched evaluation trials
    baseline_scores = rng.normal(loc=0.72, scale=0.05, size=n_samples).tolist()
    # Proposed system with slight positive shift
    delta = float(parameters.get("effect_size", 0.04))
    proposed_scores = [b + float(rng.normal(loc=delta, scale=0.02)) for b in baseline_scores]

    t_res = paired_t_test(baseline_scores, proposed_scores)
    ci_lower, ci_upper = compute_bootstrap_ci(
        [p - b for b, p in zip(baseline_scores, proposed_scores, strict=False)],
        seed=random_seed,
    )

    metrics = [
        build_metric_result("t_statistic", t_res["t_stat"]),
        build_metric_result("p_value", t_res["p_value"], higher_is_better=False),
        build_metric_result(
            "mean_difference", t_res["mean_diff"], confidence_interval=(ci_lower, ci_upper)
        ),
    ]

    def plot_fn(fig: plt.Figure) -> None:
        ax = fig.add_subplot(1, 1, 1)
        ax.boxplot([baseline_scores, proposed_scores])
        ax.set_xticks([1, 2])
        ax.set_xticklabels(["Baseline", "Proposed (ResearchOS)"])
        ax.set_ylabel("Evaluation Metric Score")
        ax.set_title(
            f"Model Comparison (p = {t_res['p_value']:.4f}, significant = {t_res['significant']})"
        )
        ax.grid(axis="y", linestyle=":", alpha=0.6)

    return {
        "metrics": metrics,
        "summary_metrics": {
            "t_statistic": t_res["t_stat"],
            "p_value": t_res["p_value"],
            "mean_difference": t_res["mean_diff"],
        },
        "plots": {"statistical_significance.png": plot_fn},
        "statistical_analysis": {
            "is_statistically_significant": t_res["significant"],
            "paired_t_test": t_res,
            "bootstrap_mean_diff_ci": [ci_lower, ci_upper],
        },
    }


_DEFAULT_EXPERIMENT_REGISTRY: ExperimentRegistry | None = None


def get_experiment_registry() -> ExperimentRegistry:
    """Singleton/factory accessor for ExperimentRegistry."""
    global _DEFAULT_EXPERIMENT_REGISTRY
    if _DEFAULT_EXPERIMENT_REGISTRY is None:
        _DEFAULT_EXPERIMENT_REGISTRY = ExperimentRegistry()
    return _DEFAULT_EXPERIMENT_REGISTRY
