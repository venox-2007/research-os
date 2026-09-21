"""LangGraph research orchestration graph assembling planner, researcher, verifier, and critic."""

from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agents.critic import ResearchCritic
from backend.agents.events import TraceCollector, TraceEvent
from backend.agents.planner import ResearchPlanner
from backend.agents.researcher import ResearchWorker
from backend.agents.state import (
    ResearchRunResult,
    ResearchState,
    create_initial_research_state,
)
from backend.agents.tools.registry import ToolRegistry, get_default_tool_registry
from backend.agents.verifier import EvidenceVerifier
from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.core.models import Evidence, ResearchPlan, Source
from backend.llm.base import BaseLLMProvider
from backend.llm.factory import get_llm_provider

logger = get_logger("agents.graph")


def build_research_graph(
    planner: ResearchPlanner,
    researcher: ResearchWorker,
    verifier: EvidenceVerifier,
    critic: ResearchCritic,
) -> Any:
    """Construct and compile the stateful deterministic LangGraph research workflow."""

    async def planner_node(state: ResearchState) -> dict[str, Any]:
        trace = TraceCollector(existing_events=state.get("trace", []))
        question = state["question"]
        discipline = state.get("discipline")
        constraints = state.get("constraints")

        plan = await planner.plan(
            question=question,
            discipline=discipline,
            constraints=constraints,
            trace_collector=trace,
        )

        tasks_dict = [t.model_dump(mode="json") for t in plan.tasks]
        return {
            "status": "planning",
            "plan": plan.model_dump(mode="json"),
            "tasks": tasks_dict,
            "pending_tasks": list(tasks_dict),
            "trace": trace.to_dicts(),
        }

    async def researcher_node(state: ResearchState) -> dict[str, Any]:
        return await researcher.execute_step(state)

    async def verifier_node(state: ResearchState) -> dict[str, Any]:
        return await verifier.verify_step(state)

    async def critic_node(state: ResearchState) -> dict[str, Any]:
        return await critic.critique_step(state)

    async def finish_node(state: ResearchState) -> dict[str, Any]:
        trace = TraceCollector(existing_events=state.get("trace", []))
        trace.record(
            event_type="workflow_complete",
            node_name="finish",
            message=f"Research workflow concluded for: '{state['question']}'",
            details={
                "iterations": state.get("iteration_count", 0),
                "verified_evidence_count": len(state.get("verified_evidence", [])),
                "sources_count": len(state.get("sources", [])),
            },
        )

        last_eval = (
            state.get("critic_evaluations", [])[-1] if state.get("critic_evaluations") else {}
        )

        final_context = {
            "question": state["question"],
            "discipline": state.get("discipline"),
            "iterations": state.get("iteration_count", 0),
            "verified_evidence_count": len(state.get("verified_evidence", [])),
            "sources_count": len(state.get("sources", [])),
            "critic_summary": last_eval.get("reason", "Research successfully conducted."),
            "confidence_score": last_eval.get("confidence_score", 0.8),
            "contradictions": state.get("contradictions", []),
            "research_notes": state.get("research_notes", []),
        }

        return {
            "status": "completed",
            "final_context": final_context,
            "trace": trace.to_dicts(),
        }

    def should_continue(state: ResearchState) -> str:
        """Route conditionally: finish if sufficient/max reached, else refine with researcher."""
        iteration = state.get("iteration_count", 0)
        max_iter = state.get("max_iterations", 3)

        if iteration >= max_iter:
            logger.info("Termination route: hit iteration budget (%d/%d)", iteration, max_iter)
            return "finish"

        critic_evals = state.get("critic_evaluations", [])
        if critic_evals:
            last_critique = critic_evals[-1]
            if last_critique.get("is_sufficient"):
                logger.info("Termination route: research critic deemed evidence sufficient.")
                return "finish"

        pending = state.get("pending_tasks", [])
        if not pending:
            logger.info("Termination route: no remaining pending tasks.")
            return "finish"

        logger.info(
            "Refinement route: continuing research iteration (%d/%d)", iteration + 1, max_iter
        )
        return "researcher"

    workflow = StateGraph(ResearchState)

    # Register workflow nodes
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("verifier", verifier_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("finish", finish_node)

    # Wire deterministic linear path
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "researcher")
    workflow.add_edge("researcher", "verifier")
    workflow.add_edge("verifier", "critic")

    # Wire conditional iteration loop
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "finish": "finish",
            "researcher": "researcher",
        },
    )

    workflow.add_edge("finish", END)

    return workflow.compile()


async def run_research(
    question: str,
    discipline: str | None = None,
    constraints: list[str] | None = None,
    max_iterations: int = 3,
    llm: BaseLLMProvider | None = None,
    tool_registry: ToolRegistry | None = None,
    settings: Settings | None = None,
) -> ResearchRunResult:
    """Execute the full agentic research workflow on a research question."""
    app_settings = settings or get_settings()
    llm_provider = llm or get_llm_provider(settings=app_settings)
    tools = tool_registry or get_default_tool_registry(settings=app_settings)

    planner = ResearchPlanner(llm=llm_provider, settings=app_settings)
    researcher = ResearchWorker(tool_registry=tools, settings=app_settings)
    verifier = EvidenceVerifier(llm=llm_provider, settings=app_settings)
    critic = ResearchCritic(llm=llm_provider, settings=app_settings)

    graph = build_research_graph(
        planner=planner,
        researcher=researcher,
        verifier=verifier,
        critic=critic,
    )

    initial_state = create_initial_research_state(
        question=question,
        discipline=discipline,
        constraints=constraints,
        max_iterations=max_iterations,
    )

    logger.info("Starting ResearchOS workflow for query: '%s'", question[:80])
    final_state: dict[str, Any] = await graph.ainvoke(initial_state)

    # Deserialize into structured result
    plan_obj = None
    if final_state.get("plan"):
        try:
            plan_obj = ResearchPlan(**final_state["plan"])
        except Exception as e:
            logger.warning("Failed deserializing ResearchPlan: %s", e)

    verified_evidence: list[Evidence] = []
    for ev in final_state.get("verified_evidence", []):
        try:
            verified_evidence.append(Evidence(**ev))
        except Exception as e:
            logger.warning("Failed deserializing Evidence: %s", e)

    sources: list[Source] = []
    for s in final_state.get("sources", []):
        try:
            sources.append(Source(**s))
        except Exception as e:
            logger.warning("Failed deserializing Source: %s", e)

    trace_events: list[TraceEvent] = []
    for tr in final_state.get("trace", []):
        try:
            trace_events.append(TraceEvent(**tr))
        except Exception as e:
            logger.warning("Failed deserializing TraceEvent: %s", e)

    last_eval = (
        final_state.get("critic_evaluations", [])[-1]
        if final_state.get("critic_evaluations")
        else {}
    )

    return ResearchRunResult(
        question=final_state.get("question", question),
        status=final_state.get("status", "completed"),
        iteration_count=final_state.get("iteration_count", 1),
        max_iterations=final_state.get("max_iterations", max_iterations),
        plan=plan_obj,
        tasks_completed=len(final_state.get("completed_tasks", [])),
        tasks_total=len(final_state.get("tasks", [])),
        verified_evidence_count=len(verified_evidence),
        sources_count=len(sources),
        verified_evidence=verified_evidence,
        sources=sources,
        contradictions=final_state.get("contradictions", []),
        research_notes=final_state.get("research_notes", []),
        critic_summary=last_eval.get("reason"),
        confidence_score=last_eval.get("confidence_score", 0.8),
        trace=trace_events,
        errors=final_state.get("errors", []),
        final_context=final_state.get("final_context", {}),
    )
