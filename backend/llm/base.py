"""Abstract base class and models for LLM provider abstraction.

Allows ResearchOS to switch seamlessly between local models (Ollama),
free-tier API providers (Gemini), and offline mock engines without
tight coupling.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field


class LLMMessage(BaseModel):
    """Structured conversational message."""

    role: str = Field(..., description="Message role: system, user, or assistant")
    content: str = Field(..., description="Message text content")


class LLMResponse(BaseModel):
    """Normalized response returned by any LLM provider."""

    content: str = Field(..., description="Generated text content")
    model: str = Field(..., description="Model identifier used for generation")
    usage: dict[str, int] = Field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        description="Token usage statistics",
    )
    finish_reason: str = Field(default="stop", description="Reason generation concluded")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Provider-specific metadata")


class BaseLLMProvider(ABC):
    """Abstract interface for all LLM providers in ResearchOS."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the unique provider name (e.g. 'mock', 'ollama', 'gemini')."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion for a given prompt string."""
        pass

    @abstractmethod
    async def generate_chat(
        self,
        messages: list[LLMMessage],
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response for a sequence of conversation messages."""
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream token chunks for a given prompt."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Check if the provider service or local daemon is reachable."""
        pass
