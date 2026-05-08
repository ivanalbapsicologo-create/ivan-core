"""Provider Anthropic (Claude)."""

from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings
from ivan_core.llm.base import BaseLLMClient


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
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> str:
        response = await self.client.messages.create(
            model=model or self.default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "",
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text  # type: ignore[union-attr]
