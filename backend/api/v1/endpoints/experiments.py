"""FastAPI endpoints for planning, executing, and inspecting safe experiments."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.experiments.artifacts import get_artifact_store
from backend.experiments.datasets import SecurityError, get_dataset_registry
from backend.experiments.models import (
    Artifact,
    DatasetSpec,
    ExperimentResult,
    ExperimentSpec,
)
from backend.experiments.planner import ExperimentPlanner
from backend.experiments.registry import get_experiment_registry
from backend.experiments.runner import get_experiment_runner

router = APIRouter(prefix="/experiments", tags=["Experiments"])

# In-memory storage of planned specs for the API session
_SPECS_DB: dict[UUID, ExperimentSpec] = {}


class PlanExperimentRequest(BaseModel):
    """Payload to plan an empirical experiment from hypothesis or task."""

    task_title: str = Field(..., min_length=3, description="Task title or experiment goal")
    hypothesis: str | None = Field(default=None, description="Formal scientific hypothesis")
    research_question: str | None = Field(default=None, description="Parent research question")
    constraints: list[str] = Field(
        default_factory=list, description="Resource or scope constraints"
    )


class RunExperimentRequest(BaseModel):
    """Payload to execute an experiment."""

    experiment_id: UUID | None = Field(
        default=None, description="ID of a previously planned ExperimentSpec"
    )
    spec: ExperimentSpec | None = Field(
        default=None, description="Inline ExperimentSpec to execute"
    )


@router.post(
    "/plan",
    response_model=ExperimentSpec,
    status_code=status.HTTP_201_CREATED,
    summary="Plan a new experiment",
)
async def plan_experiment(payload: PlanExperimentRequest) -> ExperimentSpec:
    """Translate a research task into a validated, catalog-backed ExperimentSpec."""
    planner = ExperimentPlanner()
    spec = await planner.plan_experiment(
        task_title=payload.task_title,
        hypothesis=payload.hypothesis,
        research_question=payload.research_question,
        constraints=payload.constraints,
    )
    _SPECS_DB[spec.experiment_id] = spec
    return spec


@router.post(
    "/run",
    response_model=ExperimentResult,
    status_code=status.HTTP_200_OK,
    summary="Execute an approved experiment",
)
async def execute_experiment(payload: RunExperimentRequest) -> ExperimentResult:
    """Execute an approved experiment specification in the safe execution environment."""
    spec: ExperimentSpec | None = None
    if payload.spec:
        spec = payload.spec
        _SPECS_DB[spec.experiment_id] = spec
    elif payload.experiment_id:
        spec = _SPECS_DB.get(payload.experiment_id)

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ExperimentSpec not found. Provide an inline 'spec' or a valid 'experiment_id'.",
        )

    runner = get_experiment_runner()
    result = await runner.run(spec)
    return result


@router.get(
    "/catalog/functions",
    response_model=list[dict],
    summary="List approved experiment functions",
)
async def list_approved_functions() -> list[dict]:
    """Return all verified, whitelisted experiment functions."""
    registry = get_experiment_registry()
    return registry.list_functions()


@router.get(
    "/catalog/datasets",
    response_model=list[DatasetSpec],
    summary="List approved datasets",
)
async def list_approved_datasets() -> list[DatasetSpec]:
    """Return all registered, verified local datasets."""
    datasets = get_dataset_registry()
    return datasets.list_datasets()


@router.get(
    "/{experiment_id}",
    response_model=ExperimentSpec,
    summary="Retrieve planned experiment spec",
)
async def get_experiment_spec(experiment_id: UUID) -> ExperimentSpec:
    """Retrieve details of a planned ExperimentSpec."""
    if experiment_id not in _SPECS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ExperimentSpec with ID '{experiment_id}' not found.",
        )
    return _SPECS_DB[experiment_id]


@router.get(
    "/{experiment_id}/results",
    response_model=ExperimentResult,
    summary="Retrieve latest experiment result",
)
async def get_experiment_result(experiment_id: UUID) -> ExperimentResult:
    """Retrieve the latest execution result and metrics for an experiment."""
    runner = get_experiment_runner()
    result = runner.get_result(experiment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No execution results found for experiment ID '{experiment_id}'.",
        )
    return result


@router.get(
    "/{experiment_id}/artifacts",
    response_model=list[Artifact],
    summary="List artifacts for an experiment",
)
async def list_experiment_artifacts(experiment_id: UUID) -> list[Artifact]:
    """Retrieve all artifacts generated by runs of an experiment."""
    runner = get_experiment_runner()
    result = runner.get_result(experiment_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No results or artifacts found for experiment ID '{experiment_id}'.",
        )
    return result.artifacts


@router.get(
    "/artifacts/{artifact_id}/download",
    summary="Download an experiment artifact file",
)
async def download_artifact(artifact_id: UUID) -> FileResponse:
    """Safely stream an artifact file by ID."""
    store = get_artifact_store()
    artifact = store.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact with ID '{artifact_id}' not found.",
        )

    file_path = Path(artifact.file_path).resolve()
    # Path traversal safety check
    try:
        file_path.relative_to(store.base_dir)
    except (ValueError, SecurityError) as err:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: file resides outside approved artifact repository.",
        ) from err

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artifact file missing from disk.",
        )

    return FileResponse(
        path=str(file_path),
        media_type=artifact.mime_type,
        filename=artifact.name,
    )
