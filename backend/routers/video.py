"""Video generation endpoint"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid
import asyncio

from services.minimax import get_client
from services.assembler import download_file, OUTPUT_DIR

router = APIRouter(prefix="/api", tags=["video"])

# In-memory job storage (use Redis in production)
video_jobs: dict = {}


class VideoRequest(BaseModel):
    prompt: str
    model: str = "T2V-01"  # Hailuo model


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
    background_tasks.add_task(process_video_job, job_id, request.prompt, request.model)
    
    return VideoResponse(
        job_id=job_id,
        status="pending",
        message="Video generation started. Poll /api/status/{job_id} for updates."
    )


async def process_video_job(job_id: str, prompt: str, model: str):
    """Background task to process video generation"""
    try:
        video_jobs[job_id]["status"] = "processing"
        
        client = get_client()
        
        # Start video generation
        result = await client.generate_video(prompt, model)
        
        task_id = result.get("task_id")
        if not task_id:
            raise Exception(f"No task_id in response: {result}")
        
        # Poll for completion
        final_result = await client.wait_for_video(task_id, poll_interval=10, timeout=600)
        
        # Download the video
        video_url = final_result.get("file_url") or final_result.get("video_url")
        if video_url:
            video_path = await download_file(video_url, OUTPUT_DIR)
            video_jobs[job_id]["video_path"] = video_path
            video_jobs[job_id]["video_url"] = video_url
        
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
