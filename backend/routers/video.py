"""Video generation endpoint"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid

from services.ai_service import get_ai_service
from services.assembler import OUTPUT_DIR

router = APIRouter(prefix="/api", tags=["video"])

# In-memory job storage (use Redis in production)
video_jobs: dict = {}


class VideoRequest(BaseModel):
    prompt: str
    model: str = "T2V-01"  # Hailuo model (for MiniMax)
    duration: int = 6


class VideoResponse(BaseModel):
    job_id: str
    status: str
    message: str


class VideoStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    error: Optional[str] = None


@router.post("/video", response_model=VideoResponse)
async def generate_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Start video generation (async - poll /status/{job_id} for result)"""

    job_id = uuid.uuid4().hex[:12]

    # Initialize job
    video_jobs[job_id] = {
        "status": "pending",
        "prompt": request.prompt,
        "video_path": None,
        "video_url": None,
        "error": None
    }

    # Start background task
    background_tasks.add_task(
        process_video_job, job_id, request.prompt, request.model, request.duration
    )

    return VideoResponse(
        job_id=job_id,
        status="pending",
        message="Video generation started. Poll /api/status/{job_id} for updates."
    )


async def process_video_job(job_id: str, prompt: str, model: str, duration: int):
    """Background task to process video generation"""
    try:
        video_jobs[job_id]["status"] = "processing"

        ai = get_ai_service()

        # Generate video
        result = await ai.generate_video(
            prompt=prompt,
            duration=duration,
            model=model,
        )

        # Save video if bytes returned
        if result.video_bytes:
            video_filename = f"video_{job_id}.mp4"
            video_path = OUTPUT_DIR / video_filename
            video_path.write_bytes(result.video_bytes)
            video_jobs[job_id]["video_path"] = str(video_path)
        elif result.video_path:
            video_jobs[job_id]["video_path"] = result.video_path

        video_jobs[job_id]["status"] = "completed"

    except Exception as e:
        video_jobs[job_id]["status"] = "failed"
        video_jobs[job_id]["error"] = str(e)


@router.get("/status/{job_id}", response_model=VideoStatusResponse)
async def get_job_status(job_id: str):
    """Check status of a video generation job"""

    if job_id not in video_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = video_jobs[job_id]

    return VideoStatusResponse(
        job_id=job_id,
        status=job["status"],
        video_path=job.get("video_path"),
        video_url=job.get("video_url"),
        error=job.get("error")
    )


@router.get("/video/providers")
async def get_video_providers():
    """Get current video provider info"""
    ai = get_ai_service()
    return {
        "current": ai.get_provider_info().get("video"),
        "available": ai.list_available_providers().get("video", [])
    }
