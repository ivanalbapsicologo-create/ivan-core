# ivan-core

Librería interna de utilidades reutilizables para los proyectos de Iván.

## Filosofía

Patrones que se repiten entre `licitaciones-eme`, `sourcing-mai`, automatizaciones-eme y futuros proyectos:

- Cliente Supabase con auth y RLS
- Audit log RGPD estandarizado
- Búsquedas Google vía Serper (con caché y presupuesto)
- Llamadas a Claude API (normalización, scoring, batch)
- Utilidades RGPD (retención, LIA)
- Scrapers HTTP educados (rate limit, user-agent rotation, robots.txt)

NO es framework. Es caja de herramientas: cada función hace una cosa y se importa donde haga falta.

## Instalación en un proyecto consumidor

```toml
# pyproject.toml del proyecto consumidor
[tool.poetry.dependencies]
python = "^3.11"
ivan-core = {path = "../ivan-core", develop = true}
```

O bien:
```bash
pip install -e ../ivan-core
```

## Estructura del paquete

```
ivan_core/
├── __init__.py
├── config.py                      # Settings vía env vars (pydantic-settings)
├── supabase_client.py             # Wrapper supabase-py + helpers comunes
├── audit_log.py                   # Logger RGPD para acciones sobre datos personales
├── llm/
│   └── claude.py                  # Cliente Claude (async + batch + JSON safe parsing)
├── scrapers/
│   ├── http_client.py             # httpx + rate limit + UA rotation + robots.txt
│   ├── serper.py                  # Cliente Serper.dev (caché + budget)
│   └── pdf_meta.py                # Metadatos de PDFs sin descargar contenido
└── rgpd/
    ├── retention.py               # Helpers de purga programada
    └── lia.py                     # Plantilla LIA (interés legítimo)
```

## Variables de entorno requeridas

Cada proyecto consumidor define las suyas. `ivan-core` las lee con `pydantic-settings`:

```
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_SERVICE_ROLE_KEY=        # opcional, solo backend
SERPER_API_KEY=
ANTHROPIC_API_KEY=
SERPER_MAX_PER_SEARCH=30          # cap por búsqueda
ENVIRONMENT=dev|prod|test
```

## Versionado

Sin versión semántica formal por ahora (uso interno). Cambios breaking se anotan
en `CHANGELOG.md` (cuando exista) y se actualizan los proyectos consumidores manualmente.
