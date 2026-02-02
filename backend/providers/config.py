"""Provider configuration from environment variables."""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ProviderConfig:
    """Configuration for all providers, loaded from environment."""

    # Provider selection
    text_provider: str = "minimax"
    tts_provider: str = "minimax"
    video_provider: str = "minimax"

    # Fallback chains
    text_fallback: List[str] = field(default_factory=lambda: ["minimax"])
    tts_fallback: List[str] = field(default_factory=lambda: ["minimax"])
    video_fallback: List[str] = field(default_factory=lambda: ["minimax"])

    # MiniMax config
    minimax_api_key: Optional[str] = None
    minimax_group_id: Optional[str] = None
    minimax_base_url: str = "https://api.minimax.io/v1"

    # vLLM config
    vllm_base_url: str = "http://localhost:8000"
    vllm_model: str = "meta-llama/Llama-3.1-70B-Instruct"
    vllm_api_key: Optional[str] = None

    # Coqui XTTS config
    coqui_device: str = "cuda"
    coqui_model: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    coqui_voices_dir: str = "./voices"

    # SadTalker config
    sadtalker_checkpoint: str = "./models/sadtalker"
    sadtalker_device: str = "cuda"
    sadtalker_preprocess: str = "crop"  # crop, resize, full
    sadtalker_still: bool = False
    sadtalker_enhancer: Optional[str] = None  # gfpgan, RestoreFormer

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        """Load configuration from environment variables."""

        def parse_fallback(value: Optional[str], default: List[str]) -> List[str]:
            if not value:
                return default
            return [v.strip() for v in value.split(",") if v.strip()]

        return cls(
            # Provider selection
            text_provider=os.getenv("PROVIDER_TEXT", "minimax").lower(),
            tts_provider=os.getenv("PROVIDER_TTS", "minimax").lower(),
            video_provider=os.getenv("PROVIDER_VIDEO", "minimax").lower(),

            # Fallback chains
            text_fallback=parse_fallback(
                os.getenv("PROVIDER_TEXT_FALLBACK"),
                ["vllm", "minimax"]
            ),
            tts_fallback=parse_fallback(
                os.getenv("PROVIDER_TTS_FALLBACK"),
                ["coqui", "minimax"]
            ),
            video_fallback=parse_fallback(
                os.getenv("PROVIDER_VIDEO_FALLBACK"),
                ["sadtalker", "minimax"]
            ),

            # MiniMax
            minimax_api_key=os.getenv("MINIMAX_API_KEY"),
            minimax_group_id=os.getenv("MINIMAX_GROUP_ID"),
            minimax_base_url=os.getenv("MINIMAX_BASE_URL", "https://api.minimax.io/v1"),

            # vLLM
            vllm_base_url=os.getenv("PROVIDER_VLLM_BASE_URL", "http://localhost:8000"),
            vllm_model=os.getenv("PROVIDER_VLLM_MODEL", "meta-llama/Llama-3.1-70B-Instruct"),
            vllm_api_key=os.getenv("PROVIDER_VLLM_API_KEY"),

            # Coqui
            coqui_device=os.getenv("PROVIDER_COQUI_DEVICE", "cuda"),
            coqui_model=os.getenv(
                "PROVIDER_COQUI_MODEL",
                "tts_models/multilingual/multi-dataset/xtts_v2"
            ),
            coqui_voices_dir=os.getenv("PROVIDER_COQUI_VOICES_DIR", "./voices"),

            # SadTalker
            sadtalker_checkpoint=os.getenv("PROVIDER_SADTALKER_CHECKPOINT", "./models/sadtalker"),
            sadtalker_device=os.getenv("PROVIDER_SADTALKER_DEVICE", "cuda"),
            sadtalker_preprocess=os.getenv("PROVIDER_SADTALKER_PREPROCESS", "crop"),
            sadtalker_still=os.getenv("PROVIDER_SADTALKER_STILL", "false").lower() == "true",
            sadtalker_enhancer=os.getenv("PROVIDER_SADTALKER_ENHANCER"),
        )


# Global config instance
_config: Optional[ProviderConfig] = None


def get_config() -> ProviderConfig:
    """Get global provider configuration."""
    global _config
    if _config is None:
        _config = ProviderConfig.from_env()
    return _config


def reload_config() -> ProviderConfig:
    """Reload configuration from environment."""
    global _config
    _config = ProviderConfig.from_env()
    return _config
