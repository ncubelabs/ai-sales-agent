"""vLLM text generation provider using OpenAI-compatible API."""

import httpx
from typing import Optional

from ..base import TextProvider, TextGenerationResult
from ..config import ProviderConfig


class VLLMTextProvider(TextProvider):
    """Text generation using vLLM with Llama 3.1 or other models.

    vLLM provides an OpenAI-compatible API, so we use the same format.
    Start vLLM server with:
        python -m vllm.entrypoints.openai.api_server \
            --model meta-llama/Llama-3.1-70B-Instruct
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.model = config.vllm_model

        headers = {"Content-Type": "application/json"}
        if config.vllm_api_key:
            headers["Authorization"] = f"Bearer {config.vllm_api_key}"

        # vLLM uses /v1 prefix for OpenAI compatibility
        base_url = config.vllm_base_url.rstrip("/")
        if not base_url.endswith("/v1"):
            base_url = f"{base_url}/v1"

        self.http_client = httpx.AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=300.0,  # vLLM can be slower than cloud APIs
        )

    @property
    def name(self) -> str:
        return "vllm"

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> TextGenerationResult:
        """Generate text using vLLM OpenAI-compatible API."""
        messages = []

        # Llama 3.1 Instruct works best with a system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # Default system prompt for Llama 3.1
            messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant. Respond clearly and concisely."
            })

        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            response = await self.http_client.post("/chat/completions", json=payload)

            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"vLLM API error {response.status_code}: {error_text}")

            data = response.json()

            # Handle potential error in response body
            if "error" in data:
                raise Exception(f"vLLM error: {data['error']}")

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
                model=self.model,
                usage=usage,
            )

        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Cannot connect to vLLM server at {self.config.vllm_base_url}. "
                f"Make sure vLLM is running: python -m vllm.entrypoints.openai.api_server "
                f"--model {self.model}"
            ) from e

    async def close(self) -> None:
        await self.http_client.aclose()
