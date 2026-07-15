# ivan-core

Librería interna de utilidades reutilizables para los proyectos de Iván.

## Filosofía

Patrones que se repiten entre `sourcing-mai`, licitaciones, automatizaciones y
futuros proyectos:

- Cliente Supabase con auth y RLS
- Audit log RGPD estandarizado
- Búsquedas Google vía Serper (con caché y presupuesto repartible)
- Llamadas a LLM **multi-provider** (Gemini / Claude / OpenAI / OpenRouter) con
  parsing JSON robusto (`json-repair`)
- Utilidades RGPD (retención, LIA)
- Scrapers HTTP educados (rate limit, user-agent, metadatos de PDF sin descargar)
- Verifiers (p. ej. OpenCorporates)

NO es framework. Es caja de herramientas: cada función hace una cosa y se importa
donde haga falta.

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
│   ├── __init__.py                # get_llm_client() — factory por LLM_PROVIDER
│   ├── base.py                    # interfaz común (complete / complete_json)
│   ├── gemini.py                  # Google Gemini
│   ├── claude.py                  # Anthropic Claude
│   └── openai_compat.py           # OpenAI directo + OpenRouter
├── scrapers/
│   ├── http_client.py             # httpx + rate limit + user-agent
│   ├── serper.py                  # Cliente Serper.dev (caché + presupuesto)
│   └── pdf_meta.py                # Metadatos de PDFs sin descargar contenido
├── rgpd/
│   ├── retention.py               # Helpers de purga programada
│   └── lia.py                     # Plantilla LIA (interés legítimo)
└── verifiers/
    └── opencorporates.py          # Verificación de empresas
```

## Capa LLM (multi-provider)

```python
from ivan_core.llm import get_llm_client

client = get_llm_client()                 # provider según LLM_PROVIDER
data = await client.complete_json("...", system="...")
```

`LLM_PROVIDER` ∈ `google` | `anthropic` | `openai` | `openrouter`. Los SDK se
importan de forma lazy: solo necesitas instalado el del provider que uses.

## Variables de entorno requeridas

Cada proyecto consumidor define las suyas en su propio `.env`; `ivan-core` las lee
con `pydantic-settings`. Las principales:

```
SUPABASE_URL=
SUPABASE_KEY=                     # anon key
SUPABASE_SERVICE_ROLE_KEY=        # opcional, solo backend
SERPER_API_KEY=
SERPER_MAX_PER_SEARCH=30          # cap DURO por búsqueda
LLM_PROVIDER=openrouter           # google | anthropic | openai | openrouter
OPENROUTER_API_KEY=               # (o GOOGLE_API_KEY / ANTHROPIC_API_KEY / OPENAI_API_KEY)
LLM_MAX_CALLS_PER_SEARCH=40       # tope de llamadas LLM por búsqueda
ENVIRONMENT=dev                   # dev | prod | test
```

Superficie completa de settings: `ivan_core/config.py`.

## Versionado

Sin versión semántica formal por ahora (uso interno). Los cambios breaking se
reflejan con un bump de versión en `pyproject.toml` + `ivan_core.__version__`, y los
proyectos consumidores se reinstalan manualmente (dependencia de path, sin registro).

## Más

- Reglas y contexto para Claude Code: `CLAUDE.md`.
- Estado actual: `docs/STATUS.md`.
