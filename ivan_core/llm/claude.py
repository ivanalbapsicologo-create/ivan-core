"""Provider Anthropic (Claude)."""

import logging

from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings
from ivan_core.llm.base import BaseLLMClient, account_llm_call

logger = logging.getLogger(__name__)


class ClaudeClient(BaseLLMClient):
    """Wrapper sobre AsyncAnthropic."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key or "")
        self.default_model = settings.claude_model_default

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> str:
        account_llm_call()
        target_model = model or self.default_model
        response = await self.client.messages.create(
            model=target_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )

        if getattr(response, "stop_reason", None) == "max_tokens":
            logger.warning(
                "Claude response truncated by max_tokens (model=%s); "
                "considera subir max_tokens", target_model,
            )

        # Concatena solo los bloques de texto; tolerante a content vacío.
        blocks = response.content or []
        text = "".join(
            getattr(b, "text", "") or "" for b in blocks
            if getattr(b, "type", None) == "text"
        )
        if not text:
            logger.warning("Claude returned empty content (model=%s)", target_model)
        return text
