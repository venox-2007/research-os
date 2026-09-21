"""Integration tests verifying LangGraph agent orchestration with the safe experiment engine."""

import pytest

from backend.agents.graph import run_research
from backend.agents.tools.registry import get_default_tool_registry


@pytest.mark.asyncio
async def test_agent_experiment_tool_execution() -> None:
    """Verify agent workflow invokes experiment tools and incorporates experimental evidence."""
    tools = get_default_tool_registry(mock_mode=True)
    assert tools.has_tool("plan_experiment")
    assert tools.has_tool("run_experiment")

    # Directly verify plan_experiment tool execution
    plan_res = await tools.invoke(
        "plan_experiment",
        task_title="Evaluate linear regression benchmark on synthetic data",
        hypothesis="Features are predictive of the continuous response.",
    )
    assert plan_res.success is True
    assert "spec" in plan_res.data
    spec_dict = plan_res.data["spec"]

    # Directly verify run_experiment tool execution
    run_res = await tools.invoke("run_experiment", spec=spec_dict)
    assert run_res.success is True
    assert run_res.data["status"] == "completed"
    assert len(run_res.data["artifacts"]) >= 2
    assert len(run_res.evidence_items) == 1
    assert run_res.evidence_items[0]["extraction_method"] == "safe_experiment_engine"


@pytest.mark.asyncio
async def test_full_research_workflow_with_experiment() -> None:
    """Verify run_research includes experimental results and evidence in output state."""
    tools = get_default_tool_registry(mock_mode=True)

    result = await run_research(
        question="Design and evaluate an empirical benchmark on synthetic regression data",
        discipline="Machine Learning",
        max_iterations=1,
        tool_registry=tools,
    )

    assert result.status == "completed"
    assert result.verified_evidence_count > 0
    # Check that trace records experiment or research execution
    node_names = {t.node_name for t in result.trace if t.node_name}
    assert "planner" in node_names
    assert "researcher" in node_names
