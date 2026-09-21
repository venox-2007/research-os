"""Safe, sandboxed experiment runner executing approved functions with resource limits."""

import asyncio
import platform
import random
import sys
import time
from typing import Any
from uuid import UUID, uuid4

import numpy as np

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.experiments.artifacts import ArtifactStore, get_artifact_store
from backend.experiments.datasets import DatasetRegistry, SecurityError, get_dataset_registry
from backend.experiments.models import (
    Artifact,
    ExperimentResult,
    ExperimentRun,
    ExperimentSpec,
    MetricResult,
    utc_now,
)
from backend.experiments.registry import ExperimentRegistry, get_experiment_registry

logger = get_logger("experiments.runner")

# Injection and dangerous execution patterns prohibited in any parameter
DANGEROUS_PATTERNS = {
    "__import__",
    "eval(",
    "exec(",
    "os.system",
    "subprocess",
    "open(",
    "globals()",
    "locals()",
    "getattr(",
    "shutil",
    "socket",
    "requests",
    "urllib",
    "httpx",
}


def _scan_for_injection(obj: Any) -> None:
    """Recursively scan parameters for code injection, shell payloads, or path traversal."""
    if isinstance(obj, str):
        lower = obj.lower()
        for p in DANGEROUS_PATTERNS:
            if p in lower:
                raise SecurityError(
                    f"Security policy violation: detected prohibited instruction token '{p}' in parameters."
                )
        if ".." in obj:
            raise SecurityError(
                "Security policy violation: detected path traversal tokens '..' in parameters."
            )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _scan_for_injection(k)
            _scan_for_injection(v)
    elif isinstance(obj, (list, tuple, set)):
        for item in obj:
            _scan_for_injection(item)


class SafeExperimentRunner:
    """Executes declarative experiment specifications under verified sandboxed constraints."""

    def __init__(
        self,
        registry: ExperimentRegistry | None = None,
        datasets: DatasetRegistry | None = None,
        artifacts: ArtifactStore | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.registry = registry or get_experiment_registry()
        self.datasets = datasets or get_dataset_registry()
        self.artifacts = artifacts or get_artifact_store()
        self._runs: dict[UUID, ExperimentRun] = {}
        self._results: dict[UUID, ExperimentResult] = {}

    def get_run(self, run_id: UUID) -> ExperimentRun | None:
        """Lookup an experiment run by ID."""
        return self._runs.get(run_id)

    def get_result(self, experiment_id: UUID) -> ExperimentResult | None:
        """Lookup the latest result for an experiment ID."""
        for res in reversed(list(self._results.values())):
            if res.experiment_id == experiment_id:
                return res
        return None

    def get_result_by_id(self, result_id: UUID) -> ExperimentResult | None:
        """Lookup result by unique result ID."""
        return self._results.get(result_id)

    async def run(self, spec: ExperimentSpec) -> ExperimentResult:
        """Validate, prepare, and execute an ExperimentSpec securely."""
        run_id = uuid4()
        t0 = time.perf_counter()

        logger.info("Initializing experiment run %s for spec: '%s'", run_id, spec.title)

        env_info = {
            "python_version": sys.version,
            "platform": platform.platform(),
            "numpy_version": np.__version__,
            "runner": "SafeExperimentRunner",
            "security_mode": "strict_whitelist",
        }

        # 1. Security Check: Reject arbitrary execution or unapproved function
        if not self.registry.has_function(spec.function_name):
            err_msg = (
                f"Security rejection: function '{spec.function_name}' is not in approved ExperimentRegistry. "
                "Arbitrary code, shell commands, or unregistered scripts are strictly forbidden."
            )
            logger.warning(err_msg)
            run = ExperimentRun(
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="rejected",
                start_time=utc_now(),
                end_time=utc_now(),
                random_seed=spec.random_seed,
                environment_info=env_info,
                error_message=err_msg,
            )
            self._runs[run_id] = run
            result = ExperimentResult(
                result_id=uuid4(),
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="rejected",
                provenance={"error": err_msg, "security_violation": True},
            )
            self._results[result.result_id] = result
            return result

        # 2. Security Check: Scan parameters for injection payloads
        try:
            _scan_for_injection(spec.parameters)
            _scan_for_injection(spec.hypothesis)
            _scan_for_injection(spec.dataset_id)
        except SecurityError as sec_err:
            logger.warning("Security rejection in parameters: %s", sec_err)
            run = ExperimentRun(
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="rejected",
                start_time=utc_now(),
                end_time=utc_now(),
                random_seed=spec.random_seed,
                environment_info=env_info,
                error_message=str(sec_err),
            )
            self._runs[run_id] = run
            result = ExperimentResult(
                result_id=uuid4(),
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="rejected",
                provenance={"error": str(sec_err), "security_violation": True},
            )
            self._results[result.result_id] = result
            return result

        # 3. Security Check & Dataset Loading
        try:
            dataset_spec = self.datasets.get(spec.dataset_id)
            if not dataset_spec:
                raise KeyError(
                    f"Dataset '{spec.dataset_id}' not found in approved dataset catalog."
                )
            rows = self.datasets.load_rows(spec.dataset_id)
            dataset_hash = dataset_spec.file_hash
        except (SecurityError, KeyError, FileNotFoundError) as data_err:
            err_msg = f"Dataset access failure: {data_err}"
            logger.warning(err_msg)
            run = ExperimentRun(
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="failed",
                start_time=utc_now(),
                end_time=utc_now(),
                random_seed=spec.random_seed,
                environment_info=env_info,
                error_message=err_msg,
            )
            self._runs[run_id] = run
            result = ExperimentResult(
                result_id=uuid4(),
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="failed",
                provenance={"error": err_msg},
            )
            self._results[result.result_id] = result
            return result

        # 4. Initialize verified run record
        run = ExperimentRun(
            run_id=run_id,
            experiment_id=spec.experiment_id,
            status="running",
            start_time=utc_now(),
            random_seed=spec.random_seed,
            dataset_hash=dataset_hash,
            environment_info=env_info,
        )
        self._runs[run_id] = run

        # 5. Execute approved function in controlled async threadpool with timeout
        func = self.registry.get_function(spec.function_name)
        assert func is not None

        # Seed global and numpy RNG deterministically
        random.seed(spec.random_seed)
        np.random.seed(spec.random_seed)

        timeout_sec = float(spec.parameters.get("timeout_seconds", 60.0))

        try:
            # Run in worker thread to prevent blocking the async loop
            output = await asyncio.wait_for(
                asyncio.to_thread(func, rows, spec.parameters, spec.random_seed),
                timeout=timeout_sec,
            )
        except TimeoutError:
            err_msg = f"Experiment timed out after {timeout_sec:.1f} seconds"
            logger.error(err_msg)
            run.status = "failed"
            run.end_time = utc_now()
            run.duration_ms = (time.perf_counter() - t0) * 1000.0
            run.error_message = err_msg
            result = ExperimentResult(
                result_id=uuid4(),
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="failed",
                provenance={"error": err_msg},
            )
            self._results[result.result_id] = result
            return result
        except Exception as exc:
            err_msg = f"Execution failed: {exc}"
            logger.exception("Experiment execution error in %s", spec.function_name)
            run.status = "failed"
            run.end_time = utc_now()
            run.duration_ms = (time.perf_counter() - t0) * 1000.0
            run.error_message = err_msg
            result = ExperimentResult(
                result_id=uuid4(),
                run_id=run_id,
                experiment_id=spec.experiment_id,
                status="failed",
                provenance={"error": err_msg},
            )
            self._results[result.result_id] = result
            return result

        # 6. Finalize Run Record
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        run.status = "completed"
        run.end_time = utc_now()
        run.duration_ms = round(elapsed_ms, 2)

        # 7. Generate and Persist Artifacts
        artifacts: list[Artifact] = []

        # (a) metrics.json
        metrics_data = [
            m.model_dump(mode="json") if isinstance(m, MetricResult) else m
            for m in output.get("metrics", [])
        ]
        art_metrics = self.artifacts.save_json(run_id, "metrics.json", metrics_data)
        artifacts.append(art_metrics)

        # (b) predictions.csv if available
        if output.get("predictions"):
            art_preds = self.artifacts.save_csv(run_id, "predictions.csv", output["predictions"])
            artifacts.append(art_preds)

        # (c) plots
        for plot_name, plot_cb in output.get("plots", {}).items():
            try:
                art_plot = self.artifacts.save_plot(run_id, plot_name, plot_cb)
                artifacts.append(art_plot)
            except Exception as pe:
                logger.warning("Failed saving plot %s: %s", plot_name, pe)

        # (d) summary.json
        summary_payload = {
            "run_id": str(run_id),
            "experiment_id": str(spec.experiment_id),
            "title": spec.title,
            "hypothesis": spec.hypothesis,
            "function": spec.function_name,
            "dataset_id": spec.dataset_id,
            "dataset_hash": dataset_hash,
            "random_seed": spec.random_seed,
            "duration_ms": run.duration_ms,
            "status": run.status,
            "summary_metrics": output.get("summary_metrics", {}),
            "statistical_analysis": output.get("statistical_analysis", {}),
        }
        art_summary = self.artifacts.save_json(run_id, "summary.json", summary_payload)
        artifacts.append(art_summary)

        # 8. Assemble Provenance Lineage Record
        provenance = {
            "experiment_id": str(spec.experiment_id),
            "run_id": str(run_id),
            "task_id": str(spec.task_id) if spec.task_id else None,
            "hypothesis": spec.hypothesis,
            "objective": spec.objective,
            "baseline_method": spec.baseline_method,
            "proposed_method": spec.proposed_method,
            "dataset": {
                "dataset_id": spec.dataset_id,
                "dataset_hash": dataset_hash,
                "row_count": len(rows),
            },
            "parameters": spec.parameters,
            "random_seed": spec.random_seed,
            "code_version": run.code_version,
            "artifacts_count": len(artifacts),
        }

        # 9. Build Final Result
        metrics_objs: list[MetricResult] = []
        for m in output.get("metrics", []):
            if isinstance(m, MetricResult):
                metrics_objs.append(m)
            elif isinstance(m, dict):
                metrics_objs.append(MetricResult(**m))

        result = ExperimentResult(
            result_id=uuid4(),
            run_id=run_id,
            experiment_id=spec.experiment_id,
            status="completed",
            metrics=metrics_objs,
            summary_metrics=output.get("summary_metrics", {}),
            statistical_analysis=output.get("statistical_analysis", {}),
            artifacts=artifacts,
            provenance=provenance,
            raw_output={k: v for k, v in output.items() if k != "plots"},
        )
        self._results[result.result_id] = result

        logger.info(
            "Experiment run %s completed in %.1fms with %d metrics and %d artifacts",
            run_id,
            run.duration_ms,
            len(metrics_objs),
            len(artifacts),
        )
        return result


_DEFAULT_EXPERIMENT_RUNNER: SafeExperimentRunner | None = None


def get_experiment_runner() -> SafeExperimentRunner:
    """Singleton/factory accessor for SafeExperimentRunner."""
    global _DEFAULT_EXPERIMENT_RUNNER
    if _DEFAULT_EXPERIMENT_RUNNER is None:
        _DEFAULT_EXPERIMENT_RUNNER = SafeExperimentRunner()
    return _DEFAULT_EXPERIMENT_RUNNER
