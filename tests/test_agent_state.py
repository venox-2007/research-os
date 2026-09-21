"""Unit tests for agent state models, trace collection, and domain schemas."""

from uuid import uuid4

from backend.agents.events import TraceCollector, TraceEvent
from backend.agents.state import (
    CriticEvaluation,
    ResearchRunResult,
    VerificationResult,
    create_initial_research_state,
)
from backend.core.models import Evidence, ResearchPlan, ResearchTask, Source


def test_create_initial_research_state() -> None:
    """Verify initial state construction defaults and types."""
    state = create_initial_research_state(
        question="How do speculative decoding models verify drafted tokens?",
        discipline="Computer Science",
        constraints=["focus on rejection sampling"],
        max_iterations=4,
    )
    assert state["question"] == "How do speculative decoding models verify drafted tokens?"
    assert state["discipline"] == "Computer Science"
    assert state["constraints"] == ["focus on rejection sampling"]
    assert state["max_iterations"] == 4
    assert state["iteration_count"] == 0
    assert state["status"] == "initialized"
    assert state["tasks"] == []
    assert state["pending_tasks"] == []
    assert state["completed_tasks"] == []
    assert state["retrieved_evidence"] == []
    assert state["verified_evidence"] == []
    assert state["trace"] == []


def test_trace_collector() -> None:
    """Verify trace collector records and formats events accurately."""
    collector = TraceCollector()
    collector.record(
        event_type="node_start",
        node_name="planner",
        message="Starting planning phase",
    )
    collector.record(
        event_type="tool_call",
        node_name="researcher",
        message="Calling search_rag",
        details={"query": "test query"},
    )
    collector.record(
        event_type="error",
        node_name="critic",
        message="Sample warning/error",
        error="Simulation error",
    )

    events = collector.to_dicts()
    assert len(events) == 3
    assert events[0]["node_name"] == "planner"
    assert events[0]["event_type"] == "node_start"

    node_events = collector.get_events_for_node("researcher")
    assert len(node_events) == 1
    assert node_events[0].message == "Calling search_rag"

    errors = collector.get_errors()
    assert len(errors) == 1
    assert errors[0].error == "Simulation error"

    # Test initialization with existing events
    collector2 = TraceCollector(existing_events=events)
    assert len(collector2.events) == 3


def test_verification_result_model() -> None:
    """Verify VerificationResult validation."""
    ev_id = uuid4()
    vr = VerificationResult(
        evidence_id=ev_id,
        chunk_id="chunk_123",
        relevant=True,
        support_status="supported",
        confidence=0.92,
        reason="Provides empirical ablation table",
        is_contradictory=False,
    )
    assert vr.relevant is True
    assert vr.support_status == "supported"
    assert vr.confidence == 0.92
    assert vr.is_contradictory is False


def test_critic_evaluation_model() -> None:
    """Verify CriticEvaluation schema and suggested tasks."""
    ce = CriticEvaluation(
        iteration=1,
        is_sufficient=False,
        confidence_score=0.65,
        reason="Found theoretical basis but missing empirical metrics",
        unanswered_subquestions=["What are the memory bandwidth bounds?"],
        missing_topics=["Empirical benchmarks"],
        recommended_queries=["speculative decoding memory bandwidth"],
        suggested_tasks=[
            {
                "title": "Search speculative decoding latency",
                "task_type": "literature_search",
                "required_evidence": "Latency measurements",
                "search_queries": ["speculative decoding latency benchmark"],
            }
        ],
    )
    assert ce.is_sufficient is False
    assert len(ce.suggested_tasks) == 1
    assert ce.confidence_score == 0.65


def test_research_run_result_serialization() -> None:
    """Verify ResearchRunResult serializes with domain models."""
    source_id = uuid4()
    plan_id = uuid4()

    ev = Evidence(
        source_id=source_id,
        source_title="Seminal Paper",
        content="Our method improves throughput by 2.3x without loss of accuracy.",
        section="Results",
        page_number=4,
        confidence_score=0.95,
        extraction_method="rag_test",
    )
    src = Source(
        id=source_id,
        title="Seminal Paper",
        authors=["Alice", "Bob"],
        year=2024,
    )
    task = ResearchTask(
        plan_id=plan_id,
        title="Search benchmarks",
        task_type="literature_search",
    )
    plan = ResearchPlan(
        id=plan_id,
        question_id=uuid4(),
        objectives=["Measure throughput"],
        tasks=[task],
    )

    result = ResearchRunResult(
        question="What is the speedup factor?",
        status="completed",
        iteration_count=1,
        max_iterations=3,
        plan=plan,
        tasks_completed=1,
        tasks_total=1,
        verified_evidence_count=1,
        sources_count=1,
        verified_evidence=[ev],
        sources=[src],
        confidence_score=0.95,
        trace=[
            TraceEvent(
                event_type="workflow_complete",
                message="Done",
            )
        ],
    )

    data = result.model_dump(mode="json")
    assert data["status"] == "completed"
    assert len(data["verified_evidence"]) == 1
    assert data["verified_evidence"][0]["page_number"] == 4
    assert data["plan"]["objectives"] == ["Measure throughput"]
