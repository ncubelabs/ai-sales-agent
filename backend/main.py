"""AI Sales Agent Backend - FastAPI Application"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from local .env first, then parent
load_dotenv(Path(__file__).parent / ".env")
load_dotenv(Path(__file__).parent.parent / ".env")

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from routers import research, script, voice, video, generate, personalized
from services.ai_service import get_ai_service, close_ai_service
from providers import get_registry

# Create required directories
OUTPUT_DIR = Path(__file__).parent / "outputs"
UPLOAD_DIR = Path(__file__).parent / "uploads"
DATA_DIR = Path(__file__).parent / "data"
VOICES_DIR = Path(__file__).parent / "voices"
MODELS_DIR = Path(__file__).parent / "models"

OUTPUT_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
VOICES_DIR.mkdir(exist_ok=True)
MODELS_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    print("AI Sales Agent Backend starting...")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Upload directory: {UPLOAD_DIR}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Voices directory: {VOICES_DIR}")

    # Provider configuration
    print("\n=== Provider Configuration ===")

    # Get configured providers
    text_provider = os.getenv("PROVIDER_TEXT", "minimax")
    tts_provider = os.getenv("PROVIDER_TTS", "minimax")
    video_provider = os.getenv("PROVIDER_VIDEO", "minimax")

    print(f"Text provider: {text_provider}")
    print(f"TTS provider: {tts_provider}")
    print(f"Video provider: {video_provider}")

    # Check provider-specific requirements
    if text_provider == "minimax" or tts_provider == "minimax" or video_provider == "minimax":
        if not os.getenv("MINIMAX_API_KEY"):
            print("WARNING: MINIMAX_API_KEY not set!")
        else:
            print("MiniMax API key: loaded")

        if not os.getenv("MINIMAX_GROUP_ID"):
            print("WARNING: MINIMAX_GROUP_ID not set - MiniMax TTS will not work!")
        else:
            print("MiniMax Group ID: loaded")

    if text_provider == "vllm":
        vllm_url = os.getenv("PROVIDER_VLLM_BASE_URL", "http://localhost:8000")
        vllm_model = os.getenv("PROVIDER_VLLM_MODEL", "meta-llama/Llama-3.1-70B-Instruct")
        print(f"vLLM URL: {vllm_url}")
        print(f"vLLM Model: {vllm_model}")

    if tts_provider == "coqui":
        coqui_device = os.getenv("PROVIDER_COQUI_DEVICE", "cuda")
        print(f"Coqui device: {coqui_device}")

    if video_provider == "sadtalker":
        sadtalker_path = os.getenv("PROVIDER_SADTALKER_CHECKPOINT", "./models/sadtalker")
        print(f"SadTalker checkpoint: {sadtalker_path}")

    # List available providers
    try:
        registry = get_registry()
        available = registry.list_available_providers()
        print(f"\nAvailable providers:")
        print(f"  Text: {', '.join(available['text'])}")
        print(f"  TTS: {', '.join(available['tts'])}")
        print(f"  Video: {', '.join(available['video'])}")
    except Exception as e:
        print(f"Warning: Could not initialize provider registry: {e}")

    # Check personalized pipeline status
    if os.getenv("ENABLE_PERSONALIZED_PIPELINE", "true").lower() == "true":
        print("\nPersonalized video pipeline: ENABLED")
    else:
        print("\nPersonalized video pipeline: DISABLED")

    print("\n" + "=" * 40)

    yield

    # Cleanup
    print("Shutting down...")
    await close_ai_service()


app = FastAPI(
    title="AI Sales Agent API",
    description="Generate personalized AI sales videos from company research",
    version="2.0.0",  # Updated for OSS provider support
    lifespan=lifespan
)

# CORS - allow all origins for hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(research.router)
app.include_router(script.router)
app.include_router(voice.router)
app.include_router(video.router)
app.include_router(generate.router)
app.include_router(personalized.router)

# Serve output files
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


@app.get("/")
async def root():
    """Health check and API info"""
    ai = get_ai_service()
    provider_info = ai.get_provider_info()

    return {
        "status": "running",
        "name": "AI Sales Agent API",
        "version": "2.0.0",
        "providers": provider_info,
        "endpoints": {
            "research": "POST /api/research - Research a company",
            "script": "POST /api/script - Generate sales script",
            "voice": "POST /api/voice - Generate voice audio",
            "voice_clone": "POST /api/voice/clone - Clone a voice from audio sample",
            "voice_profiles": "GET /api/voice/profiles - List saved voice profiles",
            "voice_providers": "GET /api/voice/providers - List TTS providers",
            "video": "POST /api/video - Generate video",
            "video_providers": "GET /api/video/providers - List video providers",
            "generate": "POST /api/generate - Full pipeline",
            "personalized": "POST /api/personalized/generate - Personalized video with face + voice",
            "personalized_status": "GET /api/personalized/status/{job_id} - Check personalized job status",
            "personalized_providers": "GET /api/personalized/providers - Provider configuration",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/providers")
async def get_providers():
    """Get all provider information"""
    ai = get_ai_service()
    return {
        "current": ai.get_provider_info(),
        "available": ai.list_available_providers(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
