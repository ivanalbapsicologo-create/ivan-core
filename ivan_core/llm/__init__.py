"""Capa LLM agnóstica al provider.

Uso:
    from ivan_core.llm import LLMClient        # type alias del provider activo
    from ivan_core.llm import get_llm_client   # factory por env var

    client = get_llm_client()
    text = await client.complete_json("...", system="...")

Provider configurable vía env `LLM_PROVIDER`:
    google      → Gemini (free tier de Google AI Studio) — default
    anthropic   → Claude
    openai      → OpenAI directo
    openrouter  → OpenRouter (compatibilidad OpenAI con cualquier modelo)
"""

from ivan_core.config import get_settings
from ivan_core.llm.base import BaseLLMClient

# `LLMClient` es el alias estándar que usa el resto del código.
LLMClient = BaseLLMClient


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    """Devuelve el cliente correspondiente al provider configurado."""
    name = (provider or get_settings().llm_provider).lower()

    if name == "google":
        from ivan_core.llm.gemini import GeminiClient
        return GeminiClient()
    if name == "anthropic":
        from ivan_core.llm.claude import ClaudeClient
        return ClaudeClient()
    if name == "openai":
        from ivan_core.llm.openai_compat import OpenAICompatClient
        return OpenAICompatClient(use_openrouter=False)
    if name == "openrouter":
        from ivan_core.llm.openai_compat import OpenAICompatClient
        return OpenAICompatClient(use_openrouter=True)
    raise ValueError(f"Unknown LLM_PROVIDER: {name!r}")


# Compatibilidad hacia atrás: el viejo import `from ivan_core.llm import ClaudeClient`
# sigue funcionando aunque ahora se recomienda `get_llm_client()`.
def __getattr__(name: str):
    if name == "ClaudeClient":
        from ivan_core.llm.claude import ClaudeClient
        return ClaudeClient
    raise AttributeError(f"module 'ivan_core.llm' has no attribute {name!r}")


__all__ = ["LLMClient", "get_llm_client"]
