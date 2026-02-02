#!/usr/bin/env python3
"""TTS Microservice using Edge TTS (Microsoft's free TTS API)

This service provides a simple REST API for text-to-speech using Edge TTS.
It maintains the same interface as the XTTS service for drop-in replacement.

Endpoints:
- POST /synthesize - Generate speech from text
- POST /clone - Store a voice reference (for future XTTS support)
- GET /voices - List available voices
- GET /health - Health check
"""

import os
import io
import uuid
import logging
import asyncio
from pathlib import Path
from typing import Optional, List

import edge_tts
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
VOICES_DIR = Path("/app/voices")
VOICES_DIR.mkdir(exist_ok=True)

# Default Edge TTS voices (high quality)
EDGE_VOICES = {
    # English
    "en-US-AriaNeural": {"name": "Aria (US)", "language": "en", "gender": "female"},
    "en-US-GuyNeural": {"name": "Guy (US)", "language": "en", "gender": "male"},
    "en-US-JennyNeural": {"name": "Jenny (US)", "language": "en", "gender": "female"},
    "en-GB-SoniaNeural": {"name": "Sonia (UK)", "language": "en", "gender": "female"},
    "en-GB-RyanNeural": {"name": "Ryan (UK)", "language": "en", "gender": "male"},
    # Chinese
    "zh-CN-XiaoxiaoNeural": {"name": "Xiaoxiao", "language": "zh", "gender": "female"},
    "zh-CN-YunxiNeural": {"name": "Yunxi", "language": "zh", "gender": "male"},
    # Japanese
    "ja-JP-NanamiNeural": {"name": "Nanami", "language": "ja", "gender": "female"},
    # Spanish
    "es-ES-ElviraNeural": {"name": "Elvira", "language": "es", "gender": "female"},
    # French
    "fr-FR-DeniseNeural": {"name": "Denise", "language": "fr", "gender": "female"},
}

# Default voice
DEFAULT_VOICE = "en-US-AriaNeural"

# App
app = FastAPI(
    title="TTS Service (Edge TTS)",
    description="Text-to-speech microservice using Microsoft Edge TTS",
    version="1.0.0"
)


class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str = DEFAULT_VOICE
    language: str = "en"
    speed: float = 1.0


class CloneResponse(BaseModel):
    voice_id: str
    name: str
    message: str


class VoiceInfo(BaseModel):
    id: str
    name: str
    type: str  # "edge" or "cloned"


@app.on_event("startup")
async def startup():
    """Log startup info."""
    logger.info("TTS Service (Edge TTS) starting...")
    logger.info(f"Available voices: {len(EDGE_VOICES)}")


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "cuda": False,  # Edge TTS doesn't need GPU
        "model_loaded": True,  # Edge TTS is always ready
        "backend": "edge-tts"
    }


@app.get("/voices")
async def list_voices():
    """List available voices."""
    voices = []

    # List Edge TTS voices
    for voice_id, info in EDGE_VOICES.items():
        voices.append(VoiceInfo(
            id=voice_id,
            name=info["name"],
            type="edge"
        ))

    # List any cloned voice references (for future XTTS support)
    for wav_file in VOICES_DIR.glob("*.wav"):
        voice_id = wav_file.stem
        voices.append(VoiceInfo(
            id=voice_id,
            name=voice_id.replace("_", " ").title(),
            type="cloned"
        ))

    return {"voices": voices}


def get_edge_voice_for_language(language: str, voice_id: str = None) -> str:
    """Get an appropriate Edge TTS voice for the given language."""
    # If voice_id is a valid Edge TTS voice, use it
    if voice_id in EDGE_VOICES:
        return voice_id

    # Map language codes to default voices
    lang_voices = {
        "en": "en-US-AriaNeural",
        "zh": "zh-CN-XiaoxiaoNeural",
        "ja": "ja-JP-NanamiNeural",
        "es": "es-ES-ElviraNeural",
        "fr": "fr-FR-DeniseNeural",
    }

    return lang_voices.get(language, DEFAULT_VOICE)


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Synthesize speech from text using Edge TTS.

    Returns audio bytes (MP3 format).
    """
    try:
        # Get appropriate voice
        voice = get_edge_voice_for_language(request.language, request.voice_id)

        # Calculate rate adjustment
        rate = f"+{int((request.speed - 1) * 100)}%" if request.speed >= 1 else f"{int((request.speed - 1) * 100)}%"

        # Create Edge TTS communicator
        communicate = edge_tts.Communicate(
            text=request.text,
            voice=voice,
            rate=rate
        )

        # Collect audio chunks
        audio_chunks = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])

        if not audio_chunks:
            raise HTTPException(status_code=500, detail="No audio generated")

        # Combine audio chunks
        audio_bytes = b"".join(audio_chunks)

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={"X-Voice-Used": voice}
        )

    except Exception as e:
        logger.exception("Synthesis failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clone", response_model=CloneResponse)
async def clone_voice(
    audio: UploadFile = File(..., description="Audio sample (WAV/MP3, 10s-5min)"),
    name: str = Form(..., description="Name for this voice")
):
    """Store a voice reference for future XTTS support.

    Note: Edge TTS doesn't support voice cloning. This stores the reference
    audio for future use when XTTS is properly configured.
    """
    try:
        # Read uploaded audio
        audio_bytes = await audio.read()
        filename = audio.filename or "audio.wav"

        # Generate voice ID
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        voice_id = f"cloned_{safe_name}_{uuid.uuid4().hex[:8]}"

        # Save audio (convert to WAV if needed)
        ext = filename.lower().split(".")[-1] if "." in filename else "wav"
        voice_path = VOICES_DIR / f"{voice_id}.wav"

        if ext in ["mp3", "m4a", "ogg", "flac"]:
            from pydub import AudioSegment

            if ext == "mp3":
                audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            elif ext == "m4a":
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="m4a")
            else:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)

            audio = audio.set_channels(1).set_frame_rate(22050)
            audio.export(str(voice_path), format="wav")
        else:
            voice_path.write_bytes(audio_bytes)

        logger.info(f"Voice reference saved: {voice_id} -> {voice_path}")

        return CloneResponse(
            voice_id=voice_id,
            name=name,
            message=f"Voice reference '{name}' saved. Note: Edge TTS uses preset voices. "
                    f"Use voice_id '{voice_id}' with XTTS when available, or use an Edge voice."
        )

    except Exception as e:
        logger.exception("Voice reference save failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a cloned voice reference."""
    voice_path = VOICES_DIR / f"{voice_id}.wav"

    if not voice_path.exists():
        raise HTTPException(status_code=404, detail="Voice not found")

    voice_path.unlink()
    return {"message": f"Voice reference '{voice_id}' deleted"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5050))
    uvicorn.run(app, host="0.0.0.0", port=port)
