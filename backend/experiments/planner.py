"""Autonomous Experiment Planner converting research hypotheses into safe, validated ExperimentSpecs."""

import json
import re
from typing import Any
from uuid import UUID, uuid4

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.experiments.datasets import DatasetRegistry, get_dataset_registry
from backend.experiments.models import ExperimentSpec
from backend.experiments.registry import ExperimentRegistry, get_experiment_registry
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider

logger = get_logger("experiments.planner")

PLANNER_SYSTEM_PROMPT = """You are the Senior Scientific Experiment Designer for ResearchOS.
Your objective is to translate a research question, task, or hypothesis into a rigorous, reproducible, safe experiment plan.

Rules:
1. You may ONLY choose an approved function from the available registry functions:
   - linear_regression_benchmark
   - classification_eval
   - ranking_evaluation
   - ablation_parameter_sweep
   - statistical_significance_test
2. You may ONLY choose an approved dataset from the available datasets:
   - synthetic_classification
   - synthetic_regression
   - synthetic_retrieval
3. If an experiment requires a dataset or function not listed above, you MUST note it in unavailability_reasons.
4. Do NOT output arbitrary Python code or shell commands.

Respond ONLY with valid JSON matching this schema:
{
  "title": "Ablation evaluation of ...",
  "hypothesis": "Increasing regularization alpha reduces test variance by ...",
  "objective": "Quantify test generalization metrics ...",
  "function_name": "linear_regression_benchmark",
  "dataset_id": "synthetic_regression",
  "baseline_method": "Unregularized Linear Fit",
  "proposed_method": "Ridge Regression (alpha=1.0)",
  "metrics_to_evaluate": ["mae", "rmse", "r2_score"],
  "evaluation_protocol": "80/20 train/test split with seed 42",
  "parameters": {"alpha": 1.0},
  "random_seed": 42,
  "reproducibility_notes": "Deterministic seed with fixed dataset snapshot."
}
"""


class ExperimentPlanner:
    """Translates research tasks into structured, catalog-validated ExperimentSpecs."""

    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        registry: ExperimentRegistry | None = None,
        datasets: DatasetRegistry | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm or get_llm_provider(settings=self.settings)
        self.registry = registry or get_experiment_registry()
        self.datasets = datasets or get_dataset_registry()

    async def plan_experiment(
        self,
        task_title: str,
        hypothesis: str | None = None,
        research_question: str | None = None,
        constraints: list[str] | None = None,
        task_id: UUID | None = None,
    ) -> ExperimentSpec:
        """Formulate a validated ExperimentSpec for the given task and hypothesis."""
        logger.info("Formulating experiment plan for: '%s'", task_title[:80])

        hypo_text = (
            hypothesis or f"Proposed method achieves measurable performance gains on {task_title}."
        )
        prompt = (
            f"Research Task: {task_title}\n"
            f"Research Question: {research_question or 'General Investigation'}\n"
            f"Hypothesis: {hypo_text}\n"
            f"Constraints: {', '.join(constraints or [])}\n"
            f"Available Functions: {[f['name'] for f in self.registry.list_functions()]}\n"
            f"Available Datasets: {[d.dataset_id for d in self.datasets.list_datasets()]}\n"
        )

        plan_data: dict[str, Any] = {}
        if self.settings.app_env != "testing" and self.settings.llm_provider != "mock":
            try:
                response = await self.llm.generate(
                    prompt=prompt,
                    system_prompt=PLANNER_SYSTEM_PROMPT,
                )
                parsed = self._parse_json(response.content)
                if parsed:
                    plan_data = parsed
            except Exception as exc:
                logger.warning(
                    "LLM experiment planning call failed (%s). Using heuristic fallback.", exc
                )

        if not plan_data:
            plan_data = self._heuristic_plan(task_title, hypo_text)

        # Validate against system catalog
        function_name = plan_data.get("function_name", "linear_regression_benchmark")
        dataset_id = plan_data.get("dataset_id", "synthetic_regression")

        unavailability_reasons: list[str] = []
        is_executable = True

        if not self.registry.has_function(function_name):
            is_executable = False
            unavailability_reasons.append(
                f"Requested function '{function_name}' is not in approved ExperimentRegistry."
            )

        if not self.datasets.has_dataset(dataset_id):
            is_executable = False
            unavailability_reasons.append(
                f"Requested dataset '{dataset_id}' is not in approved DatasetRegistry."
            )

        spec = ExperimentSpec(
            experiment_id=uuid4(),
            task_id=task_id,
            title=plan_data.get("title", f"Experiment: {task_title[:60]}"),
            hypothesis=plan_data.get("hypothesis", hypo_text),
            objective=plan_data.get("objective", f"Empirical evaluation of {task_title}"),
            function_name=function_name,
            baseline_method=plan_data.get("baseline_method", "Standard Baseline"),
            proposed_method=plan_data.get("proposed_method", "ResearchOS Proposed Method"),
            dataset_id=dataset_id,
            metrics_to_evaluate=plan_data.get("metrics_to_evaluate", ["mae", "rmse"]),
            evaluation_protocol=plan_data.get(
                "evaluation_protocol", "Deterministic 80/20 train/test split"
            ),
            parameters=plan_data.get("parameters", {}),
            random_seed=int(plan_data.get("random_seed", 42)),
            required_artifacts=plan_data.get(
                "required_artifacts", ["metrics.json", "summary.json"]
            ),
            reproducibility_notes=plan_data.get(
                "reproducibility_notes", "Deterministic execution with fixed dataset snapshot."
            ),
            is_executable=is_executable,
            unavailability_reasons=unavailability_reasons,
        )

        logger.info(
            "Formulated ExperimentSpec %s (function: %s, dataset: %s, executable: %s)",
            spec.experiment_id,
            spec.function_name,
            spec.dataset_id,
            spec.is_executable,
        )
        return spec

    def _heuristic_plan(self, task_title: str, hypothesis: str) -> dict[str, Any]:
        """Deterministic domain heuristic planner for test environments and zero-failure fallbacks."""
        t_lower = task_title.lower()

        if any(
            w in t_lower for w in ["retrieval", "search", "ranking", "hybrid", "rag", "mrr", "ndcg"]
        ):
            return {
                "title": f"Retrieval Ranking Evaluation: {task_title[:50]}",
                "hypothesis": hypothesis,
                "objective": "Measure Mean Reciprocal Rank (MRR) and Precision@K on benchmark queries.",
                "function_name": "ranking_evaluation",
                "dataset_id": "synthetic_retrieval",
                "baseline_method": "Single-Vector Lexical Search",
                "proposed_method": "Hybrid Reciprocal Rank Fusion",
                "metrics_to_evaluate": ["mrr", "precision_at_3"],
                "evaluation_protocol": "Query-level rank ordering across candidate documents",
                "parameters": {"top_k": 3},
                "random_seed": 42,
            }
        elif any(
            w in t_lower
            for w in ["classification", "detect", "sentiment", "predict class", "categorize"]
        ):
            return {
                "title": f"Classification Benchmark: {task_title[:50]}",
                "hypothesis": hypothesis,
                "objective": "Assess binary classification accuracy, F1-score, and precision-recall trade-offs.",
                "function_name": "classification_eval",
                "dataset_id": "synthetic_classification",
                "baseline_method": "Majority Class Predictor",
                "proposed_method": "Regularized Logistic Classifier",
                "metrics_to_evaluate": ["accuracy", "precision", "recall", "f1_score"],
                "evaluation_protocol": "70/30 stratified train/test split",
                "parameters": {"penalty": "l2"},
                "random_seed": 42,
            }
        elif any(
            w in t_lower for w in ["sweep", "ablation", "hyperparameter", "sensitivity", "tuning"]
        ):
            return {
                "title": f"Hyperparameter Ablation Sweep: {task_title[:50]}",
                "hypothesis": hypothesis,
                "objective": "Evaluate model sensitivity across regularization strengths.",
                "function_name": "ablation_parameter_sweep",
                "dataset_id": "synthetic_regression",
                "baseline_method": "Default Parameters",
                "proposed_method": "Optimal Regularization Frontier",
                "metrics_to_evaluate": ["best_alpha", "best_rmse", "best_r2"],
                "evaluation_protocol": "Grid parameter evaluation with fixed random split",
                "parameters": {"alphas": [0.01, 0.1, 1.0, 10.0, 100.0]},
                "random_seed": 42,
            }
        elif any(
            w in t_lower
            for w in ["significance", "hypothesis test", "p-value", "student", "wilcoxon"]
        ):
            return {
                "title": f"Statistical Significance Evaluation: {task_title[:50]}",
                "hypothesis": hypothesis,
                "objective": "Verify whether performance differences are statistically significant.",
                "function_name": "statistical_significance_test",
                "dataset_id": "synthetic_regression",
                "baseline_method": "Baseline Scores",
                "proposed_method": "Proposed Method Scores",
                "metrics_to_evaluate": ["t_statistic", "p_value", "mean_difference"],
                "evaluation_protocol": "Paired two-tailed Student's t-test with bootstrap CI",
                "parameters": {"n_samples": 30, "effect_size": 0.05},
                "random_seed": 42,
            }
        else:
            return {
                "title": f"Linear Benchmark Evaluation: {task_title[:50]}",
                "hypothesis": hypothesis,
                "objective": "Fit and benchmark empirical linear relationship against continuous metrics.",
                "function_name": "linear_regression_benchmark",
                "dataset_id": "synthetic_regression",
                "baseline_method": "Standard Linear Fit",
                "proposed_method": "Ridge Regularized Model",
                "metrics_to_evaluate": ["mae", "rmse", "r2_score"],
                "evaluation_protocol": "75/25 train/test split",
                "parameters": {"alpha": 1.0},
                "random_seed": 42,
            }

    def _parse_json(self, text: str) -> dict[str, Any] | None:
        """Safely extract JSON object from raw LLM output."""
        clean = text.strip()
        try:
            return json.loads(clean)
        except Exception:
            pass

        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if match:
            try:
                return json.loads(match.group(1))
            except Exception:
                pass

        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(clean[start : end + 1])
            except Exception:
                pass

        return None
