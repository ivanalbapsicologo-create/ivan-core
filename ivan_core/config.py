"""Configuración centralizada vía variables de entorno."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings comunes a todos los proyectos que usan ivan-core."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Entorno
    environment: Literal["dev", "prod", "test"] = "dev"
    log_level: str = "INFO"

    # Supabase (cada proyecto su propio project)
    supabase_url: str = Field(..., description="URL del proyecto Supabase")
    supabase_key: str = Field(..., description="Anon key (frontend + backend público)")
    supabase_service_role_key: str | None = None  # solo backend, nunca frontend

    # Serper.dev (compartido entre proyectos)
    serper_api_key: str = Field(..., description="API key de serper.dev")
    serper_base_url: str = "https://google.serper.dev"

    # Anthropic (compartido)
    anthropic_api_key: str = Field(..., description="API key de Anthropic")
    claude_model_default: str = "claude-haiku-4-5-20251001"
    claude_model_normalize: str = "claude-haiku-4-5-20251001"
    claude_model_scoring: str = "claude-haiku-4-5-20251001"

    # Rate limits y timeouts
    http_timeout: int = 30
    http_rate_limit_per_sec: float = 0.5  # 1 req cada 2s (PoliteHTTPClient)

    # Cap Serper por búsqueda (presupuesto duro para no agotar quota)
    serper_max_per_search: int = 30
    serper_default_num: int = 20  # resultados por query

    # GitHub Actions dispatch (para Vercel Function api/search.py)
    github_repo: str | None = None  # "owner/repo"
    github_dispatch_token: str | None = None  # PAT con permiso workflow

    # RGPD
    default_retention_days: int = 30
    extended_retention_days: int = 90
    audit_retention_months: int = 24


@lru_cache
def get_settings() -> Settings:
    """Singleton de Settings. Cacheado para evitar reparseo."""
    return Settings()  # type: ignore[call-arg]
