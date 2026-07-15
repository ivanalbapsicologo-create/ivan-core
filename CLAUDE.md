# CLAUDE.md — ivan-core
> Contexto que Claude Code lee al empezar cada sesión en este repo.

## Qué es

`ivan-core` es una **librería interna genérica** de utilidades reutilizables entre
los proyectos de Iván (HR sourcing, licitaciones, automatizaciones). Propietario: Iván.
No es un framework: es una caja de herramientas donde cada función hace una cosa y se
importa donde haga falta. Hoy su consumidor principal es `sourcing-mai` (path local
`../ivan-core`).

El `README.md` documenta la superficie pública (módulos, instalación, env vars). Este
archivo fija las reglas de qué puede vivir aquí y cómo se trabaja.

## Estado

Lee `docs/STATUS.md` al empezar cualquier sesión. Es la memoria del proyecto entre
sesiones (versión, módulos disponibles, pendientes). Actualízalo al final con lo hecho
y lo siguiente. **No pongas estado fechado en este archivo.**

## Stack

Lista cerrada; no añadir dependencias sin pedirlo.

- **Runtime**: Python 3.11, empaquetado con Poetry (`pyproject.toml`).
- **Núcleo**: `pydantic` + `pydantic-settings` (config por env vars), `httpx`,
  `tenacity` (retry con backoff), `selectolax` (parser HTML), `json-repair`
  (recovery de JSON casi-válido del LLM).
- **Supabase**: `supabase-py` (`supabase >= 2.10`).
- **LLM (import lazy, todos opcionales en runtime)**: `google-genai` (Gemini),
  `anthropic` (Claude), `openai` (OpenAI / OpenRouter). El provider activo se
  elige por `LLM_PROVIDER`; el factory es `ivan_core.llm.get_llm_client()`.
- **Tests/calidad**: `pytest` + `pytest-asyncio`, `ruff` (line-length 100),
  `mypy --strict`.

## Reglas para añadir código aquí

**Todo módulo debe ser genérico.**
El código de esta librería debe servir a cualquier proyecto consumidor sin
modificarlo. Si te encuentras escribiendo "MAI", "sourcing", "candidato",
"licitación" o cualquier nombre de dominio de un proyecto concreto, para: eso
pertenece al repo consumidor, no aquí.

**Sin lógica de negocio.**
Reglas de un pipeline, prompts de una app, catálogos de fuentes, esquemas SQL de
un proyecto: viven en su repo, no en la librería. Aquí solo infraestructura
compartida (clientes, helpers, plantillas RGPD reutilizables).

**Sin credenciales.**
Nunca commitees tokens, claves ni secretos. **No hay `.env` en este repo**: el
proyecto consumidor carga su propio `.env` antes de usar la librería. `ivan-core`
solo lee variables de entorno vía `pydantic-settings` (ver `config.py`).

**Sin acoplamiento a un consumidor.**
No importes de `backend.*`, `src.*` ni referencies rutas dentro de otro proyecto.
La librería debe ser instalable de forma independiente con `pip install -e .`.

**Providers LLM con import lazy.**
Cada cliente (`llm/gemini.py`, `llm/claude.py`, `llm/openai_compat.py`) importa su
SDK dentro de la función, no a nivel de módulo, para que un proyecto que solo use un
provider no necesite los SDK de los demás. No rompas ese patrón.

**Antes de añadir un módulo o cambiar la superficie pública:**
1. Confirma que no tiene lógica específica de ningún proyecto.
2. Añade/actualiza tests en `tests/` junto al cambio.
3. Actualiza `README.md` (entrada del módulo) y `ivan_core/__init__.py` si expone API.
4. Sube versión en `pyproject.toml` + `ivan_core.__version__` si el cambio afecta a
   consumidores; anótalo en `docs/STATUS.md`. Los consumidores reinstalan a mano
   (path local, sin registro).

## Convenciones

- **Naming**: `snake_case` funciones/variables, `PascalCase` clases, `UPPER_SNAKE`
  constantes.
- **Git**: commits convencionales (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`,
  `chore:`). Rama principal: `main`.
- **Versionado**: sin SemVer formal (uso interno). Cambios breaking → bump de versión
  + actualización manual de los consumidores. **No hay `CHANGELOG.md`.**
- **Tests**: `pytest`. Lógica determinista; mockea las llamadas de red/LLM.

## Flujo con Claude Code

- **Al empezar**: lee `docs/STATUS.md`.
- **Antes de modificar**: lee los archivos afectados; verifica que los tests pasan.
- **Al terminar**: `ruff` + `mypy --strict` + tests verdes, commit convencional,
  actualiza `docs/STATUS.md`.
- **Ante ambigüedad**: pregunta, no inventes (sobre todo al añadir dependencias o
  cambiar la superficie pública que consumen otros proyectos).

## Comandos críticos

```bash
pip install -e .            # o: poetry install
pip install -e ".[dev]"     # incluye pytest/ruff/mypy
pytest                      # tests
ruff check . && mypy ivan_core
```

## Documentos clave por orden de lectura

1. `CLAUDE.md` (este) — reglas y convenciones.
2. `docs/STATUS.md` — estado actual.
3. `README.md` — superficie pública (módulos, instalación, env vars).
