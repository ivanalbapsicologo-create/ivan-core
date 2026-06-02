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
    # Default openrouter: es el provider operativo (Llama 3.3 70B free).
    llm_provider: Literal["google", "anthropic", "openai", "openrouter"] = "openrouter"

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
    # Default: Llama 3.3 70B Instruct free tier. Free models de OpenRouter
    # tienen ~200 RPD sin créditos, ~1000 RPD con $10+ de saldo.
    # Alternativas gratuitas: deepseek/deepseek-chat:free,
    # google/gemini-2.0-flash-exp:free, mistralai/mistral-small-3.1-24b-instruct:free
    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model_default: str = "meta-llama/llama-3.3-70b-instruct:free"

    # Rate limits y timeouts
    http_timeout: int = 30
    http_rate_limit_per_sec: float = 0.5

    # Cap Serper por búsqueda (techo DURO; contrato de coste ≤17€/mes)
    serper_max_per_search: int = 30
    serper_default_num: int = 20

    # Tope de llamadas LLM por búsqueda (red de seguridad para la cuota free)
    llm_max_calls_per_search: int = 40

    # GitHub Actions dispatch (Vercel Functions → workflow)
    github_repo: str | None = None
    github_dispatch_token: str | None = None

    # ---------------- Autorización / seguridad de la API ----------------
    # Allowlist de admin (CSV). El panel admin solo es accesible para estas
    # identidades; el alta de Supabase Auth debería estar cerrada igualmente.
    admin_emails: str = ""
    admin_user_ids: str = ""
    # CORS: "*" o lista CSV de orígenes permitidos.
    cors_allowed_origins: str = "*"

    # RGPD
    default_retention_days: int = 30
    extended_retention_days: int = 90
    audit_retention_months: int = 24

    def admin_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.admin_emails.split(",") if e.strip()}

    def admin_id_set(self) -> set[str]:
        return {i.strip() for i in self.admin_user_ids.split(",") if i.strip()}

    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
