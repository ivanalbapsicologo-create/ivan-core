"""Interfaz común para todos los providers LLM."""

import asyncio
import json
from abc import ABC, abstractmethod
from typing import Any


class BaseLLMClient(ABC):
    """Contrato mínimo para que el resto del código sea agnóstico al provider."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> str:
        """Devuelve la respuesta como texto plano."""

    async def complete_json(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 8192,
    ) -> dict[str, Any] | list[Any]:
        """Devuelve la respuesta parseada como JSON. Limpia code fences si existen."""
        text = await self.complete(
            prompt, system=system, model=model, max_tokens=max_tokens, temperature=0.0
        )
        return parse_json_safe(text)

    async def batch_complete_json(
        self,
        prompts: list[str],
        *,
        system: str | None = None,
        model: str | None = None,
        max_concurrent: int = 5,
    ) -> list[dict[str, Any] | list[Any] | None]:
        """Lanza prompts en paralelo. None si alguno falla."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded(p: str) -> dict[str, Any] | list[Any] | None:
            async with semaphore:
                try:
                    return await self.complete_json(p, system=system, model=model)
                except Exception:
                    return None

        return await asyncio.gather(*[_bounded(p) for p in prompts])


def parse_json_safe(text: str) -> dict[str, Any] | list[Any]:
    """Parsea JSON limpiando code fences y reparando errores comunes del LLM.

    Estrategia:
    1. Quita code fences markdown
    2. json.loads directo
    3. Si falla, json_repair (recupera trailing commas, comillas, etc.)
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        from json_repair import repair_json
        repaired = repair_json(cleaned, return_objects=True)
        if repaired in ("", None):
            raise
        # repair_json devuelve dict/list/primitive directamente cuando return_objects=True
        if isinstance(repaired, (dict, list)):
            return repaired
        # Último recurso: parsear el resultado como string JSON
        return json.loads(repair_json(cleaned))
