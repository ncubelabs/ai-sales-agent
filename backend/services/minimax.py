"""MiniMax API Client - M2 Text, Speech TTS, Hailuo Video, Voice Clone, S2V-01

Required environment variables:
- MINIMAX_API_KEY: Your MiniMax API key
- MINIMAX_GROUP_ID: Your MiniMax Group ID (required for TTS)
  Find it at: https://www.minimax.io/platform/user-center/basic-information
"""
import os
import httpx
from typing import Optional, Literal
import asyncio

MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY")
MINIMAX_GROUP_ID = os.getenv("MINIMAX_GROUP_ID")
MINIMAX_BASE_URL = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1")


class MiniMaxClient:
    def __init__(self, api_key: Optional[str] = None, group_id: Optional[str] = None):
        self.api_key = api_key or MINIMAX_API_KEY
        self.group_id = group_id or MINIMAX_GROUP_ID

        if not self.api_key:
            raise ValueError("MINIMAX_API_KEY not set")

        # HTTP client for all API calls
        self.http_client = httpx.AsyncClient(
            base_url=MINIMAX_BASE_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )

    async def generate_text(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate text using MiniMax M2"""
        payload = {
            "model": "MiniMax-M2",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        response = await self.http_client.post("/chat/completions", json=payload)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax Text API error {response.status_code}: {error_text}")

        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    async def generate_speech(
        self,
        text: str,
        voice_id: str = "male-qn-qingse",
        speed: float = 1.0,
        emotion: str = "happy"
    ) -> bytes:
        """Generate speech using MiniMax Speech TTS

        Requires MINIMAX_GROUP_ID to be set.
        Voice IDs: male-qn-qingse, male-qn-jingying, female-shaonv, female-yujie, etc.
        For cloned voices, use the voice_id returned from clone_voice().
        """
        if not self.group_id:
            raise ValueError(
                "MINIMAX_GROUP_ID not set. "
                "Find it at: https://www.minimax.io/platform/user-center/basic-information"
            )

        payload = {
            "model": "speech-02-hd",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "vol": 1.0,
                "pitch": 0
            },
            "audio_setting": {
                "format": "mp3",
                "sample_rate": 32000
            }
        }

        # TTS endpoint requires GroupId as query parameter
        response = await self.http_client.post(
            f"/t2a_v2?GroupId={self.group_id}",
            json=payload
        )

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax TTS API error {response.status_code}: {error_text}")

        data = response.json()

        # Check for API-level errors
        if data.get("base_resp", {}).get("status_code") != 0:
            raise Exception(f"MiniMax TTS error: {data.get('base_resp', {}).get('status_msg')} (Response: {data})")

        # Audio is hex-encoded in the response
        audio_hex = data.get("data", {}).get("audio") or data.get("audio_file")
        if not audio_hex:
            raise Exception(f"No audio in response: {data}")

        return bytes.fromhex(audio_hex)

    async def upload_file(
        self,
        file_bytes: bytes,
        filename: str,
        purpose: Literal["voice_clone", "subject_reference"] = "voice_clone"
    ) -> str:
        """Upload a file to MiniMax for voice cloning or subject reference

        Args:
            file_bytes: The file content as bytes
            filename: Original filename (used to determine content type)
            purpose: 'voice_clone' for audio files, 'subject_reference' for video images

        Returns:
            file_id for use with clone_voice or generate_subject_video
        """
        # Determine content type from filename
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        content_type_map = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
        }
        content_type = content_type_map.get(ext, 'application/octet-stream')

        # MiniMax file upload uses multipart/form-data
        files = {
            'file': (filename, file_bytes, content_type)
        }
        data = {
            'purpose': purpose
        }

        # Create a new client without JSON content-type for multipart upload
        # Include GroupId for voice_clone uploads (required by API)
        upload_url = "/files/upload"
        if self.group_id:
            upload_url = f"/files/upload?GroupId={self.group_id}"

        async with httpx.AsyncClient(
            base_url=MINIMAX_BASE_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0
        ) as upload_client:
            response = await upload_client.post(upload_url, files=files, data=data)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax file upload error {response.status_code}: {error_text}")

        resp_data = response.json()

        # Check for API-level errors
        base_resp = resp_data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise Exception(f"MiniMax upload error: {base_resp.get('status_msg')} (Response: {resp_data})")

        file_id = resp_data.get("file", {}).get("file_id")
        if not file_id:
            raise Exception(f"No file_id in upload response: {resp_data}")

        # Return file_id as string for storage, but it will be converted to int for API calls
        return str(file_id)

    async def clone_voice(self, file_id: str, voice_name: str) -> str:
        """Clone a voice from an uploaded audio sample

        Args:
            file_id: The file_id from upload_file (audio 10s-5min, MP3/WAV/M4A)
            voice_name: Custom voice ID (will be used for TTS)

        Returns:
            voice_id to be used with generate_speech
        """
        if not self.group_id:
            raise ValueError(
                "MINIMAX_GROUP_ID not set. "
                "Find it at: https://www.minimax.io/platform/user-center/basic-information"
            )

        # MiniMax Voice Clone API
        # Reference: https://platform.minimax.io/docs/api-reference/voice-cloning-clone.md
        # Note: file_id must be an integer, not string
        payload = {
            "file_id": int(file_id),
            "voice_id": voice_name,
        }

        # Voice clone requires GroupId as query parameter
        response = await self.http_client.post(
            f"/voice_clone?GroupId={self.group_id}",
            json=payload
        )

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax voice clone error {response.status_code}: {error_text}")

        data = response.json()

        # Check for API-level errors
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            error_msg = base_resp.get("status_msg", "Unknown error")
            raise Exception(f"MiniMax voice clone error: {error_msg} (Response: {data})")

        # Return the voice_id for use with TTS
        return voice_name

    async def generate_subject_video(
        self,
        image_url: str,
        prompt: str,
        duration: int = 6
    ) -> dict:
        """Generate a video using S2V-01 with subject reference (talking head)

        Args:
            image_url: Public URL of the face image for subject reference
            prompt: Text description of the video (should describe person talking)
            duration: Video length in seconds (6 or 10)

        Returns:
            dict with task_id for status polling
        """
        payload = {
            "model": "S2V-01",
            "prompt": prompt,
            "prompt_optimizer": True,
            "duration": duration,
            "subject_reference": [
                {
                    "type": "character",
                    "image": [image_url]
                }
            ]
        }

        response = await self.http_client.post("/video_generation", json=payload)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax S2V-01 API error {response.status_code}: {error_text}")

        data = response.json()

        # Check for API-level errors
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise Exception(f"MiniMax S2V-01 error: {base_resp.get('status_msg')}")

        return {
            "task_id": data.get("task_id"),
            "status": "pending"
        }
    
    async def generate_video(
        self,
        prompt: str,
        model: str = "T2V-01",
        duration: int = 6
    ) -> dict:
        """Start video generation using Hailuo

        Args:
            prompt: Text description of the video (max 2000 chars)
            model: T2V-01, T2V-01-Director, MiniMax-Hailuo-02, or MiniMax-Hailuo-2.3
            duration: Video length in seconds (6 or 10)

        Returns:
            dict with task_id for status polling
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "prompt_optimizer": True,
            "duration": duration
        }

        response = await self.http_client.post("/video_generation", json=payload)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax Video API error {response.status_code}: {error_text}")

        data = response.json()

        # Check for API-level errors
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise Exception(f"MiniMax Video error: {base_resp.get('status_msg')}")

        return {
            "task_id": data.get("task_id"),
            "status": "pending"
        }

    async def check_video_status(self, task_id: str) -> dict:
        """Check video generation status

        Returns:
            dict with status, file_id (if complete), and download URL
        """
        response = await self.http_client.get(
            "/query/video_generation",
            params={"task_id": task_id}
        )

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax Video status error {response.status_code}: {error_text}")

        data = response.json()

        # Check for API-level errors
        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            return {
                "status": "failed",
                "error": base_resp.get("status_msg")
            }

        status = data.get("status", "unknown")

        result = {
            "status": status,
            "task_id": task_id
        }

        # If completed, include the file info
        if status == "Success":
            result["status"] = "completed"
            result["file_id"] = data.get("file_id")
            # The video URL is in the file_id - need to fetch via files API
            if data.get("file_id"):
                result["video_url"] = f"https://api.minimax.io/v1/files/retrieve?file_id={data['file_id']}"

        elif status == "Fail":
            result["status"] = "failed"
            result["error"] = data.get("base_resp", {}).get("status_msg", "Unknown error")

        elif status in ["Queueing", "Processing"]:
            result["status"] = "processing"

        return result

    async def wait_for_video(self, task_id: str, poll_interval: int = 10, timeout: int = 600) -> dict:
        """Poll until video is ready

        Args:
            task_id: The task ID from generate_video
            poll_interval: Seconds between status checks (default 10)
            timeout: Maximum wait time in seconds (default 600 = 10 min)

        Returns:
            dict with video_url when complete
        """
        elapsed = 0
        while elapsed < timeout:
            status = await self.check_video_status(task_id)

            if status.get("status") == "completed":
                return status

            if status.get("status") == "failed":
                raise Exception(f"Video generation failed: {status.get('error')}")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise TimeoutError(f"Video generation timed out after {timeout}s")

    async def download_video(self, file_id: str) -> bytes:
        """Download video file by file_id

        First retrieves the file metadata to get the download URL,
        then downloads the actual video file.
        """
        # Step 1: Get file metadata with download URL
        response = await self.http_client.get(
            "/files/retrieve",
            params={"file_id": file_id}
        )

        if response.status_code != 200:
            raise Exception(f"Failed to retrieve file info: {response.status_code}")

        data = response.json()
        download_url = data.get("file", {}).get("download_url")

        if not download_url:
            raise Exception(f"No download URL in response: {data}")

        # Step 2: Download the actual video file from CDN
        async with httpx.AsyncClient(timeout=300.0) as client:
            video_response = await client.get(download_url)

            if video_response.status_code != 200:
                raise Exception(f"Failed to download video from CDN: {video_response.status_code}")

            return video_response.content
    
    async def close(self):
        await self.http_client.aclose()


# Singleton instance
_client: Optional[MiniMaxClient] = None

def get_client() -> MiniMaxClient:
    global _client
    if _client is None:
        _client = MiniMaxClient()
    return _client
