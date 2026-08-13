"""Presupuesto LLM: semántica del contextvar y fail-fast al agotarse.

AgentLint A301: `LLMBudgetExceeded` no debe reintentarse con backoff — agotar
el tope tiene que fallar en <2 s, no en ~29 s de sleeps de tenacity.
"""

import asyncio
import time

import pytest

from ivan_core.llm.base import (
    LLMBudgetExceeded,
    account_llm_call,
    llm_calls_used,
    set_llm_budget,
)


def test_budget_basico():
    set_llm_budget(2)
    account_llm_call()
    account_llm_call()
    assert llm_calls_used() == 2
    with pytest.raises(LLMBudgetExceeded):
        account_llm_call()


def test_sin_budget_no_limita():
    set_llm_budget(None)
    for _ in range(50):
        account_llm_call()
    assert llm_calls_used() == 0  # sin presupuesto no se contabiliza


def test_budget_agotado_falla_rapido_sin_retries():
    """El decorador de los providers no debe reintentar LLMBudgetExceeded."""
    from ivan_core.llm.openai_compat import OpenAICompatClient

    client = OpenAICompatClient(use_openrouter=True)
    set_llm_budget(1)
    account_llm_call()  # consume la única llamada

    start = time.monotonic()
    with pytest.raises(LLMBudgetExceeded):
        asyncio.run(client.complete_json("hola"))
    elapsed = time.monotonic() - start
    # Sin el predicado, tenacity dormiría 2+4+8+15 ≈ 29 s antes de re-lanzar.
    assert elapsed < 2.0, f"budget exceeded tardó {elapsed:.1f}s: se está reintentando"
