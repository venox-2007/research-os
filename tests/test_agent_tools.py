"""Unit tests for agent tools, ToolRegistry, and tool dispatch."""

import pytest

from backend.agents.tools.academic_search import (
    ArxivSearchTool,
    SemanticScholarSearchTool,
)
from backend.agents.tools.rag_search import RAGSearchTool
from backend.agents.tools.registry import ToolRegistry, get_default_tool_registry
from backend.agents.tools.web_search import WebSearchTool


@pytest.mark.asyncio
async def test_tool_registry_lifecycle() -> None:
    """Verify ToolRegistry registers, discovers, inspects, and invokes tools."""
    registry = ToolRegistry()
    arxiv_tool = ArxivSearchTool(mock_mode=True)
    registry.register(arxiv_tool)

    assert registry.has_tool("search_arxiv")
    assert not registry.has_tool("nonexistent")
    assert registry.get("search_arxiv") is arxiv_tool

    manifest = registry.list_tools()
    assert len(manifest) == 1
    assert manifest[0]["name"] == "search_arxiv"
    assert "parameters" in manifest[0]

    # Test invoking registered tool
    result = await registry.invoke("search_arxiv", query="state space models", limit=2)
    assert result.success is True
    assert result.tool_name == "search_arxiv"
    assert len(result.evidence_items) > 0

    # Test invoking nonexistent tool
    bad_res = await registry.invoke("missing_tool", query="test")
    assert bad_res.success is False
    assert "Unrecognized tool" in (bad_res.error or "")


@pytest.mark.asyncio
async def test_default_tool_registry() -> None:
    """Verify default tool registry sets up all Milestone 2/3/4 research tools."""
    registry = get_default_tool_registry(mock_mode=True)
    assert registry.has_tool("search_rag")
    assert registry.has_tool("search_arxiv")
    assert registry.has_tool("search_semantic_scholar")
    assert registry.has_tool("ingest_paper")
    assert registry.has_tool("web_search")


@pytest.mark.asyncio
async def test_web_search_tool_mock_mode() -> None:
    """Verify WebSearchTool returns evidence in deterministic mock mode."""
    tool = WebSearchTool(mock_mode=True)
    result = await tool.run(query="sparse autoencoders", limit=2)
    assert result.success is True
    assert len(result.evidence_items) > 0
    assert result.data["provider"] == "mock_offline"


@pytest.mark.asyncio
async def test_academic_search_mock_mode() -> None:
    """Verify ArxivSearchTool and SemanticScholarSearchTool produce verified citations in mock mode."""
    arxiv = ArxivSearchTool(mock_mode=True)
    s2 = SemanticScholarSearchTool(mock_mode=True)

    res_arxiv = await arxiv.run(query="transformer attention", limit=2)
    assert res_arxiv.success is True
    assert len(res_arxiv.evidence_items) > 0
    assert res_arxiv.evidence_items[0]["extraction_method"] == "arxiv_search_mock"

    res_s2 = await s2.run(query="contrastive learning", limit=1)
    assert res_s2.success is True
    assert len(res_s2.evidence_items) > 0
    assert res_s2.evidence_items[0]["extraction_method"] == "semantic_scholar_mock"


@pytest.mark.asyncio
async def test_rag_search_tool() -> None:
    """Verify RAGSearchTool executes safely and returns evidence structure."""
    tool = RAGSearchTool(mock_mode=True)
    result = await tool.run(query="hybrid retrieval", top_k=2)
    assert result.success is True
    assert "evidence" in result.data
