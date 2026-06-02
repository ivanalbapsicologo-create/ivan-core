"""Verificación de empresas contra OpenCorporates (registro mercantil global).

API gratuita sin key (rate limit ~500 req/mes IP). El resultado se cachea por el
caller (TTL 90d) para no quemar la cuota.

Vive en ivan-core (no en el backend del job) porque también lo usa la Vercel
Function `api/admin_competitors.py`, que NO puede importar de `backend/`
(excluido por .vercelignore). ivan-core sí se instala en Vercel.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

OPENCORPORATES_BASE = "https://api.opencorporates.com/v0.4"
TTL_DAYS = 90


def _is_cache_fresh(cached: dict[str, Any] | None) -> bool:
    if not cached:
        return False
    checked_at = cached.get("checked_at")
    if not checked_at:
        return False
    try:
        ts = datetime.fromisoformat(checked_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return False
    return datetime.now(timezone.utc) - ts < timedelta(days=TTL_DAYS)


def _normalize(name: str) -> str:
    return name.strip().lower()


async def verify_company(
    name: str,
    country_code: str,
    *,
    cached: dict[str, Any] | None = None,
    timeout: float = 8.0,
) -> dict[str, Any]:
    """Verifica una empresa en OpenCorporates.

    Returns:
        dict con shape:
            {
              "provider": "opencorporates",
              "verified": bool,
              "jurisdiction": str | None,
              "company_number": str | None,
              "matched_name": str | None,
              "checked_at": ISO8601,
              "error": str | None,
            }
    """
    if _is_cache_fresh(cached):
        return cached  # type: ignore[return-value]

    jurisdiction = country_code.lower()
    params = {
        "q": name,
        "jurisdiction_code": jurisdiction,
        "per_page": 5,
    }
    payload: dict[str, Any] = {
        "provider": "opencorporates",
        "verified": False,
        "jurisdiction": None,
        "company_number": None,
        "matched_name": None,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(
                f"{OPENCORPORATES_BASE}/companies/search", params=params
            )
        if resp.status_code == 429:
            payload["error"] = "rate_limited"
            return payload
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        payload["error"] = f"{type(e).__name__}: {str(e)[:200]}"
        return payload

    companies = (data.get("results") or {}).get("companies") or []
    if not companies:
        return payload

    target = _normalize(name)
    for entry in companies:
        company = entry.get("company") or {}
        cname = _normalize(company.get("name") or "")
        # Match si el nombre real contiene el buscado o viceversa
        if target and (target in cname or cname in target):
            payload.update(
                verified=True,
                jurisdiction=company.get("jurisdiction_code"),
                company_number=company.get("company_number"),
                matched_name=company.get("name"),
            )
            return payload
    return payload
