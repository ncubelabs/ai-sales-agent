"""MiniMax text generation provider."""

import httpx
from typing import Optional

from ..base import TextProvider, TextGenerationResult
from ..config import ProviderConfig


class MiniMaxTextProvider(TextProvider):
    """Text generation using MiniMax M2 model."""

    def __init__(self, config: ProviderConfig):
        self.config = config

        if not config.minimax_api_key:
            raise ValueError("MINIMAX_API_KEY not set")

        self.http_client = httpx.AsyncClient(
            base_url=config.minimax_base_url,
            headers={
                "Authorization": f"Bearer {config.minimax_api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )

    @property
    def name(self) -> str:
        return "minimax"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> TextGenerationResult:
        """Generate text using MiniMax M2."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "MiniMax-M2",
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = await self.http_client.post("/chat/completions", json=payload)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax Text API error {response.status_code}: {error_text}")

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        usage = None
        if "usage" in data:
            usage = {
                "prompt_tokens": data["usage"].get("prompt_tokens", 0),
                "completion_tokens": data["usage"].get("completion_tokens", 0),
                "total_tokens": data["usage"].get("total_tokens", 0),
            }

        return TextGenerationResult(
            content=content,
            model="MiniMax-M2",
            usage=usage,
        )

    async def close(self) -> None:
        await self.http_client.aclose()
