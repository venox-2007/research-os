"""Tests for LLM provider abstraction and mock provider."""

import pytest

from backend.core.config import Settings
from backend.llm.base import BaseLLMProvider, LLMMessage
from backend.llm.factory import get_llm_provider
from backend.llm.mock import MockLLMProvider


@pytest.mark.asyncio
async def test_mock_llm_provider_direct(mock_llm: MockLLMProvider) -> None:
    """Verify MockLLMProvider produces deterministic responses offline."""
    assert isinstance(mock_llm, BaseLLMProvider)
    assert mock_llm.provider_name == "mock"
    assert await mock_llm.is_available() is True

    # Test single prompt generation
    prompt = "Summarize latest attention mechanisms"
    response = await mock_llm.generate(prompt=prompt)
    assert response.model == "mock-gpt-4o-mini"
    assert "Test synthesis response" in response.content
    assert response.usage["total_tokens"] > 0
    assert response.finish_reason == "stop"


@pytest.mark.asyncio
async def test_mock_llm_chat_and_stream(mock_llm: MockLLMProvider) -> None:
    """Verify chat message history handling and streaming in MockLLMProvider."""
    messages = [
        LLMMessage(role="system", content="You are a research assistant."),
        LLMMessage(role="user", content="Explain RAG."),
    ]
    chat_response = await mock_llm.generate_chat(messages=messages)
    assert "Test synthesis response" in chat_response.content

    # Verify streaming
    chunks = []
    async for chunk in mock_llm.generate_stream(prompt="Stream test"):
        chunks.append(chunk)
    assert len(chunks) > 0
    reconstructed = "".join(chunks).strip()
    assert reconstructed == "Test synthesis response"


def test_llm_factory_mock() -> None:
    """Verify factory instantiates mock provider when configured."""
    settings = Settings(llm_provider="mock", local_model_name="test-model")
    provider = get_llm_provider(settings)
    assert isinstance(provider, BaseLLMProvider)
    assert provider.provider_name == "mock"


def test_llm_factory_ollama_fallback() -> None:
    """Verify factory handles ollama configuration safely in M1."""
    settings = Settings(llm_provider="ollama", local_model_name="llama3.2")
    provider = get_llm_provider(settings)
    assert isinstance(provider, BaseLLMProvider)
    assert provider.provider_name == "mock"


def test_llm_factory_unknown_fallback() -> None:
    """Verify factory safely falls back to mock for unknown provider names."""
    settings = Settings(llm_provider="non_existent_provider_xyz")
    provider = get_llm_provider(settings)
    assert isinstance(provider, BaseLLMProvider)
    assert provider.provider_name == "mock"
