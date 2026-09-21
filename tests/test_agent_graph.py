"""Integration tests for the LangGraph agentic research graph and execution loop."""

import pytest

from backend.agents.critic import ResearchCritic
from backend.agents.graph import build_research_graph, run_research
from backend.agents.planner import ResearchPlanner
from backend.agents.researcher import ResearchWorker
from backend.agents.tools.registry import get_default_tool_registry
from backend.agents.verifier import EvidenceVerifier


@pytest.mark.asyncio
async def test_build_research_graph_compiles() -> None:
    """Verify graph builder wires all nodes and compiles valid Pregel workflow."""
    tools = get_default_tool_registry(mock_mode=True)
    planner = ResearchPlanner()
    researcher = ResearchWorker(tool_registry=tools)
    verifier = EvidenceVerifier()
    critic = ResearchCritic()

    graph = build_research_graph(
        planner=planner,
        researcher=researcher,
        verifier=verifier,
        critic=critic,
    )
    assert graph is not None


@pytest.mark.asyncio
async def test_run_research_end_to_end() -> None:
    """Verify full autonomous research loop execution with mock mode tools."""
    tools = get_default_tool_registry(mock_mode=True)
    result = await run_research(
        question="What are the computational trade-offs of hybrid RAG vs dense-only retrieval?",
        discipline="Information Retrieval",
        constraints=["focus on latency and reciprocal rank fusion"],
        max_iterations=2,
        tool_registry=tools,
    )

    assert result.status == "completed"
    assert (
        result.question
        == "What are the computational trade-offs of hybrid RAG vs dense-only retrieval?"
    )
    assert result.iteration_count <= 2
    assert result.plan is not None
    assert len(result.plan.tasks) >= 2
    assert result.tasks_completed >= 1
    assert result.verified_evidence_count > 0
    assert len(result.verified_evidence) > 0

    # Lineage coordinates checks
    for ev in result.verified_evidence:
        assert ev.source_id is not None
        assert ev.content is not None
        assert ev.confidence_score >= 0.0

    # Provenance sources checks
    assert result.sources_count > 0
    assert len(result.sources) > 0

    # Trace telemetry checks
    assert len(result.trace) >= 4
    node_names = {t.node_name for t in result.trace if t.node_name}
    assert "planner" in node_names
    assert "researcher" in node_names
    assert "verifier" in node_names
    assert "critic" in node_names
    assert "finish" in node_names

    # Final context summary checks
    assert "question" in result.final_context
    assert result.final_context["verified_evidence_count"] == result.verified_evidence_count


@pytest.mark.asyncio
async def test_run_research_respects_iteration_limit() -> None:
    """Verify research loop never exceeds configured max_iterations."""
    tools = get_default_tool_registry(mock_mode=True)
    result = await run_research(
        question="How does speculative decoding scale with vocabulary size?",
        max_iterations=1,
        tool_registry=tools,
    )
    assert result.iteration_count == 1
    assert result.status == "completed"
