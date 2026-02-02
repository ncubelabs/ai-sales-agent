"""Provider registry with factory pattern and fallback support."""

import logging
from typing import Dict, Type, Optional, List, TypeVar, Generic

from .base import TextProvider, TTSProvider, VideoProvider
from .config import ProviderConfig, get_config

logger = logging.getLogger(__name__)

T = TypeVar("T", TextProvider, TTSProvider, VideoProvider)


class ProviderRegistry:
    """Registry for provider implementations with fallback support."""

    def __init__(self, config: Optional[ProviderConfig] = None):
        self.config = config or get_config()

        # Registered provider classes
        self._text_providers: Dict[str, Type[TextProvider]] = {}
        self._tts_providers: Dict[str, Type[TTSProvider]] = {}
        self._video_providers: Dict[str, Type[VideoProvider]] = {}

        # Instantiated providers (singletons)
        self._text_instances: Dict[str, TextProvider] = {}
        self._tts_instances: Dict[str, TTSProvider] = {}
        self._video_instances: Dict[str, VideoProvider] = {}

        # Register built-in providers
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register built-in provider implementations."""
        # Import here to avoid circular imports
        try:
            from .text.minimax import MiniMaxTextProvider
            self._text_providers["minimax"] = MiniMaxTextProvider
        except ImportError as e:
            logger.warning(f"MiniMax text provider not available: {e}")

        try:
            from .text.vllm import VLLMTextProvider
            self._text_providers["vllm"] = VLLMTextProvider
        except ImportError as e:
            logger.debug(f"vLLM text provider not available: {e}")

        try:
            from .tts.minimax import MiniMaxTTSProvider
            self._tts_providers["minimax"] = MiniMaxTTSProvider
        except ImportError as e:
            logger.warning(f"MiniMax TTS provider not available: {e}")

        try:
            from .tts.coqui import CoquiTTSProvider
            self._tts_providers["coqui"] = CoquiTTSProvider
        except ImportError as e:
            logger.debug(f"Coqui TTS provider not available: {e}")

        try:
            from .tts.edge import EdgeTTSProvider
            self._tts_providers["edge"] = EdgeTTSProvider
        except ImportError as e:
            logger.debug(f"Edge TTS provider not available: {e}")

        try:
            from .video.minimax import MiniMaxVideoProvider
            self._video_providers["minimax"] = MiniMaxVideoProvider
        except ImportError as e:
            logger.warning(f"MiniMax video provider not available: {e}")

        try:
            from .video.sadtalker import SadTalkerVideoProvider
            self._video_providers["sadtalker"] = SadTalkerVideoProvider
        except ImportError as e:
            logger.debug(f"SadTalker video provider not available: {e}")

    def register_text_provider(
        self, name: str, provider_class: Type[TextProvider]
    ) -> None:
        """Register a text provider implementation."""
        self._text_providers[name.lower()] = provider_class

    def register_tts_provider(
        self, name: str, provider_class: Type[TTSProvider]
    ) -> None:
        """Register a TTS provider implementation."""
        self._tts_providers[name.lower()] = provider_class

    def register_video_provider(
        self, name: str, provider_class: Type[VideoProvider]
    ) -> None:
        """Register a video provider implementation."""
        self._video_providers[name.lower()] = provider_class

    def _get_provider_instance(
        self,
        name: str,
        providers: Dict[str, Type[T]],
        instances: Dict[str, T],
        fallback_chain: List[str],
        provider_type: str,
    ) -> T:
        """Get or create a provider instance with fallback support."""
        # Try primary provider first
        chain = [name] + [p for p in fallback_chain if p != name]

        last_error = None
        for provider_name in chain:
            provider_name = provider_name.lower()

            # Return cached instance if available
            if provider_name in instances:
                return instances[provider_name]

            # Try to create new instance
            if provider_name in providers:
                try:
                    provider_class = providers[provider_name]
                    instance = provider_class(self.config)
                    instances[provider_name] = instance

                    if provider_name != name:
                        logger.info(
                            f"Using fallback {provider_type} provider: {provider_name}"
                        )

                    return instance
                except Exception as e:
                    last_error = e
                    logger.warning(
                        f"Failed to initialize {provider_type} provider '{provider_name}': {e}"
                    )
            else:
                logger.debug(f"{provider_type} provider '{provider_name}' not registered")

        raise RuntimeError(
            f"No available {provider_type} provider. "
            f"Tried: {chain}. Last error: {last_error}"
        )

    def get_text_provider(self, name: Optional[str] = None) -> TextProvider:
        """Get text provider instance."""
        provider_name = name or self.config.text_provider
        return self._get_provider_instance(
            provider_name,
            self._text_providers,
            self._text_instances,
            self.config.text_fallback,
            "text",
        )

    def get_tts_provider(self, name: Optional[str] = None) -> TTSProvider:
        """Get TTS provider instance."""
        provider_name = name or self.config.tts_provider
        return self._get_provider_instance(
            provider_name,
            self._tts_providers,
            self._tts_instances,
            self.config.tts_fallback,
            "TTS",
        )

    def get_video_provider(self, name: Optional[str] = None) -> VideoProvider:
        """Get video provider instance."""
        provider_name = name or self.config.video_provider
        return self._get_provider_instance(
            provider_name,
            self._video_providers,
            self._video_instances,
            self.config.video_fallback,
            "video",
        )

    def list_available_providers(self) -> Dict[str, List[str]]:
        """List all registered providers by type."""
        return {
            "text": list(self._text_providers.keys()),
            "tts": list(self._tts_providers.keys()),
            "video": list(self._video_providers.keys()),
        }

    async def close_all(self) -> None:
        """Close all provider instances."""
        for instance in self._text_instances.values():
            await instance.close()
        for instance in self._tts_instances.values():
            await instance.close()
        for instance in self._video_instances.values():
            await instance.close()

        self._text_instances.clear()
        self._tts_instances.clear()
        self._video_instances.clear()


# Global registry instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get global provider registry."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None
