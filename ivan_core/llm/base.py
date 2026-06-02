"""Interfaz común para todos los providers LLM."""

import asyncio
import contextvars
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Tope de llamadas LLM por búsqueda (red de seguridad para la cuota free).
# Se almacena en un contextvar: runner.set_llm_budget(N) lo fija al inicio de
# una búsqueda y se comparte con las tareas hijas (scoring/normalize/etc.).
# ----------------------------------------------------------------------------
_llm_budget: contextvars.ContextVar[dict[str, int] | None] = contextvars.ContextVar(
    "llm_budget", default=None
)


class LLMBudgetExceeded(RuntimeError):
    """Se superó el tope de llamadas LLM permitido por búsqueda."""


def set_llm_budget(max_calls: int | None) -> None:
    """Fija el tope de llamadas LLM del contexto actual (None/<=0 lo desactiva)."""
    _llm_budget.set({"count": 0, "max": max_calls} if max_calls and max_calls > 0 else None)


def llm_calls_used() -> int:
    b = _llm_budget.get()
    return b["count"] if b else 0


def account_llm_call() -> None:
    """Cuenta una llamada LLM; lanza LLMBudgetExceeded si supera el tope.

    Los callers (normalize/scoring/competitors) capturan excepciones y caen a un
    fallback determinista, de modo que el tope degrada con elegancia."""
    b = _llm_budget.get()
    if b is None:
        return
    if b["count"] >= b["max"]:
        raise LLMBudgetExceeded(f"LLM call budget exceeded ({b['max']} calls/search)")
    b["count"] += 1


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
    """Parsea JSON tolerante a errores del LLM.

    Nunca lanza excepción: si todo falla devuelve dict vacío. El caller decide
    cómo manejar el fallo (default-fallback, warning, etc.).
    """
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    if not cleaned:
        return {}

    # 1. Intento directo
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. json-repair (maneja trailing commas, comillas mal, etc.)
    try:
        from json_repair import repair_json
        repaired = repair_json(cleaned)
        if repaired:
            return json.loads(repaired)
    except Exception as e:
        logger.warning("json_repair failed: %s", e)

    # 3. Último recurso: extraer el primer objeto/array balanceado
    extracted = _extract_first_balanced(cleaned)
    if extracted:
        try:
            return json.loads(extracted)
        except json.JSONDecodeError:
            pass

    logger.error(
        "parse_json_safe: irrecoverable JSON. First 500 chars: %r",
        cleaned[:500],
    )
    return {}


def _extract_first_balanced(text: str) -> str | None:
    """Extrae el primer { ... } o [ ... ] con paréntesis balanceados."""
    for open_c, close_c in (("{", "}"), ("[", "]")):
        start = text.find(open_c)
        if start < 0:
            continue
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            ch = text[i]
            if escape:
                escape = False
                continue
            if ch == "\\":
                escape = True
                continue
            if ch == '"' and not escape:
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == open_c:
                depth += 1
            elif ch == close_c:
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None
