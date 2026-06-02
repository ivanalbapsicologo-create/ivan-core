"""Provider Google Gemini (free tier de Google AI Studio).

Modelo por defecto: `gemini-2.5-flash`.
JSON nativo via `response_mime_type="application/json"`.
"""

import asyncio
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings
from ivan_core.llm.base import BaseLLMClient, account_llm_call


class GeminiClient(BaseLLMClient):
    """Wrapper sobre google-genai.

    El SDK oficial es síncrono pero hace I/O bloqueante; lo envolvemos en
    `asyncio.to_thread` para integrarse en pipelines async sin bloquear el loop.
    """

    def __init__(self) -> None:
        settings = get_settings()
        # Import lazy: evita romper otros providers si la dep no está instalada
        from google import genai  # type: ignore[import-not-found]

        api_key = settings.google_api_key or ""
        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        self.default_model = settings.gemini_model_default

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
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> str:
        return await asyncio.to_thread(
            self._sync_complete,
            prompt,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            json_mode=False,
        )

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 8192,
    ) -> dict[str, Any] | list[Any]:
        text = await asyncio.to_thread(
            self._sync_complete,
            prompt,
            system=system,
            model=model,
            max_tokens=max_tokens,
            temperature=0.0,
            json_mode=True,
        )
        from ivan_core.llm.base import parse_json_safe
        return parse_json_safe(text)

    def _sync_complete(
        self,
        prompt: str,
        *,
        system: str | None,
        model: str | None,
        max_tokens: int,
        temperature: float,
        json_mode: bool,
    ) -> str:
        account_llm_call()
        types = self._genai.types
        config_kwargs: dict[str, Any] = {
            "max_output_tokens": max_tokens,
            "temperature": temperature,
        }
        if system:
            config_kwargs["system_instruction"] = system
        if json_mode:
            config_kwargs["response_mime_type"] = "application/json"

        response = self.client.models.generate_content(
            model=model or self.default_model,
            contents=prompt,
            config=types.GenerateContentConfig(**config_kwargs),
        )
        return response.text or ""
