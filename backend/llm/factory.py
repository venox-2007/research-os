"""Factory for initializing LLM providers based on application configuration."""

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.llm.base import BaseLLMProvider
from backend.llm.mock import MockLLMProvider

logger = get_logger("llm.factory")


def get_llm_provider(settings: Settings | None = None) -> BaseLLMProvider:
    """Instantiate and return the configured LLM provider.

    Args:
        settings: Optional application settings; falls back to cached settings.

    Returns:
        Configured BaseLLMProvider instance.
    """
    app_settings = settings or get_settings()
    provider_type = app_settings.llm_provider.lower().strip()

    if provider_type == "mock":
        logger.info("Initializing MockLLMProvider (deterministic, zero-cost, offline)")
        return MockLLMProvider(model_name=app_settings.local_model_name)

    if provider_type == "ollama":
        # Future M2/M4 Ollama integration
        logger.info(
            "Ollama provider configured for model '%s' at %s (falling back to Mock in M1)",
            app_settings.local_model_name,
            app_settings.ollama_base_url,
        )
        return MockLLMProvider(
            default_response=f"Ollama[{app_settings.local_model_name}] simulated response.",
            model_name=app_settings.local_model_name,
        )

    if provider_type == "gemini":
        logger.info("Gemini free-tier provider configured (falling back to Mock in M1)")
        return MockLLMProvider(
            default_response="Gemini simulated free-tier response.",
            model_name="gemini-1.5-flash",
        )

    logger.warning("Unknown LLM provider '%s'. Defaulting to MockLLMProvider", provider_type)
    return MockLLMProvider(model_name=app_settings.local_model_name)
