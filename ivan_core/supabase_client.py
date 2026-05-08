"""Cliente Supabase con helpers comunes."""

from functools import lru_cache

from supabase import Client, create_client

from ivan_core.config import get_settings


@lru_cache
def get_supabase_client(use_service_role: bool = False) -> Client:
    """Devuelve cliente Supabase singleton.

    Args:
        use_service_role: True solo en backend (bypass RLS para crons,
            audit_log, retención automática). Nunca True en frontend.
    """
    settings = get_settings()
    key = (
        settings.supabase_service_role_key
        if use_service_role and settings.supabase_service_role_key
        else settings.supabase_key
    )
    return create_client(settings.supabase_url, key)


def insert_with_audit(
    table: str,
    row: dict,
    *,
    audit_action: str,
    user_id: str | None = None,
    details: dict | None = None,
) -> dict:
    """Inserta una fila Y registra audit_log atómicamente.

    Pensado para cualquier tabla que contenga datos personales.
    """
    from ivan_core.audit_log import audit_log

    client = get_supabase_client()
    result = client.table(table).insert(row).execute()
    inserted = result.data[0] if result.data else {}

    audit_log(
        action=audit_action,
        user_id=user_id,
        details={"table": table, "row_id": inserted.get("id"), **(details or {})},
    )
    return inserted
