"""Edge TTS provider using Microsoft Edge's online TTS.

This is a lightweight alternative to Coqui XTTS that works on any Python version.
Note: Requires internet connection, no voice cloning support.
"""

import asyncio
import uuid
import logging
from pathlib import Path
from typing import Optional, Dict

from ..base import TTSProvider, TTSResult, VoiceCloneResult
from ..config import ProviderConfig

logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    """Text-to-speech using Microsoft Edge TTS (free, online).

    This provider uses edge-tts library which interfaces with Microsoft Edge's
    read-aloud feature. It's free, high-quality, and works on any Python version.

    Limitations:
    - Requires internet connection
    - No voice cloning (returns error if attempted)
    - Limited to Microsoft's voice selection

    Install with: pip install edge-tts
    """

    # Microsoft Edge TTS voices (subset of most useful ones)
    AVAILABLE_VOICES = {
        # English - US
        "en-US-JennyNeural": "US English, Female, conversational",
        "en-US-GuyNeural": "US English, Male, conversational",
        "en-US-AriaNeural": "US English, Female, professional",
        "en-US-DavisNeural": "US English, Male, professional",
        # English - UK
        "en-GB-SoniaNeural": "UK English, Female",
        "en-GB-RyanNeural": "UK English, Male",
        # Multilingual
        "zh-CN-XiaoxiaoNeural": "Chinese, Female",
        "zh-CN-YunxiNeural": "Chinese, Male",
        "ja-JP-NanamiNeural": "Japanese, Female",
        "de-DE-KatjaNeural": "German, Female",
        "fr-FR-DeniseNeural": "French, Female",
        "es-ES-ElviraNeural": "Spanish, Female",
        # Aliases for compatibility with MiniMax voice IDs
        "female-shaonv": "en-US-JennyNeural",  # Maps to Jenny
        "female-yujie": "en-US-AriaNeural",    # Maps to Aria
        "male-qn-qingse": "en-US-GuyNeural",   # Maps to Guy
        "male-qn-jingying": "en-US-DavisNeural",  # Maps to Davis
        "default": "en-US-JennyNeural",
    }

    # Voice aliases for compatibility
    VOICE_ALIASES = {
        "female-shaonv": "en-US-JennyNeural",
        "female-yujie": "en-US-AriaNeural",
        "male-qn-qingse": "en-US-GuyNeural",
        "male-qn-jingying": "en-US-DavisNeural",
        "default": "en-US-JennyNeural",
        "default_female": "en-US-JennyNeural",
        "default_male": "en-US-GuyNeural",
    }

    def __init__(self, config: ProviderConfig):
        self.config = config
        self._edge_tts = None

    def _ensure_initialized(self):
        """Lazy import of edge_tts."""
        if self._edge_tts is None:
            try:
                import edge_tts
                self._edge_tts = edge_tts
            except ImportError:
                raise ImportError(
                    "edge-tts not installed. Install with: pip install edge-tts"
                )

    @property
    def name(self) -> str:
        return "edge"

    def _resolve_voice(self, voice_id: str) -> str:
        """Resolve voice ID to Edge TTS voice name."""
        # Check aliases first
        if voice_id in self.VOICE_ALIASES:
            return self.VOICE_ALIASES[voice_id]

        # Check if it's already a valid Edge voice
        if voice_id in self.AVAILABLE_VOICES:
            return voice_id

        # Default fallback
        logger.warning(f"Unknown voice '{voice_id}', using default")
        return "en-US-JennyNeural"

    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        emotion: Optional[str] = None,
    ) -> TTSResult:
        """Synthesize speech using Edge TTS."""
        self._ensure_initialized()

        voice = self._resolve_voice(voice_id)

        # Convert speed to Edge TTS format (percentage adjustment)
        # speed=1.0 -> +0%, speed=0.5 -> -50%, speed=2.0 -> +100%
        rate_adjustment = int((speed - 1.0) * 100)
        rate = f"{rate_adjustment:+d}%"

        # Create communicate instance
        communicate = self._edge_tts.Communicate(text, voice, rate=rate)

        # Collect audio chunks
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        audio_bytes = b"".join(audio_chunks)

        # Estimate duration
        word_count = len(text.split())
        duration_estimate = (word_count / 150) * 60 / speed

        return TTSResult(
            audio_bytes=audio_bytes,
            format="mp3",
            sample_rate=24000,
            duration_estimate=duration_estimate,
        )

    async def clone_voice(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Voice cloning is not supported by Edge TTS.

        This will raise an error. Use Coqui XTTS or MiniMax for voice cloning.
        """
        raise NotImplementedError(
            "Edge TTS does not support voice cloning. "
            "Use Coqui XTTS (requires Python <3.12) or MiniMax API for voice cloning."
        )

    def list_voices(self) -> Dict[str, str]:
        """List available voices."""
        # Return only the real voices, not aliases
        return {
            k: v for k, v in self.AVAILABLE_VOICES.items()
            if not k.startswith("female-") and not k.startswith("male-") and k != "default"
        }

    async def close(self) -> None:
        """Clean up (no-op for Edge TTS)."""
        pass
