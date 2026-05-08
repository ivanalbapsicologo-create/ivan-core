"""ivan_core - utilidades reutilizables entre proyectos."""

from ivan_core.audit_log import audit_log
from ivan_core.config import Settings, get_settings
from ivan_core.llm import ClaudeClient
from ivan_core.scrapers import SerperClient
from ivan_core.supabase_client import get_supabase_client

__all__ = [
    "Settings",
    "ClaudeClient",
    "SerperClient",
    "audit_log",
    "get_settings",
    "get_supabase_client",
]

__version__ = "0.2.0"
