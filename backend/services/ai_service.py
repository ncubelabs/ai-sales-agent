"""Unified AI Service layer for text, TTS, and video generation.

This module provides a high-level interface that abstracts away provider details.
It uses the provider registry for automatic fallback support.
"""

import logging
import re
import json
from typing import Optional, Dict, Any, List
from pathlib import Path

from providers import (
    ProviderRegistry,
    get_registry,
    TextProvider,
    TTSProvider,
    VideoProvider,
)
from providers.base import (
    TextGenerationResult,
    TTSResult,
    VoiceCloneResult,
    VideoGenerationResult,
)

logger = logging.getLogger(__name__)


class AIService:
    """Unified AI service for all generation tasks.

    Provides methods for:
    - Text generation (research, scripts)
    - Text-to-speech with voice cloning
    - Video generation (talking head, text-to-video)

    Uses provider registry for automatic fallback support.
    """

    def __init__(self, registry: Optional[ProviderRegistry] = None):
        self.registry = registry or get_registry()

    @property
    def text_provider(self) -> TextProvider:
        return self.registry.get_text_provider()

    @property
    def tts_provider(self) -> TTSProvider:
        return self.registry.get_tts_provider()

    @property
    def video_provider(self) -> VideoProvider:
        return self.registry.get_video_provider()

    # =========================================================================
    # Text Generation
    # =========================================================================

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text from a prompt.

        Args:
            prompt: The user prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system_prompt: Optional system prompt

        Returns:
            Generated text content
        """
        result = await self.text_provider.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt,
        )
        return result.content

    async def generate_research(
        self,
        research_prompt: str,
        scraped_data: str,
        company_url: str,
        company_name: str,
    ) -> Dict[str, Any]:
        """Generate company research profile.

        Args:
            research_prompt: Research prompt template
            scraped_data: Scraped company data
            company_url: Company URL
            company_name: Company name

        Returns:
            Parsed research JSON
        """
        # Fill in prompt template
        prompt = research_prompt
        prompt = prompt.replace("{company_url}", company_url)
        prompt = prompt.replace("{company_name}", company_name)
        prompt = prompt.replace("{additional_context}", "")
        prompt = prompt.replace("{scraped_data}", scraped_data)

        # Generate
        research_text = await self.generate_text(prompt)

        # Clean and parse response
        return self._parse_json_response(research_text)

    async def generate_script(
        self,
        script_prompt: str,
        research: Dict[str, Any],
        sender_name: str,
    ) -> str:
        """Generate sales script from research.

        Args:
            script_prompt: Script prompt template
            research: Research profile dict
            sender_name: Product/sender name

        Returns:
            Clean script text
        """
        # Fill in prompt template
        prompt = script_prompt
        prompt = prompt.replace("{research_profile}", json.dumps(research, indent=2))
        prompt = prompt.replace("{sender_name}", sender_name)

        # Generate
        script = await self.generate_text(prompt, max_tokens=1000)

        # Clean script
        return self._clean_script(script)

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown and think blocks."""
        clean_text = text.strip()

        # Remove <think>...</think> blocks (MiniMax/reasoning models)
        clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL).strip()

        # Remove markdown code blocks
        if clean_text.startswith("```"):
            parts = clean_text.split("```")
            if len(parts) >= 2:
                clean_text = parts[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]

        clean_text = clean_text.strip()

        # Find JSON object
        json_start = clean_text.find("{")
        json_end = clean_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            clean_text = clean_text[json_start:json_end]

        return json.loads(clean_text)

    def _clean_script(self, script: str) -> str:
        """Clean script text from LLM response."""
        clean_script = script.strip()

        # Remove <think> blocks
        clean_script = re.sub(r'<think>.*?</think>', '', clean_script, flags=re.DOTALL).strip()

        # Remove markdown formatting
        if clean_script.startswith("```"):
            parts = clean_script.split("```")
            if len(parts) >= 2:
                clean_script = parts[1].strip()

        # Extract just the script text (look for SCRIPT: marker)
        if "SCRIPT:" in clean_script:
            script_start = clean_script.find("SCRIPT:") + 7
            script_end = clean_script.find("WORD_COUNT:") if "WORD_COUNT:" in clean_script else len(clean_script)
            clean_script = clean_script[script_start:script_end].strip()

        return clean_script

    # =========================================================================
    # Text-to-Speech
    # =========================================================================

    async def generate_speech(
        self,
        text: str,
        voice_id: str = "female-shaonv",
        speed: float = 1.0,
        emotion: Optional[str] = None,
    ) -> bytes:
        """Generate speech audio from text.

        Args:
            text: Text to synthesize
            voice_id: Voice identifier
            speed: Speech speed multiplier
            emotion: Optional emotion modifier

        Returns:
            Audio bytes (MP3 format)
        """
        result = await self.tts_provider.synthesize(
            text=text,
            voice_id=voice_id,
            speed=speed,
            emotion=emotion,
        )
        return result.audio_bytes

    async def clone_voice(
        self,
        audio_bytes: bytes,
        voice_name: str,
        audio_filename: Optional[str] = None,
    ) -> VoiceCloneResult:
        """Clone a voice from audio sample.

        Args:
            audio_bytes: Audio sample bytes
            voice_name: Name for the cloned voice
            audio_filename: Original filename for format detection

        Returns:
            VoiceCloneResult with voice_id
        """
        return await self.tts_provider.clone_voice(
            audio_bytes=audio_bytes,
            voice_name=voice_name,
            audio_filename=audio_filename,
        )

    def list_voices(self) -> Dict[str, str]:
        """List available voices."""
        return self.tts_provider.list_voices()

    # =========================================================================
    # Video Generation
    # =========================================================================

    async def generate_video(
        self,
        prompt: str,
        duration: int = 6,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate video from text prompt.

        Args:
            prompt: Video description
            duration: Video duration in seconds
            **kwargs: Provider-specific options

        Returns:
            VideoGenerationResult with video bytes
        """
        return await self.video_provider.generate(
            prompt=prompt,
            duration=duration,
            **kwargs,
        )

    async def generate_talking_head(
        self,
        audio_path: str,
        face_image_path: str,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate talking head video.

        For MiniMax S2V-01, provide image_url in kwargs.
        For SadTalker, provide local file paths.

        Args:
            audio_path: Path to audio file
            face_image_path: Path to face image
            **kwargs: Provider-specific options (e.g., image_url for MiniMax)

        Returns:
            VideoGenerationResult with video bytes
        """
        return await self.video_provider.generate_talking_head(
            audio_path=audio_path,
            face_image_path=face_image_path,
            **kwargs,
        )

    # =========================================================================
    # Provider Info
    # =========================================================================

    def get_provider_info(self) -> Dict[str, str]:
        """Get current provider information."""
        return {
            "text": self.text_provider.name,
            "tts": self.tts_provider.name,
            "video": self.video_provider.name,
        }

    def list_available_providers(self) -> Dict[str, List[str]]:
        """List all available providers."""
        return self.registry.list_available_providers()

    async def close(self) -> None:
        """Close all provider connections."""
        await self.registry.close_all()


# Global service instance
_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get global AI service instance."""
    global _service
    if _service is None:
        _service = AIService()
    return _service


async def close_ai_service() -> None:
    """Close global AI service."""
    global _service
    if _service is not None:
        await _service.close()
        _service = None
