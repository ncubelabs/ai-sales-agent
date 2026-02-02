"""Full pipeline endpoint - research → script → voice → video → merge"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid

from services.ai_service import get_ai_service
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
        ai = get_ai_service()

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

        research = await ai.generate_research(
            research_prompt=RESEARCH_PROMPT,
            scraped_data=scraped_text,
            company_url=request.company_url,
            company_name=scraped.company_name or scraped.domain,
        )

        job["research"] = research
        job["progress"] = 25

        # Step 2: Script (40%)
        job["status"] = "scripting"

        clean_script = await ai.generate_script(
            script_prompt=SCRIPT_PROMPT,
            research=research,
            sender_name=request.our_product,
        )

        job["script"] = clean_script
        job["progress"] = 40

        # Step 3: Voice (60%)
        job["status"] = "generating_voice"

        audio_bytes = await ai.generate_speech(
            text=clean_script,
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
            video_prompt = (
                "Professional business person in modern office, talking to camera, "
                "confident and friendly, corporate setting, high quality, 4K"
            )

        # Generate video
        video_result = await ai.generate_video(video_prompt)

        if video_result.video_bytes:
            video_filename = f"video_{job_id}.mp4"
            video_path = OUTPUT_DIR / video_filename
            video_path.write_bytes(video_result.video_bytes)
            job["video_path"] = str(video_path)
        elif video_result.video_path:
            job["video_path"] = video_result.video_path

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
