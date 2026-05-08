"""Helpers para PDFs encontrados en búsquedas.

IMPORTANTE: por decisión RGPD no descargamos ni almacenamos los PDFs.
Solo extraemos metadatos del snippet de Google + título + URL.
La extracción de campos del CV se hace por el LLM a partir del snippet.

Si en algún momento se decidiera procesar el PDF en memoria (no es el caso
actual), este módulo es donde iría esa lógica con borrado garantizado.
"""

from urllib.parse import urlparse


def is_likely_cv(url: str, title: str, snippet: str) -> bool:
    """Heurística: ¿este resultado parece un CV personal y no una plantilla?"""
    text = f"{url} {title} {snippet}".lower()

    cv_signals = ["cv", "curriculum", "resume", "résumé"]
    has_cv_signal = any(s in text for s in cv_signals)

    # Filtros de exclusión: plantillas, ejemplos, generadores
    exclude = [
        "template", "plantilla", "ejemplo", "example", "modelo",
        "generator", "sample", "format-de-cv", "cv-modele",
        "how to write", "cómo escribir", "how-to",
    ]
    is_excluded = any(s in text for s in exclude)

    return has_cv_signal and not is_excluded


def extract_filetype(url: str) -> str | None:
    """Devuelve 'pdf', 'doc', 'docx' o None."""
    path = urlparse(url).path.lower()
    if path.endswith(".pdf"):
        return "pdf"
    if path.endswith(".docx"):
        return "docx"
    if path.endswith(".doc"):
        return "doc"
    return None
