"""Mock LLM Provider for zero-cost, deterministic, offline testing.

Operates without network requests, external API keys, or GPU resources.
"""

from collections.abc import AsyncIterator
from typing import Any

from backend.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class MockLLMProvider(BaseLLMProvider):
    """Deterministic mock provider for unit testing and offline development."""

    def __init__(
        self,
        default_response: str | None = None,
        model_name: str = "mock-gpt-4o-mini",
    ) -> None:
        self.default_response = (
            default_response or "Mock LLM Response: Synthesis complete with 0 API cost."
        )
        self.model_name = model_name

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        content = (
            f"{self.default_response} [Prompt: {prompt[:30]}...]"
            if len(prompt) > 30
            else f"{self.default_response} [Prompt: {prompt}]"
        )
        return LLMResponse(
            content=content,
            model=self.model_name,
            usage={
                "prompt_tokens": len(prompt.split()),
                "completion_tokens": len(content.split()),
                "total_tokens": len(prompt.split()) + len(content.split()),
            },
            finish_reason="stop",
            metadata={"system_prompt": system_prompt},
        )

    async def generate_chat(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        last_msg = messages[-1].content if messages else "empty"
        return await self.generate(prompt=last_msg, **kwargs)

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        words = self.default_response.split()
        for word in words:
            yield f"{word} "

    async def is_available(self) -> bool:
        """Mock provider is always available offline."""
        return True
