"""Helpers RGPD para purga programada y gestión de retención."""

from datetime import date, timedelta

from ivan_core.audit_log import audit_log
from ivan_core.config import get_settings
from ivan_core.supabase_client import get_supabase_client


def purge_expired(table: str, retention_column: str = "retention_until") -> int:
    """Borra filas con retención expirada.

    Args:
        table: Nombre de la tabla
        retention_column: Columna de tipo date que marca cuando expira

    Returns:
        Número de filas borradas
    """
    client = get_supabase_client(use_service_role=True)
    today = date.today().isoformat()

    result = (
        client.table(table).delete().lt(retention_column, today).execute()
    )
    count = len(result.data) if result.data else 0

    audit_log(
        action="retention_purge",
        details={"table": table, "count": count, "executed_at": today},
    )
    return count


def compute_retention(extended: bool = False) -> date:
    """Calcula fecha de expiración según política."""
    settings = get_settings()
    days = settings.extended_retention_days if extended else settings.default_retention_days
    return date.today() + timedelta(days=days)
