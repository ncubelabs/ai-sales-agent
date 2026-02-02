"""Coqui XTTS v2 TTS provider with voice cloning support.

This provider can work in two modes:
1. Service mode (default): Calls XTTS microservice via HTTP (works on any Python)
2. Direct mode: Loads model directly (requires Python 3.9-3.11)

The microservice mode is recommended for production as it:
- Works regardless of main app's Python version
- Isolates GPU memory usage
- Allows independent scaling
"""

import os
import io
import httpx
import logging
from pathlib import Path
from typing import Optional, Dict

from ..base import TTSProvider, TTSResult, VoiceCloneResult
from ..config import ProviderConfig

logger = logging.getLogger(__name__)


class CoquiTTSProvider(TTSProvider):
    """Text-to-speech using Coqui XTTS v2.

    By default, connects to the XTTS microservice running in Docker.
    Set PROVIDER_COQUI_MODE=direct to load the model directly (Python 3.9-3.11 only).
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.voices_dir = Path(config.coqui_voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)

        # Service URL (Docker container)
        self.service_url = os.getenv("PROVIDER_COQUI_SERVICE_URL", "http://localhost:5050")

        # Mode: "service" (default) or "direct"
        self.mode = os.getenv("PROVIDER_COQUI_MODE", "service")

        # For direct mode
        self._tts = None
        self._initialized = False

        # HTTP client for service mode
        self._http_client = None

    def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client for service mode."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url=self.service_url,
                timeout=300.0,  # TTS can take a while
            )
        return self._http_client

    async def _check_service(self) -> bool:
        """Check if XTTS service is running."""
        try:
            client = self._get_http_client()
            response = await client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    @property
    def name(self) -> str:
        return "coqui"

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        emotion: Optional[str] = None,
    ) -> TTSResult:
        """Synthesize speech using XTTS v2."""
        if self.mode == "service":
            return await self._synthesize_service(text, voice_id, speed)
        else:
            return await self._synthesize_direct(text, voice_id, speed)

    async def _synthesize_service(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> TTSResult:
        """Synthesize via XTTS microservice."""
        client = self._get_http_client()

        # Check service is running
        if not await self._check_service():
            raise ConnectionError(
                f"XTTS service not running at {self.service_url}. "
                "Start it with: docker-compose up -d xtts"
            )

        payload = {
            "text": text,
            "voice_id": voice_id,
            "language": "en",
            "speed": speed,
        }

        response = await client.post("/synthesize", json=payload)

        if response.status_code != 200:
            error = response.text
            raise Exception(f"XTTS service error: {error}")

        audio_bytes = response.content

        # Get format from content-type
        content_type = response.headers.get("content-type", "audio/mpeg")
        audio_format = "mp3" if "mpeg" in content_type else "wav"

        # Estimate duration
        word_count = len(text.split())
        duration_estimate = (word_count / 150) * 60 / speed

        return TTSResult(
            audio_bytes=audio_bytes,
            format=audio_format,
            sample_rate=24000,
            duration_estimate=duration_estimate,
        )

    async def _synthesize_direct(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> TTSResult:
        """Synthesize directly (requires Python 3.9-3.11)."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        self._ensure_initialized()

        # Get voice reference
        voice_path = self._get_voice_reference(voice_id)
        if not voice_path:
            raise ValueError(f"Voice '{voice_id}' not found. Clone a voice first.")

        # Run in thread pool (blocking operation)
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            audio_bytes = await loop.run_in_executor(
                executor,
                self._synthesize_sync,
                text,
                voice_path,
            )

        # Estimate duration
        word_count = len(text.split())
        duration_estimate = (word_count / 150) * 60 / speed

        return TTSResult(
            audio_bytes=audio_bytes,
            format="mp3",
            sample_rate=24000,
            duration_estimate=duration_estimate,
        )

    def _ensure_initialized(self):
        """Initialize TTS model for direct mode."""
        if self._initialized:
            return

        try:
            from TTS.api import TTS
        except ImportError:
            raise ImportError(
                "Coqui TTS not installed or Python version incompatible. "
                "Use service mode (docker-compose up -d xtts) or install: pip install TTS>=0.22.0"
            )

        logger.info(f"Loading XTTS v2 model on {self.config.coqui_device}...")
        self._tts = TTS(self.config.coqui_model).to(self.config.coqui_device)
        self._initialized = True
        logger.info("XTTS v2 model loaded")

    def _get_voice_reference(self, voice_id: str) -> Optional[str]:
        """Get reference audio path for a voice ID."""
        voice_path = self.voices_dir / f"{voice_id}.wav"
        if voice_path.exists():
            return str(voice_path)

        # Try without extension
        for ext in [".wav", ".mp3"]:
            path = self.voices_dir / f"{voice_id}{ext}"
            if path.exists():
                return str(path)

        return None

    def _synthesize_sync(self, text: str, voice_reference: str) -> bytes:
        """Synchronous synthesis for direct mode."""
        import uuid
        from pathlib import Path

        temp_path = Path(f"/tmp/tts_{uuid.uuid4().hex}.wav")

        try:
            self._tts.tts_to_file(
                text=text,
                speaker_wav=voice_reference,
                language="en",
                file_path=str(temp_path),
            )

            audio_bytes = temp_path.read_bytes()

            # Convert to MP3
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                mp3_buffer = io.BytesIO()
                audio.export(mp3_buffer, format="mp3", bitrate="192k")
                mp3_buffer.seek(0)
                return mp3_buffer.read()
            except Exception:
                return audio_bytes

        finally:
            if temp_path.exists():
                temp_path.unlink()

    async def clone_voice(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Clone a voice from audio sample."""
        if self.mode == "service":
            return await self._clone_voice_service(audio_bytes, voice_name, audio_filename)
        else:
            return await self._clone_voice_direct(audio_bytes, voice_name, audio_filename)

    async def _clone_voice_service(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Clone voice via XTTS microservice."""
        client = self._get_http_client()

        if not await self._check_service():
            raise ConnectionError(
                f"XTTS service not running at {self.service_url}. "
                "Start it with: docker-compose up -d xtts"
            )

        filename = audio_filename or "audio.wav"
        files = {"audio": (filename, audio_bytes)}
        data = {"name": voice_name}

        response = await client.post("/clone", files=files, data=data)

        if response.status_code != 200:
            error = response.text
            raise Exception(f"XTTS clone error: {error}")

        result = response.json()

        return VoiceCloneResult(
            voice_id=result["voice_id"],
            name=result["name"],
            provider="coqui",
        )

    async def _clone_voice_direct(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Clone voice directly (save reference audio)."""
        import uuid

        filename = audio_filename or "audio.wav"
        ext = filename.lower().split(".")[-1] if "." in filename else "wav"

        # Generate voice ID
        safe_name = "".join(c if c.isalnum() else "_" for c in voice_name.lower())
        voice_id = f"cloned_{safe_name}_{uuid.uuid4().hex[:8]}"

        voice_path = self.voices_dir / f"{voice_id}.wav"

        # Convert to WAV if needed
        if ext in ["mp3", "m4a", "ogg"]:
            try:
                from pydub import AudioSegment

                if ext == "mp3":
                    audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
                else:
                    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)

                audio.export(str(voice_path), format="wav")
            except ImportError:
                raise ImportError("pydub required for audio conversion")
        else:
            voice_path.write_bytes(audio_bytes)

        logger.info(f"Voice cloned: {voice_id} -> {voice_path}")

        return VoiceCloneResult(
            voice_id=voice_id,
            name=voice_name,
            provider="coqui",
        )

    def list_voices(self) -> Dict[str, str]:
        """List available voices."""
        voices = {}

        # List cloned voices from local directory
        for wav_file in self.voices_dir.glob("*.wav"):
            voice_id = wav_file.stem
            voices[voice_id] = f"Cloned: {voice_id}"

        if not voices:
            voices["_no_voices"] = "No voices cloned yet. Clone a voice first."

        return voices

    async def close(self) -> None:
        """Clean up resources."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

        if self._tts is not None:
            del self._tts
            self._tts = None
            self._initialized = False
