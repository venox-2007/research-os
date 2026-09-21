"""Unit tests for ResearchPlanner and plan decomposition."""

import pytest

from backend.agents.events import TraceCollector
from backend.agents.planner import ResearchPlanner
from backend.llm.base import LLMResponse
from backend.llm.mock import MockLLMProvider


class StructuredMockLLM(MockLLMProvider):
    """Mock LLM returning valid JSON research plans."""

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        content = """
        {
          "objectives": [
            "Assess retrieval recall and latency trade-offs",
            "Examine memory footprint of sparse vs dense indexes"
          ],
          "tasks": [
            {
              "title": "Search hybrid retrieval latency benchmarks",
              "task_type": "literature_search",
              "required_evidence": "Latency tables comparing BM25, FAISS, and RRF",
              "search_queries": ["hybrid rag latency", "bm25 faiss benchmarks"]
            },
            {
              "title": "Retrieve memory scaling data",
              "task_type": "rag_query",
              "required_evidence": "RAM consumption per 1M vectors",
              "search_queries": ["vector index memory footprint"]
            }
          ],
          "stopping_criteria": "Found both latency and memory metrics."
        }
        """
        return LLMResponse(content=content, model="mock-structured")


class UnstructuredMockLLM(MockLLMProvider):
    """Mock LLM returning plain text to test fallback heuristic plan parsing."""

    async def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        return LLMResponse(content="I think you should look into hybrid RAG.", model="mock-plain")


@pytest.mark.asyncio
async def test_planner_with_structured_json() -> None:
    """Verify planner parses structured JSON LLM output into atomic tasks."""
    llm = StructuredMockLLM()
    planner = ResearchPlanner(llm=llm)
    trace = TraceCollector()

    plan = await planner.plan(
        question="What are the trade-offs of hybrid RAG?",
        discipline="Computer Science",
        constraints=["Focus on latency"],
        trace_collector=trace,
    )

    assert len(plan.objectives) == 2
    assert len(plan.tasks) == 2
    assert plan.tasks[0].task_type == "literature_search"
    assert plan.tasks[0].title == "Search hybrid retrieval latency benchmarks"
    assert plan.tasks[1].task_type == "rag_query"
    assert len(trace.events) >= 2


@pytest.mark.asyncio
async def test_planner_fallback_on_unstructured_output() -> None:
    """Verify planner activates deterministic domain fallback plan when LLM is unstructured."""
    llm = UnstructuredMockLLM()
    planner = ResearchPlanner(llm=llm)

    plan = await planner.plan(
        question="How do transformer attention mechanisms scale with context length?",
    )

    assert plan is not None
    assert len(plan.tasks) == 3
    assert any(t.task_type == "literature_search" for t in plan.tasks)
    assert any(t.task_type == "rag_query" for t in plan.tasks)
    assert any(t.task_type == "critique" for t in plan.tasks)
