"""Cliente HTTP educado: rate limit, UA rotation, respeta robots.txt."""

import asyncio
import random
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from ivan_core.config import get_settings

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class PoliteHTTPClient:
    """Cliente HTTP que respeta rate limits y robots.txt.

    Uso:
        async with PoliteHTTPClient() as client:
            html = await client.get("https://example.com/page")
    """

    def __init__(self, rate_limit_per_sec: float | None = None) -> None:
        settings = get_settings()
        self.rate_limit = rate_limit_per_sec or settings.http_rate_limit_per_sec
        self.timeout = settings.http_timeout
        self._last_request: dict[str, float] = {}  # host -> timestamp
        self._robots_cache: dict[str, RobotFileParser] = {}
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "PoliteHTTPClient":
        self._client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=True)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    async def _check_robots(self, url: str) -> bool:
        """True si robots.txt permite acceder a la URL."""
        parsed = urlparse(url)
        host = f"{parsed.scheme}://{parsed.netloc}"

        if host not in self._robots_cache:
            rp = RobotFileParser()
            rp.set_url(f"{host}/robots.txt")
            try:
                # robots.txt parsing es síncrono, lo metemos en thread
                await asyncio.to_thread(rp.read)
            except Exception:
                # Si no se puede leer robots.txt, asumimos permitido (conservador)
                return True
            self._robots_cache[host] = rp

        return self._robots_cache[host].can_fetch("*", url)

    async def _respect_rate_limit(self, host: str) -> None:
        """Espera lo necesario para respetar el rate limit por host."""
        now = time.monotonic()
        last = self._last_request.get(host, 0)
        min_interval = 1.0 / self.rate_limit
        elapsed = now - last
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        self._last_request[host] = time.monotonic()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def get(self, url: str, *, check_robots: bool = True) -> str:
        """GET educado.

        Args:
            url: URL completa
            check_robots: Si True, verifica robots.txt antes (default True)

        Returns:
            HTML como string

        Raises:
            PermissionError: si robots.txt prohíbe la URL
        """
        if check_robots and not await self._check_robots(url):
            raise PermissionError(f"robots.txt prohíbe acceder a {url}")

        host = urlparse(url).netloc
        await self._respect_rate_limit(host)

        assert self._client is not None
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = await self._client.get(url, headers=headers)
        response.raise_for_status()
        return response.text
