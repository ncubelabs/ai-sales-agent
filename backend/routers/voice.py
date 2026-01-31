"""Voice/TTS endpoint"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid

from services.minimax import get_client

router = APIRouter(prefix="/api", tags=["voice"])

OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


class VoiceRequest(BaseModel):
    text: str
    voice_id: str = "female-shaonv"  # Options: female-shaonv, male-qn-qingse, etc.
    speed: float = 1.0
    emotion: str = "happy"  # Options: happy, sad, angry, fearful, disgusted, surprised, neutral


class VoiceResponse(BaseModel):
    audio_path: str
    duration_estimate: int  # seconds
    file_size: int  # bytes


@router.post("/voice", response_model=VoiceResponse)
async def generate_voice(request: VoiceRequest):
    """Generate voice audio from text using MiniMax Speech TTS"""
    
    try:
        client = get_client()
        
        # Generate audio
        audio_bytes = await client.generate_speech(
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


@router.get("/voice/{filename}")
async def get_voice_file(filename: str):
    """Download a generated audio file"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)


# Available voices for reference
AVAILABLE_VOICES = {
    "female-shaonv": "Young female, energetic",
    "female-yujie": "Mature female, professional",
    "male-qn-qingse": "Young male, fresh",
    "male-qn-jingying": "Male, business professional",
    "presenter_male": "Male presenter voice",
    "presenter_female": "Female presenter voice",
}

@router.get("/voice/voices/list")
async def list_voices():
    """List available voice options"""
    return {"voices": AVAILABLE_VOICES}
