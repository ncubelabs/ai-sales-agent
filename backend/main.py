"""AI Sales Agent Backend - FastAPI Application"""
import os
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from parent .env
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from routers import research, script, voice, video, generate

# Create outputs directory
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    print("🚀 AI Sales Agent Backend starting...")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    
    # Check for API key
    if not os.getenv("MINIMAX_API_KEY"):
        print("⚠️  WARNING: MINIMAX_API_KEY not set!")
    else:
        print("✅ MiniMax API key loaded")
    
    yield
    
    print("👋 Shutting down...")


app = FastAPI(
    title="AI Sales Agent API",
    description="Generate personalized AI sales videos from company research",
    version="1.0.0",
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

# Serve output files
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")


@app.get("/")
async def root():
    """Health check and API info"""
    return {
        "status": "running",
        "name": "AI Sales Agent API",
        "version": "1.0.0",
        "endpoints": {
            "research": "POST /api/research - Research a company",
            "script": "POST /api/script - Generate sales script",
            "voice": "POST /api/voice - Generate voice audio",
            "video": "POST /api/video - Generate video",
            "generate": "POST /api/generate - Full pipeline",
            "status": "GET /api/status/{job_id} - Check job status",
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
