"""MiniMax video generation provider."""

import asyncio
import httpx
from typing import Optional
from pathlib import Path

from ..base import VideoProvider, VideoGenerationResult
from ..config import ProviderConfig


class MiniMaxVideoProvider(VideoProvider):
    """Video generation using MiniMax Hailuo/T2V models."""

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
        duration: int = 6,
        model: str = "T2V-01",
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate video using MiniMax T2V/Hailuo models."""
        payload = {
            "model": model,
            "prompt": prompt,
            "prompt_optimizer": True,
            "duration": duration,
        }

        response = await self.http_client.post("/video_generation", json=payload)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax Video API error {response.status_code}: {error_text}")

        data = response.json()

        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise Exception(f"MiniMax Video error: {base_resp.get('status_msg')}")

        task_id = data.get("task_id")
        if not task_id:
            raise Exception(f"No task_id in response: {data}")

        # Wait for completion
        result = await self._wait_for_video(task_id)

        # Download video
        file_id = result.get("file_id")
        if file_id:
            video_bytes = await self._download_video(file_id)
            return VideoGenerationResult(
                video_bytes=video_bytes,
                task_id=task_id,
                status="completed",
                duration=duration,
            )

        return VideoGenerationResult(
            task_id=task_id,
            status="completed",
            duration=duration,
        )

    async def generate_talking_head(
        self,
        audio_path: str,
        face_image_path: str,
        image_url: Optional[str] = None,
        duration: int = 6,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate talking head using S2V-01 with subject reference.

        Note: MiniMax S2V-01 requires a public URL for the face image.
        The image_url parameter should be provided, or the face_image_path
        should be uploaded to get a URL first.
        """
        if not image_url:
            # For MiniMax, we need a public URL - caller should handle upload
            raise ValueError(
                "MiniMax S2V-01 requires a public image_url. "
                "Upload the face image first to get a URL."
            )

        # Generate video prompt for talking head
        prompt = kwargs.get(
            "prompt",
            "Professional person talking to camera in modern office setting. "
            "Natural head movements and expressions. Confident and friendly demeanor. "
            "High quality, well-lit, corporate environment."
        )

        payload = {
            "model": "S2V-01",
            "prompt": prompt,
            "prompt_optimizer": True,
            "duration": duration,
            "subject_reference": [
                {
                    "type": "character",
                    "image": [image_url],
                }
            ],
        }

        response = await self.http_client.post("/video_generation", json=payload)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax S2V-01 API error {response.status_code}: {error_text}")

        data = response.json()

        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise Exception(f"MiniMax S2V-01 error: {base_resp.get('status_msg')}")

        task_id = data.get("task_id")
        if not task_id:
            raise Exception(f"No task_id in response: {data}")

        # Wait for completion
        result = await self._wait_for_video(task_id)

        # Download video
        file_id = result.get("file_id")
        if file_id:
            video_bytes = await self._download_video(file_id)
            return VideoGenerationResult(
                video_bytes=video_bytes,
                task_id=task_id,
                status="completed",
                duration=duration,
            )

        return VideoGenerationResult(
            task_id=task_id,
            status="completed",
            duration=duration,
        )

    async def _wait_for_video(
        self, task_id: str, poll_interval: int = 10, timeout: int = 600
    ) -> dict:
        """Poll until video is ready."""
        elapsed = 0
        while elapsed < timeout:
            response = await self.http_client.get(
                "/query/video_generation",
                params={"task_id": task_id},
            )

            if response.status_code != 200:
                error_text = response.text
                raise Exception(
                    f"MiniMax Video status error {response.status_code}: {error_text}"
                )

            data = response.json()

            base_resp = data.get("base_resp", {})
            if base_resp.get("status_code") != 0:
                raise Exception(
                    f"Video generation failed: {base_resp.get('status_msg')}"
                )

            status = data.get("status", "unknown")

            if status == "Success":
                return {
                    "status": "completed",
                    "file_id": data.get("file_id"),
                }

            if status == "Fail":
                raise Exception(
                    f"Video generation failed: {base_resp.get('status_msg', 'Unknown error')}"
                )

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Video generation timed out after {timeout}s")

    async def _download_video(self, file_id: str) -> bytes:
        """Download video file by file_id."""
        # Get file metadata with download URL
        response = await self.http_client.get(
            "/files/retrieve",
            params={"file_id": file_id},
        )

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve file info: {response.status_code}")

        data = response.json()
        download_url = data.get("file", {}).get("download_url")

        if not download_url:
            raise Exception(f"No download URL in response: {data}")

        # Download the actual video file from CDN
        async with httpx.AsyncClient(timeout=300.0) as client:
            video_response = await client.get(download_url)

            if video_response.status_code != 200:
                raise Exception(
                    f"Failed to download video from CDN: {video_response.status_code}"
                )

            return video_response.content

    async def close(self) -> None:
        await self.http_client.aclose()
