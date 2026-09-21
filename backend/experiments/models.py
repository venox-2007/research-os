"""Domain models for hypothesis-driven, safe, and reproducible experiments."""

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    """Return timezone-aware current UTC datetime."""
    return datetime.now(UTC)


ExecutionStatus = Literal["pending", "running", "completed", "failed", "rejected"]


class MetricResult(BaseModel):
    """Normalized numerical or statistical evaluation metric."""

    name: str = Field(..., description="Canonical metric identifier, e.g. 'accuracy', 'rmse'")
    value: float = Field(..., description="Computed numerical metric value")
    unit: str | None = Field(default=None, description="Optional unit of measurement")
    split: str = Field(default="test", description="Dataset split (train, val, test, kfold)")
    confidence_interval: tuple[float, float] | None = Field(
        default=None, description="Optional 95% confidence interval bounds (lower, upper)"
    )
    higher_is_better: bool = Field(
        default=True, description="Whether higher values represent superior performance"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional context or calculation parameters"
    )


class Artifact(BaseModel):
    """File or plot output produced during an experiment run."""

    id: UUID = Field(default_factory=uuid4, description="Unique artifact identifier")
    run_id: UUID = Field(..., description="ID of the parent ExperimentRun")
    name: str = Field(..., description="Artifact filename or label")
    artifact_type: str = Field(
        ..., description="Type tag: 'plot', 'csv', 'json', 'summary', 'text'"
    )
    file_path: str = Field(..., description="Relative or absolute path within artifact directory")
    file_hash: str = Field(..., description="SHA-256 checksum of artifact file")
    size_bytes: int = Field(default=0, ge=0, description="File size in bytes")
    mime_type: str = Field(default="application/octet-stream", description="MIME content type")
    created_at: datetime = Field(default_factory=utc_now)


class DatasetSpec(BaseModel):
    """Specification of an approved, validated dataset asset."""

    dataset_id: str = Field(..., description="Canonical identifier in DatasetRegistry")
    name: str = Field(..., description="Human-readable dataset name")
    version: str = Field(default="1.0", description="Dataset version tag")
    file_path: str = Field(..., description="Path to dataset file relative to data/datasets/")
    file_hash: str = Field(..., description="SHA-256 hash of dataset content")
    format: str = Field(default="csv", description="File format: 'csv', 'json', 'synthetic'")
    row_count: int = Field(default=0, ge=0, description="Total number of observations")
    feature_columns: list[str] = Field(default_factory=list, description="Names of feature columns")
    target_column: str | None = Field(default=None, description="Target label or response column")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Dataset descriptive metadata"
    )


class ExperimentConfig(BaseModel):
    """Execution parameters and computational resource constraints."""

    random_seed: int = Field(default=42, description="Random seed for reproducible RNG")
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Hyperparameters passed to registered experiment function"
    )
    timeout_seconds: int = Field(
        default=60, ge=1, le=300, description="Execution timeout threshold"
    )
    max_memory_mb: int = Field(default=512, ge=64, le=4096, description="Memory ceiling in MB")
    env_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Runtime environment snapshot (Python, OS, packages)"
    )


class ExperimentSpec(BaseModel):
    """Declarative specification defining a structured, hypothesis-driven experiment."""

    experiment_id: UUID = Field(default_factory=uuid4, description="Unique experiment identifier")
    task_id: UUID | None = Field(default=None, description="Associated ResearchTask ID")
    title: str = Field(..., description="Short descriptive experiment title")
    hypothesis: str = Field(..., description="Formal scientific hypothesis under investigation")
    objective: str = Field(..., description="Explicit experimental objective")
    function_name: str = Field(
        ..., description="Approved internal function registered in ExperimentRegistry"
    )
    baseline_method: str | None = Field(default=None, description="Baseline model or algorithm")
    proposed_method: str | None = Field(default=None, description="Proposed or variant method")
    dataset_id: str = Field(..., description="Target dataset identifier from DatasetRegistry")
    metrics_to_evaluate: list[str] = Field(
        default_factory=list, description="Target metric names to compute and compare"
    )
    evaluation_protocol: str = Field(
        default="train_test_split",
        description="Protocol description (e.g. '80/20 train_test_split', 'cross_validation')",
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="Input parameters and hyperparameter overrides"
    )
    random_seed: int = Field(default=42, description="RNG seed ensuring deterministic evaluation")
    required_artifacts: list[str] = Field(
        default_factory=lambda: ["metrics.json", "summary.json"],
        description="Required artifact filenames to generate",
    )
    reproducibility_notes: str | None = Field(
        default=None, description="Guidance ensuring exact independent reproduction"
    )
    is_executable: bool = Field(
        default=True,
        description="Whether all required functions and datasets are verified as available",
    )
    unavailability_reasons: list[str] = Field(
        default_factory=list,
        description="Reasons why experiment is marked non-executable if dependencies are missing",
    )
    created_at: datetime = Field(default_factory=utc_now)


class ExperimentRun(BaseModel):
    """Runtime execution record of an ExperimentSpec."""

    run_id: UUID = Field(default_factory=uuid4, description="Unique execution run identifier")
    experiment_id: UUID = Field(..., description="Parent ExperimentSpec identifier")
    status: ExecutionStatus = Field(default="pending", description="Current execution state")
    start_time: datetime = Field(default_factory=utc_now, description="Execution start timestamp")
    end_time: datetime | None = Field(default=None, description="Execution completion timestamp")
    duration_ms: float = Field(default=0.0, ge=0.0, description="Total execution duration in ms")
    random_seed: int = Field(default=42, description="Random seed used in this run")
    code_version: str = Field(
        default="v0.5.0", description="Codebase release or Git commit identifier"
    )
    dataset_hash: str | None = Field(default=None, description="SHA-256 hash of dataset at runtime")
    environment_info: dict[str, Any] = Field(
        default_factory=dict, description="Captured platform, Python, and package versions"
    )
    error_message: str | None = Field(
        default=None, description="Error or failure message if failed"
    )


class ExperimentResult(BaseModel):
    """Complete analyzed deliverable package produced by an ExperimentRun."""

    result_id: UUID = Field(default_factory=uuid4, description="Unique result identifier")
    run_id: UUID = Field(..., description="Associated ExperimentRun identifier")
    experiment_id: UUID = Field(..., description="Associated ExperimentSpec identifier")
    status: ExecutionStatus = Field(default="completed", description="Final run status")
    metrics: list[MetricResult] = Field(
        default_factory=list, description="Granular metric outcomes"
    )
    summary_metrics: dict[str, float] = Field(
        default_factory=dict, description="Primary scalar metrics for quick comparison"
    )
    statistical_analysis: dict[str, Any] = Field(
        default_factory=dict, description="Significance tests, p-values, and confidence intervals"
    )
    artifacts: list[Artifact] = Field(
        default_factory=list, description="Registered artifact files produced by the run"
    )
    provenance: dict[str, Any] = Field(
        default_factory=dict, description="End-to-end lineage mapping back to research hypothesis"
    )
    raw_output: dict[str, Any] = Field(
        default_factory=dict, description="Raw dictionary returned by the registered function"
    )
    created_at: datetime = Field(default_factory=utc_now)
