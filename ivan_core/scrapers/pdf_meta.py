"""Helpers para PDFs encontrados en búsquedas.

IMPORTANTE: por decisión RGPD no descargamos ni almacenamos los PDFs.
Solo extraemos metadatos del snippet de Google + título + URL.
"""

import re
from urllib.parse import urlparse


# Hosts que rara vez albergan CVs reales (blogs amateur, repositorios random).
# Si el host está aquí, exigimos señales fuertes de CV.
LOW_QUALITY_HOSTS = (
    "over-blog-kiwi.com", "over-blog.com", "blogspot.", "wordpress.com",
    "tumblr.com", "weebly.com", "wix.com", "yola.com",
    "issuu.com",  # plataforma de docs, mucho marketing
    "scribd.com",  # mismo
    "slideshare.net",  # mismo
    "academia.edu",  # OK pero su sourcing va por scholar
    "researchgate.net",  # idem
    "facebook.com", "twitter.com", "instagram.com",
)

# Slugs random tipo "ob_9075dd_xx.pdf" o "doc-1234567.pdf" no parecen nombres humanos
RANDOM_SLUG_RX = re.compile(
    r"^(ob_[a-f0-9]+|doc[-_]\d+|file[-_]\d+|tmp[-_]\w+|[a-f0-9]{20,}|\d{8,})\."
)


def is_likely_cv(url: str, title: str, snippet: str) -> bool:
    """Heurística mejorada: ¿este resultado parece un CV personal y no una plantilla?"""
    text = f"{url} {title} {snippet}".lower()

    cv_signals = ["cv", "curriculum", "resume", "résumé", "vitae"]
    has_cv_signal = any(s in text for s in cv_signals)
    if not has_cv_signal:
        return False

    # Filtros de exclusión: plantillas, ejemplos, generadores
    exclude = [
        "template", "plantilla", "ejemplo", "example", "modelo",
        "generator", "sample", "format-de-cv", "cv-modele",
        "how to write", "cómo escribir", "como escribir", "how-to",
        "best cv", "cv builder", "cv maker", "cv design",
    ]
    if any(s in text for s in exclude):
        return False

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.lower()
    filename = path.rsplit("/", 1)[-1] if "/" in path else path

    # Hosts dudosos: solo aceptar si filename parece nombre humano
    if any(lq in host for lq in LOW_QUALITY_HOSTS):
        if RANDOM_SLUG_RX.match(filename):
            return False
        # Filename sin extensión que parezca nombre humano (al menos 1 letra + nombre)
        if not _looks_like_human_filename(filename):
            return False

    return True


def _looks_like_human_filename(filename: str) -> bool:
    """Heurística: filename con al menos 2 palabras alfabéticas separadas (nombre apellido)."""
    base = filename.rsplit(".", 1)[0]
    # Reemplaza separadores por espacio
    normalized = re.sub(r"[-_.]+", " ", base)
    parts = [p for p in normalized.split() if any(c.isalpha() for c in p)]
    return len(parts) >= 2


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
