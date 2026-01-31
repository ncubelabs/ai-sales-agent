"""Full pipeline endpoint - research → script → voice → video → merge"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid
import json

from services.minimax import get_client
from services.scraper import scrape_company_info
from services.assembler import merge_audio_video, download_file, OUTPUT_DIR

router = APIRouter(prefix="/api", tags=["generate"])

# Load prompts
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
RESEARCH_PROMPT = (PROMPTS_DIR / "research.txt").read_text()
SCRIPT_PROMPT = (PROMPTS_DIR / "script.txt").read_text()

# In-memory job storage
generation_jobs: dict = {}


class GenerateRequest(BaseModel):
    company_url: str
    our_product: str = "AI-powered sales automation platform"
    voice_id: str = "female-shaonv"
    voice_emotion: str = "happy"
    video_prompt: Optional[str] = None  # Custom video prompt, or auto-generate
    skip_video: bool = False  # Skip video generation (just do audio)


class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class GenerateStatusResponse(BaseModel):
    job_id: str
    status: str  # researching, scripting, generating_voice, generating_video, merging, completed, failed
    progress: int  # 0-100
    research: Optional[dict] = None
    script: Optional[str] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    final_path: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate", response_model=GenerateResponse)
async def generate_full_pipeline(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Run the full sales video generation pipeline"""
    
    job_id = uuid.uuid4().hex[:12]
    
    generation_jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "research": None,
        "script": None,
        "audio_path": None,
        "video_path": None,
        "final_path": None,
        "error": None,
        "request": request.model_dump()
    }
    
    background_tasks.add_task(run_pipeline, job_id)
    
    return GenerateResponse(
        job_id=job_id,
        status="pending",
        message="Pipeline started. Poll /api/generate/status/{job_id} for updates."
    )


async def run_pipeline(job_id: str):
    """Background task to run full pipeline"""
    job = generation_jobs[job_id]
    request = GenerateRequest(**job["request"])
    
    try:
        client = get_client()
        
        # Step 1: Research (20%)
        job["status"] = "researching"
        job["progress"] = 10
        
        scraped = await scrape_company_info(request.company_url)
        
        # Convert scraped data to text format
        scraped_text = f"""
Company: {scraped.company_name or scraped.domain}
Title: {scraped.title or ""}
Description: {scraped.meta_description or ""}
About: {scraped.about_text or ""}
Services: {', '.join(scraped.services)}
Contact: {scraped.contact_info}
"""
        
        prompt = RESEARCH_PROMPT.format(
            url=request.company_url,
            content=scraped_text
        )
        
        research_text = await client.generate_text(prompt)
        
        # Parse research JSON
        clean_text = research_text.strip()
        if clean_text.startswith("```"):
            clean_text = clean_text.split("```")[1]
            if clean_text.startswith("json"):
                clean_text = clean_text[4:]
        research = json.loads(clean_text.strip())
        
        job["research"] = research
        job["progress"] = 25
        
        # Step 2: Script (40%)
        job["status"] = "scripting"
        
        script_prompt = SCRIPT_PROMPT.format(
            research=json.dumps(research, indent=2),
            our_product=request.our_product
        )
        
        script = await client.generate_text(script_prompt, max_tokens=1000)
        job["script"] = script.strip()
        job["progress"] = 40
        
        # Step 3: Voice (60%)
        job["status"] = "generating_voice"
        
        audio_bytes = await client.generate_speech(
            text=job["script"],
            voice_id=request.voice_id,
            emotion=request.voice_emotion
        )
        
        audio_filename = f"audio_{job_id}.mp3"
        audio_path = OUTPUT_DIR / audio_filename
        audio_path.write_bytes(audio_bytes)
        job["audio_path"] = str(audio_path)
        job["progress"] = 60
        
        if request.skip_video:
            # Just return audio
            job["final_path"] = str(audio_path)
            job["status"] = "completed"
            job["progress"] = 100
            return
        
        # Step 4: Video (80%)
        job["status"] = "generating_video"
        
        # Generate video prompt if not provided
        video_prompt = request.video_prompt
        if not video_prompt:
            company_name = research.get("company_name", "a company")
            video_prompt = f"Professional business person in modern office, talking to camera, confident and friendly, corporate setting, high quality, 4K"
        
        # Start video generation
        video_result = await client.generate_video(video_prompt)
        task_id = video_result.get("task_id")
        
        if task_id:
            # Wait for video
            final_video = await client.wait_for_video(task_id, poll_interval=10, timeout=600)
            video_url = final_video.get("file_url") or final_video.get("video_url")
            
            if video_url:
                video_path = await download_file(video_url, OUTPUT_DIR)
                job["video_path"] = video_path
        
        job["progress"] = 85
        
        # Step 5: Merge (100%)
        if job.get("video_path"):
            job["status"] = "merging"
            
            final_filename = f"final_{job_id}.mp4"
            final_path = await merge_audio_video(
                job["audio_path"],
                job["video_path"],
                final_filename
            )
            job["final_path"] = final_path
        else:
            # No video, just use audio
            job["final_path"] = job["audio_path"]
        
        job["status"] = "completed"
        job["progress"] = 100
        
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)


@router.get("/generate/status/{job_id}", response_model=GenerateStatusResponse)
async def get_generate_status(job_id: str):
    """Check status of a full generation job"""
    
    if job_id not in generation_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = generation_jobs[job_id]
    
    return GenerateStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        research=job.get("research"),
        script=job.get("script"),
        audio_path=job.get("audio_path"),
        video_path=job.get("video_path"),
        final_path=job.get("final_path"),
        error=job.get("error")
    )
