"""Caché de OpenCorporates: los errores no se congelan 90 días (AgentLint A402)."""

from datetime import datetime, timedelta, timezone

from ivan_core.verifiers.opencorporates import _is_cache_fresh


def _payload(**overrides):
    base = {
        "provider": "opencorporates",
        "verified": False,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
    base.update(overrides)
    return base


def test_resultado_fresco_es_cache():
    assert _is_cache_fresh(_payload(verified=True)) is True


def test_error_nunca_es_cache_fresco():
    # Un timeout/rate-limit cacheado como fresco dejaba a la empresa sin
    # reverificar durante todo el TTL.
    assert _is_cache_fresh(_payload(error="rate_limited")) is False


def test_caducado_no_es_fresco():
    old = (datetime.now(timezone.utc) - timedelta(days=91)).isoformat()
    assert _is_cache_fresh(_payload(checked_at=old)) is False


def test_vacio_no_es_fresco():
    assert _is_cache_fresh(None) is False
    assert _is_cache_fresh({}) is False
