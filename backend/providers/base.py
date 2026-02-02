"""Abstract base classes for provider implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from pathlib import Path


@dataclass
class TextGenerationResult:
    """Result from text generation."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None


@dataclass
class TTSResult:
    """Result from text-to-speech generation."""
    audio_bytes: bytes
    format: str = "mp3"
    sample_rate: int = 32000
    duration_estimate: Optional[float] = None


@dataclass
class VoiceCloneResult:
    """Result from voice cloning."""
    voice_id: str
    name: str
    provider: str


@dataclass
class VideoGenerationResult:
    """Result from video generation."""
    video_bytes: Optional[bytes] = None
    video_path: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "completed"
    duration: Optional[int] = None


class TextProvider(ABC):
    """Abstract base class for text generation providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> TextGenerationResult:
        """Generate text from a prompt.

        Args:
            prompt: The user prompt to generate from
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            system_prompt: Optional system prompt

        Returns:
            TextGenerationResult with generated content
        """
        pass

    async def close(self) -> None:
        """Clean up resources."""
        pass


class TTSProvider(ABC):
    """Abstract base class for text-to-speech providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        emotion: Optional[str] = None,
    ) -> TTSResult:
        """Synthesize speech from text.

        Args:
            text: Text to synthesize
            voice_id: Voice identifier (builtin or cloned)
            speed: Speech speed multiplier
            emotion: Optional emotion modifier

        Returns:
            TTSResult with audio bytes
        """
        pass

    @abstractmethod
    async def clone_voice(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Clone a voice from audio sample.

        Args:
            audio_bytes: Audio sample bytes (10s-5min recommended)
            voice_name: Name for the cloned voice
            audio_filename: Original filename for format detection

        Returns:
            VoiceCloneResult with voice_id for TTS
        """
        pass

    @abstractmethod
    def list_voices(self) -> Dict[str, str]:
        """List available built-in voices.

        Returns:
            Dict mapping voice_id to description
        """
        pass

    async def close(self) -> None:
        """Clean up resources."""
        pass


class VideoProvider(ABC):
    """Abstract base class for video generation providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        duration: int = 6,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate video from prompt.

        Args:
            prompt: Text description of the video
            duration: Video duration in seconds
            **kwargs: Provider-specific options

        Returns:
            VideoGenerationResult with video bytes or path
        """
        pass

    @abstractmethod
    async def generate_talking_head(
        self,
        audio_path: str,
        face_image_path: str,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate talking head video from audio and face image.

        Args:
            audio_path: Path to audio file
            face_image_path: Path to face image
            **kwargs: Provider-specific options

        Returns:
            VideoGenerationResult with video bytes or path
        """
        pass

    async def close(self) -> None:
        """Clean up resources."""
        pass
