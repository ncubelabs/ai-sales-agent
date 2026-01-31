"""Full pipeline endpoint - research → script → voice → video → merge"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import uuid
import json
import re

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
        
        # Use replace instead of format to avoid issues with JSON braces in prompt
        prompt = RESEARCH_PROMPT
        prompt = prompt.replace("{company_url}", request.company_url)
        prompt = prompt.replace("{company_name}", scraped.company_name or scraped.domain)
        prompt = prompt.replace("{additional_context}", "")
        prompt = prompt.replace("{scraped_data}", scraped_text)
        
        research_text = await client.generate_text(prompt)

        # Parse research JSON - handle MiniMax's <think> blocks and markdown
        clean_text = research_text.strip()

        # Remove <think>...</think> blocks (MiniMax includes reasoning)
        clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL).strip()

        # Remove markdown code blocks
        if clean_text.startswith("```"):
            parts = clean_text.split("```")
            if len(parts) >= 2:
                clean_text = parts[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]

        clean_text = clean_text.strip()

        # Find JSON object in response
        json_start = clean_text.find("{")
        json_end = clean_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            clean_text = clean_text[json_start:json_end]

        research = json.loads(clean_text)
        
        job["research"] = research
        job["progress"] = 25
        
        # Step 2: Script (40%)
        job["status"] = "scripting"
        
        # Use replace instead of format to avoid issues with JSON braces in prompt
        script_prompt = SCRIPT_PROMPT
        script_prompt = script_prompt.replace("{research_profile}", json.dumps(research, indent=2))
        script_prompt = script_prompt.replace("{sender_name}", request.our_product)
        
        script = await client.generate_text(script_prompt, max_tokens=1000)

        # Clean script - remove <think> blocks from MiniMax response
        clean_script = re.sub(r'<think>.*?</think>', '', script, flags=re.DOTALL).strip()

        # Remove markdown formatting if present
        if clean_script.startswith("```"):
            parts = clean_script.split("```")
            if len(parts) >= 2:
                clean_script = parts[1].strip()

        # Extract just the script text (look for SCRIPT: marker)
        if "SCRIPT:" in clean_script:
            script_start = clean_script.find("SCRIPT:") + 7
            script_end = clean_script.find("WORD_COUNT:") if "WORD_COUNT:" in clean_script else len(clean_script)
            clean_script = clean_script[script_start:script_end].strip()

        job["script"] = clean_script
        job["progress"] = 40

        # Step 3: Voice (60%)
        job["status"] = "generating_voice"

        audio_bytes = await client.generate_speech(
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
            company_name = research.get("company_name", "a company")
            video_prompt = f"Professional business person in modern office, talking to camera, confident and friendly, corporate setting, high quality, 4K"
        
        # Start video generation
        video_result = await client.generate_video(video_prompt)
        task_id = video_result.get("task_id")

        if task_id:
            # Wait for video to complete
            final_video = await client.wait_for_video(task_id, poll_interval=10, timeout=600)

            # Download video file
            file_id = final_video.get("file_id")
            if file_id:
                video_bytes = await client.download_video(file_id)
                video_filename = f"video_{job_id}.mp4"
                video_path = OUTPUT_DIR / video_filename
                video_path.write_bytes(video_bytes)
                job["video_path"] = str(video_path)
            elif final_video.get("video_url"):
                # Fallback to URL download if available
                video_path = await download_file(final_video["video_url"], OUTPUT_DIR)
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
