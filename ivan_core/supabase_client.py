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
    if use_service_role:
        # Falla ruidosamente: degradar a anon en silencio rompería audit_log,
        # purga y crons (RLS los bloquearía) sin error visible.
        if not settings.supabase_service_role_key:
            raise RuntimeError(
                "Se pidió cliente service_role pero SUPABASE_SERVICE_ROLE_KEY no está "
                "configurada. Configúrala en el entorno del backend/jobs."
            )
        key = settings.supabase_service_role_key
    else:
        key = settings.supabase_key
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

    # service_role: estas tablas tienen RLS y datos personales; el cliente anon
    # no podría insertar.
    client = get_supabase_client(use_service_role=True)
    result = client.table(table).insert(row).execute()
    inserted = result.data[0] if result.data else {}

    audit_log(
        action=audit_action,
        user_id=user_id,
        details={"table": table, "row_id": inserted.get("id"), **(details or {})},
    )
    return inserted
