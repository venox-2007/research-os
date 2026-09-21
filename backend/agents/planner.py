"""Autonomous Research Planner decomposing scientific queries into prioritized tasks."""

import json
import re
from typing import Any
from uuid import uuid4

from backend.agents.events import TraceCollector
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import ResearchPlan, ResearchTask
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider

logger = get_logger("agents.planner")

PLANNER_SYSTEM_PROMPT = """You are the Lead Scientific Planner for ResearchOS, an autonomous research engineer.
Your job is to analyze a research question and create a rigorous, ordered, non-redundant research plan.
Decompose the query into 3 to 6 explicit, prioritized tasks.
For each task, specify:
1. title: clear action-oriented objective
2. task_type: one of 'literature_search', 'paper_ingestion', 'rag_query', 'critique'
3. required_evidence: what specific empirical data, benchmark, or theoretical proof is needed
4. search_queries: 1-3 targeted search queries

Respond ONLY in valid JSON matching this schema:
{
  "objectives": ["primary objective 1", "primary objective 2"],
  "tasks": [
    {
      "title": "Search foundational literature on ...",
      "task_type": "literature_search",
      "required_evidence": "Definitions, core mathematical formulation, or baseline methods",
      "search_queries": ["query 1", "query 2"]
    }
  ],
  "stopping_criteria": "Sufficient empirical evidence found covering..."
}
"""


class ResearchPlanner:
    """Generates structured, verifiable research plans using the LLM abstraction."""

    def __init__(
        self,
        llm: BaseLLMProvider | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.llm = llm or get_llm_provider(settings=self.settings)

    async def plan(
        self,
        question: str,
        discipline: str | None = None,
        constraints: list[str] | None = None,
        trace_collector: TraceCollector | None = None,
    ) -> ResearchPlan:
        """Create a structured ResearchPlan with atomic tasks for the given question."""
        user_prompt = f"Research Question: {question}\n"
        if discipline:
            user_prompt += f"Discipline: {discipline}\n"
        if constraints:
            user_prompt += f"Constraints: {', '.join(constraints)}\n"

        logger.info("Generating research plan for: '%s'", question[:80])
        if trace_collector:
            trace_collector.record(
                event_type="node_start",
                node_name="planner",
                message=f"Starting research planning for: '{question}'",
            )

        llm_response = await self.llm.generate(
            prompt=user_prompt,
            system_prompt=PLANNER_SYSTEM_PROMPT,
        )

        plan_data = self._parse_plan_json(llm_response.content, question)

        plan_id = uuid4()
        tasks: list[ResearchTask] = []
        for i, t in enumerate(plan_data.get("tasks", [])):
            task_type = t.get("task_type", "literature_search")
            if task_type not in {
                "literature_search",
                "paper_ingestion",
                "rag_query",
                "critique",
            }:
                task_type = "literature_search"

            task_obj = ResearchTask(
                plan_id=plan_id,
                title=t.get("title", f"Task {i + 1}"),
                task_type=task_type,
                assigned_agent="researcher",
                status="pending",
                output={
                    "required_evidence": t.get("required_evidence", ""),
                    "search_queries": t.get("search_queries", [question]),
                },
            )
            tasks.append(task_obj)

        research_plan = ResearchPlan(
            id=plan_id,
            question_id=uuid4(),
            objectives=plan_data.get("objectives", [question]),
            tasks=tasks,
            status="created",
        )

        logger.info("Generated plan with %d tasks", len(tasks))
        if trace_collector:
            trace_collector.record(
                event_type="node_complete",
                node_name="planner",
                message=f"Plan generated with {len(tasks)} tasks",
                details={
                    "tasks_count": len(tasks),
                    "objectives": research_plan.objectives,
                },
            )

        return research_plan

    def _parse_plan_json(self, raw_content: str, fallback_query: str) -> dict[str, Any]:
        """Safely extract and parse JSON from LLM output with deterministic fallback."""
        clean = raw_content.strip()

        # Direct JSON parse
        try:
            return json.loads(clean)
        except Exception:
            pass

        # Markdown ```json block extraction
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except Exception:
                pass

        # Heuristic JSON bracket extraction
        start_idx = clean.find("{")
        end_idx = clean.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            try:
                return json.loads(clean[start_idx : end_idx + 1])
            except Exception:
                pass

        # Deterministic domain-tailored fallback plan
        logger.warning("Could not parse LLM JSON plan. Employing structured fallback plan.")
        return {
            "objectives": [
                f"Identify primary empirical findings regarding {fallback_query}",
                "Extract quantitative benchmarks and comparative evidence",
                "Synthesize conflicting outcomes and methodological constraints",
            ],
            "tasks": [
                {
                    "title": f"Search foundational literature on {fallback_query}",
                    "task_type": "literature_search",
                    "required_evidence": "Core methodology, theoretical framework, or baseline techniques",
                    "search_queries": [fallback_query, f"{fallback_query} methodology"],
                },
                {
                    "title": f"Retrieve empirical benchmarks for {fallback_query}",
                    "task_type": "rag_query",
                    "required_evidence": "Metrics, ablation studies, and evaluation tables",
                    "search_queries": [
                        f"{fallback_query} evaluation",
                        f"{fallback_query} benchmark",
                    ],
                },
                {
                    "title": f"Identify limitations and contradictory findings for {fallback_query}",
                    "task_type": "critique",
                    "required_evidence": "Reported failure cases, limitations, and conflicting studies",
                    "search_queries": [
                        f"{fallback_query} limitations",
                        f"{fallback_query} trade-offs",
                    ],
                },
            ],
            "stopping_criteria": "Identified peer-reviewed literature with verified metrics and acknowledged limitations.",
        }
