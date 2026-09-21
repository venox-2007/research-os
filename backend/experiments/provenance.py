"""Full lineage provenance graph and evidence conversion for experiment results."""

from typing import Any
from uuid import uuid4

from backend.core.models import Evidence
from backend.experiments.models import ExperimentResult, ExperimentSpec


def build_experiment_provenance_record(
    spec: ExperimentSpec,
    result: ExperimentResult,
    question: str | None = None,
    task_title: str | None = None,
) -> dict[str, Any]:
    """Assemble complete end-to-end lineage graph for an experimental evaluation."""
    return {
        "research_question": question,
        "research_task": task_title,
        "task_id": str(spec.task_id) if spec.task_id else None,
        "experiment_id": str(spec.experiment_id),
        "run_id": str(result.run_id),
        "hypothesis": spec.hypothesis,
        "objective": spec.objective,
        "baseline_method": spec.baseline_method,
        "proposed_method": spec.proposed_method,
        "function_name": spec.function_name,
        "dataset_spec": {
            "dataset_id": spec.dataset_id,
            "dataset_hash": result.provenance.get("dataset", {}).get("dataset_hash"),
            "row_count": result.provenance.get("dataset", {}).get("row_count", 0),
        },
        "config": {
            "parameters": spec.parameters,
            "random_seed": spec.random_seed,
            "evaluation_protocol": spec.evaluation_protocol,
        },
        "metrics": result.summary_metrics,
        "statistical_analysis": result.statistical_analysis,
        "artifacts": [
            {
                "artifact_id": str(a.id),
                "name": a.name,
                "type": a.artifact_type,
                "file_hash": a.file_hash,
                "size_bytes": a.size_bytes,
            }
            for a in result.artifacts
        ],
        "status": result.status,
    }


def convert_experiment_to_evidence(
    result: ExperimentResult,
    spec: ExperimentSpec,
    task_title: str | None = None,
) -> Evidence:
    """Convert experimental outcome into a first-class verified Evidence object."""
    metrics_str = ", ".join(f"{k} = {v:.3f}" for k, v in result.summary_metrics.items())
    content = (
        f"Empirical Experiment Result for '{spec.title}'. "
        f"Hypothesis: {spec.hypothesis}. "
        f"Evaluated on {spec.dataset_id} ({spec.evaluation_protocol}). "
        f"Key Metrics: {metrics_str}. "
        f"Artifacts generated: {[a.name for a in result.artifacts]}."
    )

    ev_id = uuid4()
    source_id = uuid4()
    provenance_summary = (
        f"ExperimentRun {result.run_id} | Spec {spec.experiment_id} | "
        f"Func: {spec.function_name} | Dataset: {spec.dataset_id}"
    )

    return Evidence(
        id=ev_id,
        source_id=source_id,
        chunk_id=f"exp_{result.run_id}",
        source_title=f"Experiment: {spec.title}",
        content=content,
        section="Empirical Results",
        page_number=1,
        confidence_score=0.98 if result.status == "completed" else 0.4,
        extraction_method="safe_experiment_engine",
        provenance_summary=provenance_summary,
        metadata={
            "run_id": str(result.run_id),
            "experiment_id": str(spec.experiment_id),
            "summary_metrics": result.summary_metrics,
            "statistical_analysis": result.statistical_analysis,
            "artifacts": [str(a.id) for a in result.artifacts],
            "dataset_id": spec.dataset_id,
            "task_title": task_title,
        },
    )
