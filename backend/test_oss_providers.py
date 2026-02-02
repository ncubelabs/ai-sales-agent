#!/usr/bin/env python3
"""Test script for OSS provider migration.

Run this to verify your provider configuration is working.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from providers import get_registry
from providers.config import get_config
from services.ai_service import get_ai_service


async def test_text_provider():
    """Test text generation."""
    print("\n=== Testing Text Provider ===")
    try:
        ai = get_ai_service()
        provider = ai.text_provider
        print(f"Provider: {provider.name}")

        result = await provider.generate(
            prompt="Say 'Hello, OSS!' in a creative way.",
            max_tokens=50,
        )
        print(f"Response: {result.content[:100]}...")
        print("✓ Text provider working!")
        return True
    except Exception as e:
        print(f"✗ Text provider failed: {e}")
        return False


async def test_tts_provider():
    """Test TTS."""
    print("\n=== Testing TTS Provider ===")
    try:
        ai = get_ai_service()
        provider = ai.tts_provider
        print(f"Provider: {provider.name}")

        # List voices
        voices = provider.list_voices()
        print(f"Available voices: {list(voices.keys())[:3]}...")

        # Generate speech (short test)
        result = await provider.synthesize(
            text="Hello, this is a test of the text to speech system.",
            voice_id=list(voices.keys())[0] if voices else "default",
        )
        print(f"Audio size: {len(result.audio_bytes)} bytes")
        print("✓ TTS provider working!")
        return True
    except Exception as e:
        print(f"✗ TTS provider failed: {e}")
        return False


async def test_video_provider():
    """Test video provider info (not full generation)."""
    print("\n=== Testing Video Provider ===")
    try:
        ai = get_ai_service()
        provider = ai.video_provider
        print(f"Provider: {provider.name}")

        if provider.name == "sadtalker":
            print("SadTalker requires audio + face image.")
            print("Skipping full generation test (would require test files).")
        else:
            print("Video generation is expensive, skipping full test.")

        print("✓ Video provider loaded!")
        return True
    except Exception as e:
        print(f"✗ Video provider failed: {e}")
        return False


async def test_aiservice():
    """Test AIService methods."""
    print("\n=== Testing AIService ===")
    try:
        ai = get_ai_service()

        # Provider info
        info = ai.get_provider_info()
        print(f"Current providers: {info}")

        available = ai.list_available_providers()
        print(f"Available providers: {available}")

        print("✓ AIService working!")
        return True
    except Exception as e:
        print(f"✗ AIService failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("=" * 50)
    print("OSS Provider Migration Test")
    print("=" * 50)

    config = get_config()
    print(f"\nConfiguration:")
    print(f"  Text: {config.text_provider}")
    print(f"  TTS: {config.tts_provider}")
    print(f"  Video: {config.video_provider}")

    results = []

    # Test AIService first
    results.append(await test_aiservice())

    # Test text provider
    results.append(await test_text_provider())

    # Test TTS provider
    results.append(await test_tts_provider())

    # Test video provider
    results.append(await test_video_provider())

    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed. Check configuration.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
