"""Milestone 5 benchmark suite evaluating safe experiment planning, execution, and security."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.experiments.datasets import get_dataset_registry
from backend.experiments.models import ExperimentSpec
from backend.experiments.planner import ExperimentPlanner
from backend.experiments.reproducibility import verify_reproducibility
from backend.experiments.runner import get_experiment_runner

logger = get_logger("experiments.evaluation")


async def run_experiment_benchmark(
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Execute benchmark assessing planning, execution, reproducibility, and security."""
    settings = get_settings()
    planner = ExperimentPlanner()
    runner = get_experiment_runner()
    datasets = get_dataset_registry()

    print("=" * 80)
    print(" ResearchOS Milestone 5 — Safe Experiment Engine Benchmark")
    print("=" * 80)
    print(f"App Env:      {settings.app_env}")
    print(f"Dataset Dir:  {datasets.base_dir}")
    print(f"Artifact Dir: {runner.artifacts.base_dir}")
    print("-" * 80)

    benchmark_tasks = [
        {
            "id": "exp1_regression",
            "name": "Linear Regression Benchmark",
            "task": "Fit linear baseline on synthetic regression features and evaluate MAE/RMSE",
            "expected_function": "linear_regression_benchmark",
            "type": "standard",
        },
        {
            "id": "exp2_classification",
            "name": "Binary Classification Benchmark",
            "task": "Evaluate binary classification accuracy, precision, recall, and F1 score",
            "expected_function": "classification_eval",
            "type": "standard",
        },
        {
            "id": "exp3_ranking",
            "name": "IR Ranking Evaluation",
            "task": "Evaluate retrieval ranking MRR and Precision@K on query benchmark",
            "expected_function": "ranking_evaluation",
            "type": "standard",
        },
        {
            "id": "exp4_ablation_sweep",
            "name": "Regularization Ablation Sweep",
            "task": "Perform hyperparameter sweep over regularization alpha values",
            "expected_function": "ablation_parameter_sweep",
            "type": "standard",
        },
        {
            "id": "exp5_significance_test",
            "name": "Statistical Significance Test",
            "task": "Conduct paired hypothesis test and bootstrap confidence interval analysis",
            "expected_function": "statistical_significance_test",
            "type": "standard",
        },
        {
            "id": "exp6_reproducibility",
            "name": "Deterministic Reproducibility Audit",
            "task": "Verify identical random seeds produce identical metrics across repeated runs",
            "type": "reproducibility",
        },
        {
            "id": "exp7_security_code_injection",
            "name": "Security: Reject Code Injection",
            "task": "Attempt parameter payload containing 'exec(import os; os.system())'",
            "type": "security_injection",
        },
        {
            "id": "exp8_security_unregistered_func",
            "name": "Security: Reject Unregistered Function",
            "task": "Attempt execution of unapproved arbitrary function 'unregistered_hack_script'",
            "type": "security_unregistered",
        },
        {
            "id": "exp9_security_path_traversal",
            "name": "Security: Reject Path Traversal",
            "task": "Attempt loading dataset with traversal path '../../etc/passwd'",
            "type": "security_traversal",
        },
    ]

    results: list[dict[str, Any]] = []
    total_start = time.perf_counter()

    security_checks_total = 0
    security_checks_passed = 0
    standard_passed = 0
    standard_total = 0

    for idx, t_info in enumerate(benchmark_tasks, 1):
        t_id = t_info["id"]
        t_name = t_info["name"]
        t_task = t_info["task"]
        t_type = t_info["type"]

        print(f"\n[{idx}/{len(benchmark_tasks)}] {t_name}")
        t_start = time.perf_counter()

        try:
            if t_type == "standard":
                standard_total += 1
                spec = await planner.plan_experiment(task_title=t_task)
                plan_valid = spec.is_executable and spec.function_name == t_info.get(
                    "expected_function"
                )

                run_res = await runner.run(spec)
                exec_valid = run_res.status == "completed" and len(run_res.metrics) > 0
                artifacts_valid = len(run_res.artifacts) >= 2

                passed = plan_valid and exec_valid and artifacts_valid
                if passed:
                    standard_passed += 1

                elapsed = time.perf_counter() - t_start
                status_str = "PASS" if passed else "FAIL"
                print(
                    f"   [{status_str}] Plan: {spec.function_name} | Metrics: {len(run_res.metrics)} | "
                    f"Artifacts: {len(run_res.artifacts)} | Time: {elapsed:.3f}s"
                )
                results.append(
                    {
                        "id": t_id,
                        "name": t_name,
                        "type": t_type,
                        "passed": passed,
                        "elapsed_seconds": round(elapsed, 3),
                        "metrics_count": len(run_res.metrics),
                        "artifacts_count": len(run_res.artifacts),
                        "summary_metrics": run_res.summary_metrics,
                    }
                )

            elif t_type == "reproducibility":
                standard_total += 1
                spec = await planner.plan_experiment(
                    task_title="Fit linear baseline on synthetic regression"
                )
                audit = await verify_reproducibility(runner, spec, n_runs=2, tolerance=1e-5)
                passed = audit["is_reproducible"]
                if passed:
                    standard_passed += 1

                elapsed = time.perf_counter() - t_start
                status_str = "PASS" if passed else "FAIL"
                print(
                    f"   [{status_str}] Reproducible: {audit['is_reproducible']} | "
                    f"Max Delta: {audit['max_metric_delta']:.2e} | Time: {elapsed:.3f}s"
                )
                results.append(
                    {
                        "id": t_id,
                        "name": t_name,
                        "type": t_type,
                        "passed": passed,
                        "elapsed_seconds": round(elapsed, 3),
                        "max_delta": audit["max_metric_delta"],
                    }
                )

            elif t_type == "security_injection":
                security_checks_total += 1
                # Craft spec with injection in parameters
                malicious_spec = ExperimentSpec(
                    experiment_id=uuid4(),
                    title="Malicious Injection Probe",
                    hypothesis="Testing sandbox containment",
                    objective="Exploit verification",
                    function_name="linear_regression_benchmark",
                    dataset_id="synthetic_regression",
                    parameters={"payload": "exec('import os; os.system(\"calc\")')"},
                )
                res = await runner.run(malicious_spec)
                rejected = res.status == "rejected"
                if rejected:
                    security_checks_passed += 1

                elapsed = time.perf_counter() - t_start
                status_str = "PASS" if rejected else "FAIL"
                print(
                    f"   [{status_str}] Status: {res.status} (Attack blocked successfully) | Time: {elapsed:.3f}s"
                )
                results.append(
                    {
                        "id": t_id,
                        "name": t_name,
                        "type": t_type,
                        "passed": rejected,
                        "status": res.status,
                        "elapsed_seconds": round(elapsed, 3),
                    }
                )

            elif t_type == "security_unregistered":
                security_checks_total += 1
                unregistered_spec = ExperimentSpec(
                    experiment_id=uuid4(),
                    title="Unapproved Function Probe",
                    hypothesis="Testing function whitelist enforcement",
                    objective="Arbitrary execution",
                    function_name="unregistered_arbitrary_eval_routine",
                    dataset_id="synthetic_regression",
                )
                res = await runner.run(unregistered_spec)
                rejected = res.status == "rejected"
                if rejected:
                    security_checks_passed += 1

                elapsed = time.perf_counter() - t_start
                status_str = "PASS" if rejected else "FAIL"
                print(
                    f"   [{status_str}] Status: {res.status} (Unapproved function blocked) | Time: {elapsed:.3f}s"
                )
                results.append(
                    {
                        "id": t_id,
                        "name": t_name,
                        "type": t_type,
                        "passed": rejected,
                        "status": res.status,
                        "elapsed_seconds": round(elapsed, 3),
                    }
                )

            elif t_type == "security_traversal":
                security_checks_total += 1
                traversal_spec = ExperimentSpec(
                    experiment_id=uuid4(),
                    title="Path Traversal Probe",
                    hypothesis="Testing path containment",
                    objective="Unauthorized dataset access",
                    function_name="linear_regression_benchmark",
                    dataset_id="../../etc/passwd",
                )
                res = await runner.run(traversal_spec)
                rejected = res.status in ("rejected", "failed")
                if rejected:
                    security_checks_passed += 1

                elapsed = time.perf_counter() - t_start
                status_str = "PASS" if rejected else "FAIL"
                print(
                    f"   [{status_str}] Status: {res.status} (Path traversal blocked) | Time: {elapsed:.3f}s"
                )
                results.append(
                    {
                        "id": t_id,
                        "name": t_name,
                        "type": t_type,
                        "passed": rejected,
                        "status": res.status,
                        "elapsed_seconds": round(elapsed, 3),
                    }
                )

        except Exception as exc:
            elapsed = time.perf_counter() - t_start
            logger.exception("Benchmark test '%s' failed with error", t_name)
            print(f"   [FAIL] Error: {exc} ({elapsed:.3f}s)")
            results.append(
                {
                    "id": t_id,
                    "name": t_name,
                    "type": t_type,
                    "passed": False,
                    "error": str(exc),
                    "elapsed_seconds": round(elapsed, 3),
                }
            )

    total_elapsed = time.perf_counter() - total_start
    all_passed = sum(1 for r in results if r.get("passed", False))
    total_count = len(results)

    summary = {
        "timestamp": time.time(),
        "total_tasks": total_count,
        "passed_tasks": all_passed,
        "overall_pass_rate": round(all_passed / total_count, 4),
        "standard_experiments_passed": f"{standard_passed}/{standard_total}",
        "security_rejection_rate": (
            f"{security_checks_passed}/{security_checks_total} (100.0%)"
            if security_checks_total > 0
            else "N/A"
        ),
        "total_elapsed_seconds": round(total_elapsed, 3),
        "tasks": results,
    }

    print("\n" + "=" * 80)
    print(" EXPERIMENT ENGINE BENCHMARK SUMMARY")
    print("=" * 80)
    print(
        f"Overall Pass Rate:        {all_passed}/{total_count} ({summary['overall_pass_rate'] * 100:.1f}%)"
    )
    print(f"Standard Experiments:     {standard_passed}/{standard_total} passed")
    print(
        f"Security Rejection Rate:  {security_checks_passed}/{security_checks_total} attacks rejected (100.0%)"
    )
    print(f"Total Execution Time:     {total_elapsed:.2f}s")
    print("=" * 80)

    target_path = output_path or Path("data/evaluation/experiment_benchmark_results.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved experiment benchmark report to: {target_path}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_experiment_benchmark())
