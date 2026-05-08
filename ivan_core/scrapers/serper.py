"""Cliente Serper.dev para búsquedas Google.

Documentación: https://serper.dev/api

Características:
- Reintentos con backoff exponencial (tenacity)
- Cap de queries por instancia (presupuesto duro)
- Caché en memoria por (query, type, gl, hl, num) — evita repetir dentro de un job
- Soporta type=search | scholar | news | images | videos
"""

import asyncio
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings


class SerperBudgetExceeded(RuntimeError):
    """Se alcanzó el cap de queries permitido por instancia."""


class SerperClient:
    """Cliente asíncrono de Serper.dev con caché y presupuesto.

    Una instancia = un job. Reusa la misma instancia para que la caché
    y el presupuesto compartido apliquen.
    """

    def __init__(self, max_queries: int | None = None) -> None:
        settings = get_settings()
        self.api_key = settings.serper_api_key
        self.base_url = settings.serper_base_url
        self.timeout = settings.http_timeout
        self.max_queries = max_queries if max_queries is not None else settings.serper_max_per_search
        self._consumed = 0
        self._cache: dict[tuple[str, str, str, str, int], dict[str, Any]] = {}

    @property
    def consumed(self) -> int:
        return self._consumed

    @property
    def remaining(self) -> int:
        return max(0, self.max_queries - self._consumed)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def search(
        self,
        query: str,
        *,
        num: int | None = None,
        gl: str = "es",  # geolocalización
        hl: str = "es",  # idioma
        type: str = "search",  # search | images | videos | news | scholar
    ) -> dict[str, Any]:
        """Lanza una query Google vía Serper.

        Devuelve `{"error": ..., "query": ...}` si se supera el presupuesto.
        Aplica caché por (query, type, gl, hl, num).
        """
        settings = get_settings()
        n = num if num is not None else settings.serper_default_num
        cache_key = (query, type, gl, hl, n)

        if cache_key in self._cache:
            return self._cache[cache_key]

        if self._consumed >= self.max_queries:
            return {
                "error": "serper_budget_exceeded",
                "query": query,
                "consumed": self._consumed,
                "max": self.max_queries,
            }

        url = f"{self.base_url}/{type}"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": n, "gl": gl, "hl": hl}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()

        self._consumed += 1
        self._cache[cache_key] = result
        return result

    async def search_many(
        self,
        queries: list[str],
        *,
        num: int | None = None,
        gl: str = "es",
        hl: str = "es",
        type: str = "search",
        max_concurrent: int = 5,
    ) -> list[dict[str, Any]]:
        """Lanza múltiples queries en paralelo con límite de concurrencia.

        Las queries que excedan el presupuesto devuelven `{"error": "serper_budget_exceeded"}`.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def _bounded_search(q: str) -> dict[str, Any]:
            async with semaphore:
                try:
                    return await self.search(q, num=num, gl=gl, hl=hl, type=type)
                except Exception as e:
                    return {"error": str(e), "query": q}

        return await asyncio.gather(*[_bounded_search(q) for q in queries])


def parse_organic_results(serper_response: dict[str, Any]) -> list[dict[str, Any]]:
    """Extrae resultados orgánicos de la respuesta Serper.

    Devuelve lista de dicts con: title, link, snippet, position.
    Para type=scholar Serper usa la clave `organic` también.
    """
    return [
        {
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "position": r.get("position"),
        }
        for r in serper_response.get("organic", [])
    ]
