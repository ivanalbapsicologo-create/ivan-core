"""Configuración centralizada vía variables de entorno."""

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings comunes a todos los proyectos que usan ivan-core."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Entorno
    environment: Literal["dev", "prod", "test"] = "dev"
    log_level: str = "INFO"

    # Supabase. Aceptamos varios alias porque la integración Supabase-Vercel
    # genera nombres ligeramente distintos (SUPABASE_ANON_KEY vs SUPABASE_KEY).
    supabase_url: str = Field(
        ...,
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
        description="URL del proyecto Supabase",
    )
    supabase_key: str = Field(
        ...,
        validation_alias=AliasChoices(
            "SUPABASE_KEY",
            "SUPABASE_ANON_KEY",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY",
        ),
        description="Anon key (frontend + backend público)",
    )
    supabase_service_role_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "SUPABASE_SERVICE_ROLE_KEY",
            "SUPABASE_SERVICE_KEY",
        ),
    )

    # Serper.dev
    serper_api_key: str = Field(..., description="API key de serper.dev")
    serper_base_url: str = "https://google.serper.dev"

    # ---------------- LLM ----------------
    # Provider activo: google | anthropic | openai | openrouter
    llm_provider: Literal["google", "anthropic", "openai", "openrouter"] = "google"

    # Google Gemini (free tier de Google AI Studio)
    google_api_key: str | None = None
    gemini_model_default: str = "gemini-2.5-flash"

    # Anthropic
    anthropic_api_key: str | None = None
    claude_model_default: str = "claude-haiku-4-5-20251001"
    claude_model_normalize: str = "claude-haiku-4-5-20251001"
    claude_model_scoring: str = "claude-haiku-4-5-20251001"

    # OpenAI directo
    openai_api_key: str | None = None
    openai_base_url: str | None = None  # None = api.openai.com por defecto
    openai_model_default: str = "gpt-4o-mini"

    # OpenRouter (compatible OpenAI)
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model_default: str = "google/gemini-2.5-flash"

    # Rate limits y timeouts
    http_timeout: int = 30
    http_rate_limit_per_sec: float = 0.5

    # Cap Serper por búsqueda
    serper_max_per_search: int = 30
    serper_default_num: int = 20

    # GitHub Actions dispatch (Vercel Functions → workflow)
    github_repo: str | None = None
    github_dispatch_token: str | None = None

    # RGPD
    default_retention_days: int = 30
    extended_retention_days: int = 90
    audit_retention_months: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
