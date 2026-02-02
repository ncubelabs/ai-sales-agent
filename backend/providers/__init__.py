"""Provider abstraction layer for AI services.

This module provides a unified interface for text generation, TTS, and video
generation with support for multiple backend providers (MiniMax, vLLM, Coqui, SadTalker).
"""

from .base import TextProvider, TTSProvider, VideoProvider
from .config import ProviderConfig
from .registry import ProviderRegistry, get_registry

__all__ = [
    "TextProvider",
    "TTSProvider",
    "VideoProvider",
    "ProviderConfig",
    "ProviderRegistry",
    "get_registry",
]
