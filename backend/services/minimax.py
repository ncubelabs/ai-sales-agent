"""MiniMax API Client - M2.1 Text, Speech TTS, Hailuo Video"""
import os
import httpx
import anthropic
from typing import Optional
import asyncio

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_BASE_URL = "https://api.minimax.io/v1"


class MiniMaxClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or MINIMAX_API_KEY
        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")
        
        # Anthropic-compatible client for M2.1
        self.text_client = anthropic.Anthropic(
            api_key=self.api_key,
            base_url=MINIMAX_BASE_URL
        )
        
        # HTTP client for Speech and Video
        self.http_client = httpx.AsyncClient(
            base_url=MINIMAX_BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0
        )
    
    async def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using MiniMax M2-her"""
        payload = {
            "model": "M2-her",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        response = await self.http_client.post("/chat/completions", json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def generate_speech(
        self, 
        text: str, 
        voice_id: str = "female-shaonv",
        speed: float = 1.0,
        emotion: str = "happy"
    ) -> bytes:
        """Generate speech using MiniMax Speech TTS"""
        payload = {
            "model": "speech-2.8-hd",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "emotion": emotion
            },
            "audio_setting": {
                "format": "mp3",
                "sample_rate": 32000
            }
        }
        
        response = await self.http_client.post("/t2a_v2", json=payload)
        response.raise_for_status()
        
        data = response.json()
        # Audio is hex-encoded
        audio_hex = data["data"]["audio"]
        return bytes.fromhex(audio_hex)
    
    async def generate_video(
        self,
        prompt: str,
        model: str = "T2V-01"
    ) -> dict:
        """Start video generation using Hailuo (returns job info)"""
        # Video generation appears to not be available with this API key
        # Return a mock response to prevent errors
        return {
            "task_id": "mock_task_video_not_available",
            "status": "failed",
            "message": "Video generation not available with current API access"
        }
    
    async def check_video_status(self, task_id: str) -> dict:
        """Check video generation status"""
        if task_id.startswith("mock_task"):
            return {
                "status": "failed",
                "message": "Video generation not available with current API access"
            }
        response = await self.http_client.get(f"/video/generation/{task_id}")
        response.raise_for_status()
        return response.json()
    
    async def wait_for_video(self, task_id: str, poll_interval: int = 5, timeout: int = 300) -> dict:
        """Poll until video is ready"""
        elapsed = 0
        while elapsed < timeout:
            status = await self.check_video_status(task_id)
            if status.get("status") == "completed":
                return status
            if status.get("status") == "failed":
                raise Exception(f"Video generation failed: {status}")
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        raise TimeoutError("Video generation timed out")
    
    async def close(self):
        await self.http_client.aclose()


# Singleton instance
_client: Optional[MiniMaxClient] = None

def get_client() -> MiniMaxClient:
    global _client
    if _client is None:
        _client = MiniMaxClient()
    return _client
