"""Unit tests for ResearchCritic evaluation and refinement decisions."""

from uuid import uuid4

import pytest

from backend.agents.critic import ResearchCritic
from backend.agents.state import create_initial_research_state
from backend.core.models import Evidence


@pytest.mark.asyncio
async def test_critic_enforces_hard_iteration_limit() -> None:
    """Verify critic forces completion when max_iterations is reached regardless of evidence."""
    critic = ResearchCritic()
    state = create_initial_research_state(
        question="How does speculative decoding scale?",
        max_iterations=2,
    )
    # Simulate already at iteration 1 (so next critique is iteration 2 = max_iterations)
    state["iteration_count"] = 1
    state["verified_evidence"] = []  # Even with zero evidence, must stop!

    update = await critic.critique_step(state)
    assert update["iteration_count"] == 2
    assert len(update["critic_evaluations"]) == 1
    eval_record = update["critic_evaluations"][0]
    assert eval_record["is_sufficient"] is True
    assert "maximum iteration limit" in eval_record["reason"].lower()
    assert len(update["pending_tasks"]) == 0


@pytest.mark.asyncio
async def test_critic_proposes_refinement_when_insufficient() -> None:
    """Verify critic generates new tasks when evidence is insufficient and budget remains."""
    critic = ResearchCritic()
    state = create_initial_research_state(
        question="What are the empirical limitations of speculative decoding?",
        max_iterations=3,
    )
    state["iteration_count"] = 0
    state["verified_evidence"] = []  # Zero evidence -> insufficient

    update = await critic.critique_step(state)
    assert update["iteration_count"] == 1
    eval_record = update["critic_evaluations"][0]
    assert eval_record["is_sufficient"] is False
    assert len(update["pending_tasks"]) >= 1
    assert any("speculative decoding" in t["title"].lower() for t in update["pending_tasks"])
    assert len(update["research_notes"]) >= 1


@pytest.mark.asyncio
async def test_critic_approves_when_evidence_sufficient() -> None:
    """Verify critic approves completion when verified evidence is abundant."""
    critic = ResearchCritic()
    state = create_initial_research_state(
        question="What are the benefits of hybrid retrieval?",
        max_iterations=3,
    )
    state["iteration_count"] = 0

    # Provide 3 verified items
    evidence_list = [
        Evidence(
            source_id=uuid4(),
            source_title=f"Paper {i}",
            content=f"Substantial empirical evidence findings item {i} regarding hybrid retrieval.",
        ).model_dump(mode="json")
        for i in range(3)
    ]
    state["verified_evidence"] = evidence_list

    update = await critic.critique_step(state)
    eval_record = update["critic_evaluations"][0]
    assert eval_record["is_sufficient"] is True
    assert eval_record["confidence_score"] >= 0.7
