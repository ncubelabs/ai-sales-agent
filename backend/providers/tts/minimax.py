"""MiniMax TTS provider with voice cloning support."""

import httpx
from typing import Optional, Dict

from ..base import TTSProvider, TTSResult, VoiceCloneResult
from ..config import ProviderConfig


class MiniMaxTTSProvider(TTSProvider):
    """Text-to-speech using MiniMax Speech API."""

    AVAILABLE_VOICES = {
        "female-shaonv": "Young female, energetic",
        "female-yujie": "Mature female, professional",
        "male-qn-qingse": "Young male, fresh",
        "male-qn-jingying": "Male, business professional",
        "presenter_male": "Male presenter voice",
        "presenter_female": "Female presenter voice",
    }

    def __init__(self, config: ProviderConfig):
        self.config = config

        if not config.minimax_api_key:
            raise ValueError("MINIMAX_API_KEY not set")

        if not config.minimax_group_id:
            raise ValueError(
                "MINIMAX_GROUP_ID not set. "
                "Find it at: https://www.minimax.io/platform/user-center/basic-information"
            )

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

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        emotion: Optional[str] = None,
    ) -> TTSResult:
        """Generate speech using MiniMax Speech TTS."""
        payload = {
            "model": "speech-02-hd",
            "text": text,
            "stream": False,
            "voice_setting": {
                "voice_id": voice_id,
                "speed": speed,
                "vol": 1.0,
                "pitch": 0,
            },
            "audio_setting": {
                "format": "mp3",
                "sample_rate": 32000,
            },
        }

        response = await self.http_client.post(
            f"/t2a_v2?GroupId={self.config.minimax_group_id}",
            json=payload,
        )

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax TTS API error {response.status_code}: {error_text}")

        data = response.json()

        # Check for API-level errors
        if data.get("base_resp", {}).get("status_code") != 0:
            raise Exception(
                f"MiniMax TTS error: {data.get('base_resp', {}).get('status_msg')} "
                f"(Response: {data})"
            )

        # Audio is hex-encoded in the response
        audio_hex = data.get("data", {}).get("audio") or data.get("audio_file")
        if not audio_hex:
            raise Exception(f"No audio in response: {data}")

        audio_bytes = bytes.fromhex(audio_hex)

        # Estimate duration (~150 words/min at speed 1.0)
        word_count = len(text.split())
        duration_estimate = (word_count / 150) * 60 / speed

        return TTSResult(
            audio_bytes=audio_bytes,
            format="mp3",
            sample_rate=32000,
            duration_estimate=duration_estimate,
        )

    async def clone_voice(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Clone a voice from audio sample using MiniMax Voice Clone API."""
        filename = audio_filename or "audio.mp3"

        # Determine content type from filename
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        content_type_map = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "m4a": "audio/mp4",
        }
        content_type = content_type_map.get(ext, "audio/mpeg")

        # Step 1: Upload the audio file
        files = {"file": (filename, audio_bytes, content_type)}
        data = {"purpose": "voice_clone"}

        upload_url = f"/files/upload?GroupId={self.config.minimax_group_id}"

        async with httpx.AsyncClient(
            base_url=self.config.minimax_base_url,
            headers={"Authorization": f"Bearer {self.config.minimax_api_key}"},
            timeout=120.0,
        ) as upload_client:
            response = await upload_client.post(upload_url, files=files, data=data)

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax file upload error {response.status_code}: {error_text}")

        resp_data = response.json()

        base_resp = resp_data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            raise Exception(
                f"MiniMax upload error: {base_resp.get('status_msg')} "
                f"(Response: {resp_data})"
            )

        file_id = resp_data.get("file", {}).get("file_id")
        if not file_id:
            raise Exception(f"No file_id in upload response: {resp_data}")

        # Step 2: Clone the voice
        payload = {
            "file_id": int(file_id),
            "voice_id": voice_name,
        }

        response = await self.http_client.post(
            f"/voice_clone?GroupId={self.config.minimax_group_id}",
            json=payload,
        )

        if response.status_code != 200:
            error_text = response.text
            raise Exception(f"MiniMax voice clone error {response.status_code}: {error_text}")

        data = response.json()

        base_resp = data.get("base_resp", {})
        if base_resp.get("status_code") != 0:
            error_msg = base_resp.get("status_msg", "Unknown error")
            raise Exception(f"MiniMax voice clone error: {error_msg} (Response: {data})")

        return VoiceCloneResult(
            voice_id=voice_name,
            name=voice_name,
            provider="minimax",
        )

    def list_voices(self) -> Dict[str, str]:
        """List available built-in voices."""
        return self.AVAILABLE_VOICES.copy()

    async def close(self) -> None:
        await self.http_client.aclose()
