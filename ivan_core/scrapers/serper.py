"""Cliente Serper.dev para búsquedas Google.

Documentación: https://serper.dev/api

Características:
- Reintentos con backoff exponencial (tenacity)
- Cap de queries por búsqueda (presupuesto duro, techo no superable)
- Reparto del presupuesto entre módulos vía `sub_budget(n)`: cada módulo recibe
  un cliente con su propio techo local, pero todos comparten el cap global y la
  caché de la búsqueda, de modo que ningún módulo pueda acaparar el presupuesto.
- Caché en memoria por (query, type, gl, hl, num) — evita repetir dentro de un job
- Reserva el slot ANTES de la petición HTTP: el cap es estricto incluso con
  varias queries concurrentes (sin TOCTOU).
- Soporta type=search | scholar | news | images | videos
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings

CacheKey = tuple[str, str, str, str, int]


class SerperBudgetExceeded(RuntimeError):
    """Se alcanzó el cap de queries permitido por búsqueda."""


@dataclass
class _SerperBudget:
    """Presupuesto compartido entre el cliente principal y sus sub-presupuestos.

    Centraliza el cap global (techo duro), el contador de consumo y la caché,
    para que el reparto por módulo nunca sobrepase el cap de la búsqueda.
    """

    max_queries: int
    consumed: int = 0
    cache: dict[CacheKey, dict[str, Any]] = field(default_factory=dict)


def _budget_error(scope: str, query: str, budget: "_SerperBudget", local: int | None, local_max: int | None) -> dict[str, Any]:
    return {
        "error": "serper_budget_exceeded",
        "scope": scope,
        "query": query,
        "consumed": budget.consumed,
        "max": budget.max_queries,
        "local_consumed": local,
        "local_max": local_max,
    }


class SerperClient:
    """Cliente asíncrono de Serper.dev con caché y presupuesto compartido.

    Una instancia raíz = una búsqueda. Usa `sub_budget(n)` para entregar a cada
    módulo un cliente con techo local propio que comparte cap global y caché.
    """

    def __init__(
        self,
        max_queries: int | None = None,
        *,
        _budget: _SerperBudget | None = None,
        _local_cap: int | None = None,
    ) -> None:
        settings = get_settings()
        self.api_key = settings.serper_api_key
        self.base_url = settings.serper_base_url
        self.timeout = settings.http_timeout
        self.default_num = settings.serper_default_num
        if _budget is not None:
            self._budget = _budget
        else:
            cap = max_queries if max_queries is not None else settings.serper_max_per_search
            self._budget = _SerperBudget(max_queries=max(0, cap))
        self._local_cap = _local_cap
        self._local_consumed = 0

    # ---- Estado del presupuesto global (compartido) ----
    @property
    def consumed(self) -> int:
        return self._budget.consumed

    @property
    def max_queries(self) -> int:
        return self._budget.max_queries

    @property
    def remaining(self) -> int:
        return max(0, self._budget.max_queries - self._budget.consumed)

    # ---- Estado del presupuesto local (este módulo) ----
    @property
    def local_consumed(self) -> int:
        return self._local_consumed

    @property
    def local_remaining(self) -> int:
        if self._local_cap is None:
            return self.remaining
        return max(0, min(self._local_cap - self._local_consumed, self.remaining))

    def sub_budget(self, max_queries: int) -> "SerperClient":
        """Cliente hijo con techo local propio que comparte cap global y caché."""
        return SerperClient(_budget=self._budget, _local_cap=max(0, max_queries))

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

        Devuelve `{"error": "serper_budget_exceeded", ...}` (sin lanzar) si se
        supera el presupuesto global o el local. Aplica caché por
        (query, type, gl, hl, num); los aciertos de caché no consumen presupuesto.
        """
        n = num if num is not None else self.default_num
        cache_key: CacheKey = (query, type, gl, hl, n)

        cached = self._budget.cache.get(cache_key)
        if cached is not None:
            return cached

        # Reserva el slot ANTES de la petición → cap estricto bajo concurrencia.
        if self._budget.consumed >= self._budget.max_queries:
            return _budget_error("global", query, self._budget, self._local_consumed, self._local_cap)
        if self._local_cap is not None and self._local_consumed >= self._local_cap:
            return _budget_error("local", query, self._budget, self._local_consumed, self._local_cap)

        self._budget.consumed += 1
        self._local_consumed += 1

        url = f"{self.base_url}/{type}"
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}
        payload = {"q": query, "num": n, "gl": gl, "hl": hl}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
        except Exception:
            # Devuelve el slot reservado: un fallo transitorio no debe quemar presupuesto.
            self._budget.consumed -= 1
            self._local_consumed -= 1
            raise

        self._budget.cache[cache_key] = result
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

        Las queries que excedan el presupuesto devuelven
        `{"error": "serper_budget_exceeded", ...}`.
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
    if not isinstance(serper_response, dict):
        return []
    organic = serper_response.get("organic")
    if not isinstance(organic, list):
        return []
    return [
        {
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", ""),
            "position": r.get("position"),
        }
        for r in organic
        if isinstance(r, dict)
    ]
