"""Audit log RGPD - registro obligatorio de acciones sobre datos personales."""

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def audit_log(
    action: str,
    *,
    user_id: str | None = None,
    search_id: str | None = None,
    candidate_id: str | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> bool:
    """Registra una acción en la tabla audit_log.

    Acciones tipadas (no exhaustivo):
    - search_executed: nueva búsqueda lanzada
    - search_viewed: usuario abre detalle de búsqueda
    - candidate_viewed: usuario abre ficha de candidato
    - candidate_deleted: borrado a petición o por retención
    - export_csv | export_pdf: exportación de datos
    - share_link_created | share_link_accessed: compartir
    - retention_purge: purga automática
    - rights_request: solicitud de derecho ARCO-POL
    - cv_pdf_processed: CV PDF procesado en memoria (sin guardar)

    Devuelve True si el registro se escribió, False si falló (el caller decide
    si un fallo de auditoría es tolerable para SU acción — AgentLint A401).
    """
    from ivan_core.supabase_client import get_supabase_client

    client = get_supabase_client(use_service_role=True)

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "user_id": user_id,
        "search_id": search_id,
        "candidate_id": candidate_id,
        "details": details or {},
        "ip_address": ip_address,
        "user_agent": user_agent,
    }
    # Limpia None
    row = {k: v for k, v in row.items() if v is not None}

    try:
        client.table("audit_log").insert(row).execute()
        return True
    except Exception as e:
        # Audit log nunca debe romper la app, pero sí logear. SIN la fila: sus
        # campos (user_id, candidate_id, IP) son datos personales y este log va
        # a plataformas (Actions/Vercel) fuera de la política de retención
        # propia (AgentLint A501). El caller recibe False y decide.
        logger.error("audit_log failed: action=%s error=%s", action, type(e).__name__)
        return False
