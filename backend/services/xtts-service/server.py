#!/usr/bin/env python3
"""XTTS v2 Microservice - Voice Synthesis and Cloning API

This service wraps Coqui XTTS v2 in a simple REST API for use by the main
AI Sales Agent backend. It runs in a Docker container with Python 3.11.

Endpoints:
- POST /synthesize - Generate speech from text
- POST /clone - Clone a voice from audio sample
- GET /voices - List available voices
- GET /health - Health check
"""

import os
import io
import uuid
import logging
from pathlib import Path
from typing import Optional

import torch
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directories
MODELS_DIR = Path("/app/models")
VOICES_DIR = Path("/app/voices")
MODELS_DIR.mkdir(exist_ok=True)
VOICES_DIR.mkdir(exist_ok=True)

# App
app = FastAPI(
    title="XTTS v2 Service",
    description="Voice synthesis and cloning microservice",
    version="1.0.0"
)

# Global TTS instance (lazy loaded)
_tts = None


def get_tts():
    """Lazy load TTS model."""
    global _tts
    if _tts is None:
        logger.info("Loading XTTS v2 model...")
        from TTS.api import TTS

        # Check for GPU
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")

        # Load model
        _tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        logger.info("XTTS v2 model loaded successfully")

    return _tts


class SynthesizeRequest(BaseModel):
    text: str
    voice_id: str
    language: str = "en"
    speed: float = 1.0


class CloneResponse(BaseModel):
    voice_id: str
    name: str
    message: str


class VoiceInfo(BaseModel):
    id: str
    name: str
    type: str  # "cloned" or "default"


@app.on_event("startup")
async def startup():
    """Pre-load model on startup."""
    logger.info("XTTS Service starting...")
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"GPU: {torch.cuda.get_device_name(0)}")

    # Optionally pre-load model (comment out to lazy load)
    # get_tts()


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "cuda": torch.cuda.is_available(),
        "model_loaded": _tts is not None
    }


@app.get("/voices")
async def list_voices():
    """List available voices."""
    voices = []

    # List cloned voices
    for wav_file in VOICES_DIR.glob("*.wav"):
        voice_id = wav_file.stem
        voices.append(VoiceInfo(
            id=voice_id,
            name=voice_id.replace("_", " ").title(),
            type="cloned"
        ))

    # Add default voice info
    if not voices:
        voices.append(VoiceInfo(
            id="_none",
            name="No voices cloned yet",
            type="info"
        ))

    return {"voices": voices}


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """Synthesize speech from text.

    Returns audio bytes (WAV format).
    """
    try:
        tts = get_tts()

        # Get voice reference
        voice_path = VOICES_DIR / f"{request.voice_id}.wav"
        if not voice_path.exists():
            # Try to find any voice file as fallback
            voice_files = list(VOICES_DIR.glob("*.wav"))
            if voice_files:
                voice_path = voice_files[0]
                logger.warning(f"Voice '{request.voice_id}' not found, using {voice_path.name}")
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Voice '{request.voice_id}' not found and no fallback available. Clone a voice first."
                )

        # Generate speech to temp file
        temp_path = Path(f"/tmp/tts_{uuid.uuid4().hex}.wav")

        try:
            tts.tts_to_file(
                text=request.text,
                speaker_wav=str(voice_path),
                language=request.language,
                file_path=str(temp_path),
            )

            # Read audio bytes
            audio_bytes = temp_path.read_bytes()

            # Convert to MP3 for smaller size
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(io.BytesIO(audio_bytes))
                mp3_buffer = io.BytesIO()
                audio.export(mp3_buffer, format="mp3", bitrate="192k")
                mp3_buffer.seek(0)
                audio_bytes = mp3_buffer.read()
                content_type = "audio/mpeg"
            except Exception as e:
                logger.warning(f"MP3 conversion failed: {e}, returning WAV")
                content_type = "audio/wav"

            return Response(
                content=audio_bytes,
                media_type=content_type,
                headers={"X-Voice-Used": voice_path.stem}
            )

        finally:
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Synthesis failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clone", response_model=CloneResponse)
async def clone_voice(
    audio: UploadFile = File(..., description="Audio sample (WAV/MP3, 10s-5min)"),
    name: str = Form(..., description="Name for this voice")
):
    """Clone a voice from an audio sample.

    The audio sample should be 10 seconds to 5 minutes of clear speech.
    Saves the reference audio for use with /synthesize.
    """
    try:
        # Read uploaded audio
        audio_bytes = await audio.read()
        filename = audio.filename or "audio.wav"

        # Generate voice ID
        safe_name = "".join(c if c.isalnum() else "_" for c in name.lower())
        voice_id = f"cloned_{safe_name}_{uuid.uuid4().hex[:8]}"

        # Determine format and convert to WAV if needed
        ext = filename.lower().split(".")[-1] if "." in filename else "wav"
        voice_path = VOICES_DIR / f"{voice_id}.wav"

        if ext in ["mp3", "m4a", "ogg", "flac"]:
            # Convert to WAV
            from pydub import AudioSegment

            if ext == "mp3":
                audio = AudioSegment.from_mp3(io.BytesIO(audio_bytes))
            elif ext == "m4a":
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="m4a")
            else:
                audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)

            # Export as WAV (mono, 22050 Hz for XTTS)
            audio = audio.set_channels(1).set_frame_rate(22050)
            audio.export(str(voice_path), format="wav")
        else:
            # Assume WAV
            voice_path.write_bytes(audio_bytes)

        logger.info(f"Voice cloned: {voice_id} -> {voice_path}")

        return CloneResponse(
            voice_id=voice_id,
            name=name,
            message=f"Voice '{name}' cloned successfully. Use voice_id '{voice_id}' for synthesis."
        )

    except Exception as e:
        logger.exception("Voice cloning failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/voices/{voice_id}")
async def delete_voice(voice_id: str):
    """Delete a cloned voice."""
    voice_path = VOICES_DIR / f"{voice_id}.wav"

    if not voice_path.exists():
        raise HTTPException(status_code=404, detail="Voice not found")

    voice_path.unlink()
    return {"message": f"Voice '{voice_id}' deleted"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 5050))
    uvicorn.run(app, host="0.0.0.0", port=port)
