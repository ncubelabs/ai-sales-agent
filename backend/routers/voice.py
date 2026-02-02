"""Voice/TTS endpoint with voice cloning support"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from pathlib import Path
import uuid

from services.ai_service import get_ai_service
from services.voice_profile import (
    create_voice_profile,
    get_voice_profile,
    list_voice_profiles,
    delete_voice_profile,
    VoiceProfile,
)
from services.asset_storage import AssetValidationError

router = APIRouter(prefix="/api", tags=["voice"])

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


class VoiceRequest(BaseModel):
    text: str
    voice_id: str = "female-shaonv"  # Options: female-shaonv, male-qn-qingse, or cloned voice ID
    speed: float = 1.0
    emotion: str = "happy"  # Options: happy, sad, angry, fearful, disgusted, surprised, neutral


class VoiceResponse(BaseModel):
    audio_path: str
    duration_estimate: int  # seconds
    file_size: int  # bytes


class VoiceCloneResponse(BaseModel):
    profile_id: str
    name: str
    voice_id: str
    message: str


class VoiceProfileResponse(BaseModel):
    id: str
    name: str
    voice_id: str
    created_at: str
    audio_duration_estimate: Optional[int] = None


class VoiceProfileListResponse(BaseModel):
    profiles: List[VoiceProfileResponse]


@router.post("/voice", response_model=VoiceResponse)
async def generate_voice(request: VoiceRequest):
    """Generate voice audio from text using configured TTS provider"""

    try:
        ai = get_ai_service()

        # Generate audio
        audio_bytes = await ai.generate_speech(
            text=request.text,
            voice_id=request.voice_id,
            speed=request.speed,
            emotion=request.emotion
        )

        # Save to file
        filename = f"voice_{uuid.uuid4().hex[:8]}.mp3"
        audio_path = OUTPUT_DIR / filename
        audio_path.write_bytes(audio_bytes)

        # Estimate duration (rough: ~150 words/min at speed 1.0)
        word_count = len(request.text.split())
        duration = int((word_count / 150) * 60 / request.speed)

        return VoiceResponse(
            audio_path=str(audio_path),
            duration_estimate=duration,
            file_size=len(audio_bytes)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/voice/voices/list")
async def list_voices():
    """List available voice options from current provider"""
    ai = get_ai_service()
    voices = ai.list_voices()
    provider_info = ai.get_provider_info()
    return {
        "voices": voices,
        "provider": provider_info.get("tts", "unknown")
    }


@router.post("/voice/clone", response_model=VoiceCloneResponse)
async def clone_voice(
    audio: UploadFile = File(..., description="Audio file (MP3/WAV/M4A, 10s-5min)"),
    name: str = Form(..., description="Name for this voice profile")
):
    """Clone a voice from an audio sample

    Upload an audio file (10 seconds to 5 minutes) with clear speech
    to create a cloned voice that can be used for text-to-speech.
    """
    try:
        # Read uploaded file
        audio_bytes = await audio.read()
        filename = audio.filename or "audio.mp3"

        # Create voice profile (handles validation, upload, and cloning)
        profile = await create_voice_profile(audio_bytes, filename, name)

        return VoiceCloneResponse(
            profile_id=profile.id,
            name=profile.name,
            voice_id=profile.minimax_voice_id,
            message=f"Voice '{name}' cloned successfully. Use voice_id '{profile.minimax_voice_id}' for TTS."
        )

    except AssetValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice cloning failed: {str(e)}")


@router.get("/voice/profiles", response_model=VoiceProfileListResponse)
async def get_voice_profiles():
    """List all saved voice profiles"""
    profiles = list_voice_profiles()
    return VoiceProfileListResponse(
        profiles=[
            VoiceProfileResponse(
                id=p.id,
                name=p.name,
                voice_id=p.minimax_voice_id,
                created_at=p.created_at,
                audio_duration_estimate=p.audio_duration_estimate
            )
            for p in profiles
        ]
    )


@router.get("/voice/profiles/{profile_id}", response_model=VoiceProfileResponse)
async def get_profile(profile_id: str):
    """Get a specific voice profile"""
    profile = get_voice_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    return VoiceProfileResponse(
        id=profile.id,
        name=profile.name,
        voice_id=profile.minimax_voice_id,
        created_at=profile.created_at,
        audio_duration_estimate=profile.audio_duration_estimate
    )


@router.delete("/voice/profiles/{profile_id}")
async def delete_profile(profile_id: str):
    """Delete a voice profile"""
    deleted = delete_voice_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Voice profile not found")

    return {"message": "Voice profile deleted", "profile_id": profile_id}


@router.get("/voice/providers")
async def get_voice_providers():
    """Get current TTS provider info"""
    ai = get_ai_service()
    return {
        "current": ai.get_provider_info().get("tts"),
        "available": ai.list_available_providers().get("tts", [])
    }


# File download route MUST be last to avoid catching other routes
@router.get("/voice/download/{filename}")
async def get_voice_file(filename: str):
    """Download a generated audio file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)
