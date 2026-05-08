"""Provider OpenAI-compatible (sirve para OpenAI directo y para OpenRouter)."""

from typing import Any

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings
from ivan_core.llm.base import BaseLLMClient


class OpenAICompatClient(BaseLLMClient):
    """Cliente para cualquier API compatible con OpenAI.

    - OpenAI directo: base_url=None, api_key=OPENAI_API_KEY
    - OpenRouter: base_url=https://openrouter.ai/api/v1, api_key=OPENROUTER_API_KEY
      Modelo: prefijado por provider, ej. `google/gemini-2.5-flash`,
      `anthropic/claude-haiku-4.5`, `openai/gpt-4o-mini`.
    """

    def __init__(self, *, use_openrouter: bool = False) -> None:
        settings = get_settings()
        if use_openrouter:
            api_key = settings.openrouter_api_key or ""
            base_url = settings.openrouter_base_url
            self.default_model = settings.openrouter_model_default
        else:
            api_key = settings.openai_api_key or ""
            base_url = settings.openai_base_url
            self.default_model = settings.openai_model_default

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url or None,
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> dict[str, Any] | list[Any]:
        """Pide JSON usando `response_format={"type": "json_object"}` cuando aplica."""
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=model or self.default_model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=0.0,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content or ""

        from ivan_core.llm.base import parse_json_safe
        return parse_json_safe(text)
