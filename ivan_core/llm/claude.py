"""Cliente Claude con helpers para JSON mode y batching."""

import asyncio
import json
from typing import Any

from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings


class ClaudeClient:
    """Wrapper sobre AsyncAnthropic con utilidades comunes."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.default_model = settings.claude_model_default

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
        """Llamada simple, devuelve texto."""
        response = await self.client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text  # type: ignore[union-attr]

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 2048,
    ) -> dict[str, Any] | list[Any]:
        """Llamada que espera JSON. Parsea y limpia code fences si los hay."""
        text = await self.complete(
            prompt, system=system, model=model, max_tokens=max_tokens, temperature=0.0
        )
        return _parse_json_safe(text)

    async def batch_complete_json(
        self,
        prompts: list[str],
        *,
        system: str | None = None,
        model: str | None = None,
        max_concurrent: int = 5,
    ) -> list[dict[str, Any] | list[Any] | None]:
        """Lanza múltiples prompts en paralelo. None si falla alguno."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded(p: str) -> dict[str, Any] | list[Any] | None:
            async with semaphore:
                try:
                    return await self.complete_json(p, system=system, model=model)
                except Exception:
                    return None

        return await asyncio.gather(*[_bounded(p) for p in prompts])


def _parse_json_safe(text: str) -> dict[str, Any] | list[Any]:
    """Parsea JSON limpiando code fences y posibles preámbulos."""
    cleaned = text.strip()
    # Quitar fences markdown
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Quitar primera línea (```json o ```)
        lines = lines[1:]
        # Quitar última línea si es ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)
