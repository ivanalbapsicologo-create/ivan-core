# STATUS — ivan-core
_Actualizado: 2026-08-13_

## Dónde estamos

Librería estable en **v0.4.1**, en su repo Git propio (rama `main`). Consumidor
principal: `sourcing-mai` (path local `../ivan-core`). Se añaden módulos solo
cuando son genéricos de verdad.

**Tests**: la primera suite propia llegó el 2026-08-13 (12 tests: presupuesto
LLM con fail-fast, `parse_json_safe`, caché de OpenCorporates). Antes de esa
fecha este STATUS afirmaba "cubierta por tests" sin que existiera `tests/`
(hallazgo A601 de la review AgentLint). La mayor parte de la superficie sigue
sin cobertura directa — la cobertura indirecta vive en la suite de sourcing-mai.

**Sesión 2026-08-13 (quick wins AgentLint)**:
- A301: los decoradores tenacity de los 3 providers ya NO reintentan
  `LLMBudgetExceeded` (presupuesto agotado fallaba tras ~29 s de backoff).
- A402: `_is_cache_fresh` (OpenCorporates) ignora payloads con `error` — un
  timeout/rate-limit ya no deja a la empresa sin reverificar 90 días.
- A401/A501: `audit_log` devuelve `bool` (el caller sabe si se auditó) y el log
  de fallo ya no vuelca la fila con datos personales.
- Deuda anotada (review completa en `agentlint/reviews/ivan-core/report.md`):
  el presupuesto cuenta intentos (no llamadas lógicas); `refresh_active_countries`
  corre sin presupuesto; ~45 % de la librería es superficie huérfana (rgpd/,
  http_client, insert_with_audit…) candidata a poda (hipótesis H-0001).

## Módulos disponibles (hechos)

- `ivan_core.config` — `Settings` + `get_settings()` (pydantic-settings, multi-alias
  para Supabase/Vercel).
- `ivan_core.supabase_client` — `get_supabase_client()`.
- `ivan_core.audit_log` — `audit_log()` RGPD.
- `ivan_core.llm` — `get_llm_client()` (factory por `LLM_PROVIDER`) + `LLMClient`.
  Providers: `gemini`, `claude`, `openai_compat` (OpenAI + OpenRouter), con import lazy
  del SDK y parsing JSON tolerante (`json-repair`).
- `ivan_core.scrapers` — `SerperClient` (caché + presupuesto repartible), `http_client`,
  `pdf_meta` (metadatos sin descargar el PDF).
- `ivan_core.rgpd` — `retention`, `lia`.
- `ivan_core.verifiers` — `opencorporates`.

## Hecho reciente

- `947741a` — retry en `complete_json` + bump a **0.4.1**.
- `0c59608` — bump 0.3.0 → 0.4.0.
- `63c7427` — presupuesto Serper repartible entre módulos, tope de llamadas LLM,
  verifiers y hardening general.
- `499109d` — default LLM a OpenRouter Llama 3.3 70B `:free` + modo JSON resiliente.
- Serie de fixes de parsing JSON del LLM (`json-repair`, balanced-extract, max_tokens
  8192) y de `pdf_meta` (rechaza slugs aleatorios / hosts de baja calidad).

## Pendiente / próximo

- Sin backlog abierto propio. Los nuevos helpers entran cuando un consumidor los
  necesite y estén libres de lógica de negocio.
- Sin `CHANGELOG.md` ni SemVer formal (decisión consciente para uso interno); si crece
  el número de consumidores, reconsiderar.

## Bloqueos

- Ninguno.
