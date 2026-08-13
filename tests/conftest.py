"""Stubs de entorno para los tests (Settings exige estas claves)."""

import os

os.environ.setdefault("SUPABASE_URL", "https://stub.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "stub-anon-key")
os.environ.setdefault("SERPER_API_KEY", "stub-serper")
os.environ.setdefault("OPENROUTER_API_KEY", "stub-openrouter")
