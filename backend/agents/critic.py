"""Autonomous Research Critic node evaluating evidence sufficiency and orchestrating refinement loops."""

import json
import re
from typing import Any
from uuid import uuid4

from backend.agents.events import TraceCollector
from backend.agents.state import CriticEvaluation, ResearchState
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import ResearchTask
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider

logger = get_logger("agents.critic")

CRITIC_SYSTEM_PROMPT = """You are the Senior Research Critic for ResearchOS, an autonomous research engineer.
Your job is to objectively evaluate whether the current verified evidence is sufficient to rigorously answer the user's research question.

Evaluate:
1. Did the evidence answer the core question?
2. Are key quantitative baselines or empirical comparisons present?
3. Are there unaddressed contradictions or missing perspectives?
4. Is additional literature or data required?

Output valid JSON ONLY matching this schema:
{
  "is_sufficient": true,
  "confidence_score": 0.88,
  "reason": "Clear explanation of evaluation",
  "unanswered_subquestions": [],
  "weak_evidence_notes": [],
  "missing_topics": [],
  "recommended_queries": [],
  "suggested_tasks": [
    {
      "title": "Investigate ablation studies on ...",
      "task_type": "literature_search",
      "required_evidence": "Ablation tables comparing component contributions",
      "search_queries": ["query 1", "query 2"]
    }
  ]
}
"""


class ResearchCritic:
    """Evaluates research completeness and determines whether to terminate or refine."""

    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm or get_llm_provider(settings=self.settings)

    async def critique_step(self, state: ResearchState) -> dict[str, Any]:
        """Assess verified evidence and formulate refinement tasks if insufficient."""
        current_iteration = state.get("iteration_count", 0) + 1
        max_iterations = state.get("max_iterations", self.settings.max_research_iterations)

        trace = TraceCollector(existing_events=state.get("trace", []))
        trace.record(
            event_type="node_start",
            node_name="critic",
            message=f"Starting critique evaluation for iteration {current_iteration}/{max_iterations}",
        )

        question = state.get("question", "")
        verified_evidence = state.get("verified_evidence", [])
        contradictions = state.get("contradictions", [])
        critic_evaluations = list(state.get("critic_evaluations", []))
        pending_tasks = list(state.get("pending_tasks", []))
        all_tasks = list(state.get("tasks", []))
        research_notes = list(state.get("research_notes", []))

        # Check hard iteration limit
        if current_iteration >= max_iterations:
            logger.info(
                "Reached maximum research iterations (%d). Forcing completion.", max_iterations
            )
            evaluation = CriticEvaluation(
                iteration=current_iteration,
                is_sufficient=True,
                confidence_score=min(0.5 + (len(verified_evidence) * 0.08), 0.95),
                reason=f"Reached maximum iteration limit ({max_iterations}). Finalizing research with {len(verified_evidence)} verified evidence items.",
                unanswered_subquestions=[],
                weak_evidence_notes=[],
                missing_topics=[],
                recommended_queries=[],
                suggested_tasks=[],
            )
        else:
            evaluation = await self._evaluate_evidence(
                question=question,
                verified_evidence=verified_evidence,
                contradictions=contradictions,
                iteration=current_iteration,
            )

        critic_evaluations.append(evaluation.model_dump(mode="json"))

        # If critic determined insufficient and we have budget, spawn refinement tasks
        new_tasks_added = 0
        if not evaluation.is_sufficient and current_iteration < max_iterations:
            if evaluation.suggested_tasks:
                plan_id = None
                if state.get("plan"):
                    plan_id = state["plan"].get("id")

                for st in evaluation.suggested_tasks[:2]:  # Limit to top 2 tasks per loop
                    task_obj = ResearchTask(
                        plan_id=plan_id if isinstance(plan_id, uuid4().__class__) else uuid4(),
                        title=st.get("title", f"Refinement query on {question[:30]}"),
                        task_type=st.get("task_type", "literature_search"),
                        assigned_agent="researcher",
                        status="pending",
                        output={
                            "required_evidence": st.get("required_evidence", ""),
                            "search_queries": st.get("search_queries", [question]),
                        },
                    )
                    task_dict = task_obj.model_dump(mode="json")
                    all_tasks.append(task_dict)
                    pending_tasks.append(task_dict)
                    new_tasks_added += 1

        # Synthesize research note for this iteration
        note = (
            f"Iteration {current_iteration}: {len(verified_evidence)} verified items, "
            f"Confidence: {evaluation.confidence_score:.2f}, Sufficient: {evaluation.is_sufficient}. "
            f"{evaluation.reason}"
        )
        research_notes.append(note)

        trace.record(
            event_type="critique_complete",
            node_name="critic",
            message=f"Critique complete: is_sufficient={evaluation.is_sufficient} (confidence={evaluation.confidence_score:.2f})",
            details={
                "iteration": current_iteration,
                "is_sufficient": evaluation.is_sufficient,
                "confidence_score": evaluation.confidence_score,
                "new_tasks_spawned": new_tasks_added,
                "reason": evaluation.reason,
            },
        )

        trace.record(
            event_type="node_complete",
            node_name="critic",
            message=f"Critique finished. Next state: {'finish' if evaluation.is_sufficient else 'refine'}",
        )

        return {
            "status": "critiquing",
            "iteration_count": current_iteration,
            "critic_evaluations": critic_evaluations,
            "tasks": all_tasks,
            "pending_tasks": pending_tasks,
            "research_notes": research_notes,
            "trace": trace.to_dicts(),
        }

    async def _evaluate_evidence(
        self,
        question: str,
        verified_evidence: list[dict[str, Any]],
        contradictions: list[str],
        iteration: int,
    ) -> CriticEvaluation:
        """Call LLM critic with fallback heuristics for testing and robustness."""
        # Use heuristic evaluation for testing or mock LLM provider
        if self.settings.app_env == "testing" or self.settings.llm_provider == "mock":
            return self._heuristic_critique(question, verified_evidence, contradictions, iteration)

        evidence_snippets = "\n---\n".join(
            f"[{e.get('source_title', 'Unknown')} | {e.get('provenance_summary', '')}]: {e.get('content', '')[:300]}"
            for e in verified_evidence[:8]
        )
        contra_text = "\n".join(contradictions) if contradictions else "None detected."

        prompt = (
            f"Research Question: {question}\n\n"
            f"Verified Evidence Items ({len(verified_evidence)} total):\n{evidence_snippets}\n\n"
            f"Contradictions:\n{contra_text}\n\n"
            f"Current Iteration: {iteration}\n"
        )

        try:
            response = await self.llm.generate(
                prompt=prompt,
                system_prompt=CRITIC_SYSTEM_PROMPT,
            )
            parsed = self._parse_json_response(response.content)
            if parsed:
                return CriticEvaluation(
                    iteration=iteration,
                    is_sufficient=bool(parsed.get("is_sufficient", True)),
                    confidence_score=float(parsed.get("confidence_score", 0.8)),
                    reason=str(parsed.get("reason", "Evaluated by research critic.")),
                    unanswered_subquestions=list(parsed.get("unanswered_subquestions", [])),
                    weak_evidence_notes=list(parsed.get("weak_evidence_notes", [])),
                    missing_topics=list(parsed.get("missing_topics", [])),
                    recommended_queries=list(parsed.get("recommended_queries", [])),
                    suggested_tasks=list(parsed.get("suggested_tasks", [])),
                )
        except Exception as exc:
            logger.warning("LLM critic evaluation failed: %s. Using heuristic evaluation.", exc)

        return self._heuristic_critique(question, verified_evidence, contradictions, iteration)

    def _heuristic_critique(
        self,
        question: str,
        verified_evidence: list[dict[str, Any]],
        contradictions: list[str],
        iteration: int,
    ) -> CriticEvaluation:
        """Deterministic heuristic critique for test environments."""
        evidence_count = len(verified_evidence)

        # In iteration 1, if we have at least 2 items, consider it sufficient for speed/offline or refine once
        is_sufficient = evidence_count >= 2

        confidence = min(0.4 + (evidence_count * 0.15), 0.95)
        reason = (
            f"Retrieved {evidence_count} verified evidence items. Core methodology and empirical findings identified."
            if is_sufficient
            else f"Retrieved {evidence_count} items. Insufficient depth to thoroughly answer '{question}'."
        )

        suggested_tasks = []
        if not is_sufficient:
            suggested_tasks = [
                {
                    "title": f"Deepen literature search on: {question[:100]}",
                    "task_type": "literature_search",
                    "required_evidence": "Empirical benchmarks and comparative evaluations",
                    "search_queries": [f"{question} empirical results", f"{question} benchmarks"],
                }
            ]

        return CriticEvaluation(
            iteration=iteration,
            is_sufficient=is_sufficient,
            confidence_score=confidence,
            reason=reason,
            unanswered_subquestions=[] if is_sufficient else ["Detailed ablation benchmarks"],
            weak_evidence_notes=[],
            missing_topics=[] if is_sufficient else ["Comparative baselines"],
            recommended_queries=[f"{question} empirical results"] if not is_sufficient else [],
            suggested_tasks=suggested_tasks,
        )

    def _parse_json_response(self, raw_text: str) -> dict[str, Any] | None:
        """Safely parse JSON response from LLM."""
        clean = raw_text.strip()
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
