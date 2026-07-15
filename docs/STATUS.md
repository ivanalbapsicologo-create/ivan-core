# STATUS — ivan-core
_Actualizado: 2026-07-15_

## Dónde estamos

Librería estable en **v0.4.1**, en su repo Git propio (rama `main`). Superficie
pública pequeña y cubierta por tests. Consumidor principal: `sourcing-mai` (path
local `../ivan-core`). Se añaden módulos solo cuando son genéricos de verdad.

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
