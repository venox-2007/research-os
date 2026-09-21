"""Agent research tools for planning and executing safe experiments."""

from typing import Any

from pydantic import BaseModel, Field

from backend.agents.tools.base import BaseResearchTool
from backend.core.config import Settings, get_settings
from backend.experiments.models import ExperimentSpec
from backend.experiments.planner import ExperimentPlanner
from backend.experiments.provenance import convert_experiment_to_evidence
from backend.experiments.runner import SafeExperimentRunner, get_experiment_runner


class PlanExperimentInput(BaseModel):
    """Input arguments for planning an empirical experiment."""

    task_title: str = Field(..., description="Title or goal of the experimental task")
    hypothesis: str | None = Field(default=None, description="Formal scientific hypothesis")
    research_question: str | None = Field(default=None, description="Parent research question")
    constraints: list[str] = Field(
        default_factory=list, description="Resource or domain constraints"
    )


class ExperimentPlanTool(BaseResearchTool):
    """Translates a research hypothesis into a validated, declarative ExperimentSpec."""

    name: str = "plan_experiment"
    description: str = (
        "Formulate a structured, safe ExperimentSpec from a scientific hypothesis. "
        "Validates that required evaluation routines and datasets are available in the system catalog."
    )
    args_schema: type[BaseModel] = PlanExperimentInput

    def __init__(
        self,
        planner: ExperimentPlanner | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.planner = planner or ExperimentPlanner(settings=self.settings)

    async def _execute(
        self,
        task_title: str,
        hypothesis: str | None = None,
        research_question: str | None = None,
        constraints: list[str] | None = None,
    ) -> dict[str, Any]:
        spec = await self.planner.plan_experiment(
            task_title=task_title,
            hypothesis=hypothesis,
            research_question=research_question,
            constraints=constraints,
        )
        return {
            "experiment_id": str(spec.experiment_id),
            "title": spec.title,
            "hypothesis": spec.hypothesis,
            "function_name": spec.function_name,
            "dataset_id": spec.dataset_id,
            "is_executable": spec.is_executable,
            "unavailability_reasons": spec.unavailability_reasons,
            "spec": spec.model_dump(mode="json"),
        }


class RunExperimentInput(BaseModel):
    """Input arguments for executing a planned ExperimentSpec."""

    spec: dict[str, Any] = Field(..., description="Complete ExperimentSpec dictionary payload")


class ExperimentRunTool(BaseResearchTool):
    """Executes an approved ExperimentSpec in a sandboxed, deterministic environment."""

    name: str = "run_experiment"
    description: str = (
        "Safely execute an approved ExperimentSpec. Prohibits arbitrary code execution, "
        "shell access, and network requests. Computes metrics and generates traceable artifacts."
    )
    args_schema: type[BaseModel] = RunExperimentInput

    def __init__(
        self,
        runner: SafeExperimentRunner | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.runner = runner or get_experiment_runner()

    async def _execute(self, spec: dict[str, Any]) -> dict[str, Any]:
        spec_obj = ExperimentSpec(**spec)
        result = await self.runner.run(spec_obj)

        evidence_obj = convert_experiment_to_evidence(
            result=result,
            spec=spec_obj,
            task_title=spec_obj.title,
        )

        return {
            "result_id": str(result.result_id),
            "run_id": str(result.run_id),
            "experiment_id": str(result.experiment_id),
            "status": result.status,
            "summary_metrics": result.summary_metrics,
            "statistical_analysis": result.statistical_analysis,
            "artifacts_count": len(result.artifacts),
            "artifacts": [a.model_dump(mode="json") for a in result.artifacts],
            "evidence": [evidence_obj.model_dump(mode="json")],
        }
