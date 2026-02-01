"""Personalized Video Generation Pipeline

Generates hyper-personalized sales videos using:
- Person's face image (for S2V-01 subject reference)
- Person's voice sample (for voice cloning)
- Company research and script generation
"""
import os
import json
import re
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel

from services.minimax import get_client
from services.scraper import scrape_company_info
from services.assembler import merge_audio_video, OUTPUT_DIR
from services.asset_storage import (
    save_and_upload_image,
    save_and_upload_audio,
    AssetValidationError,
)
from services.voice_profile import (
    create_voice_profile,
    get_voice_profile,
    VoiceProfile,
)

router = APIRouter(prefix="/api/personalized", tags=["personalized"])

# Load prompts
PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
RESEARCH_PROMPT = (PROMPTS_DIR / "research.txt").read_text()
SCRIPT_PROMPT = (PROMPTS_DIR / "script.txt").read_text()

# In-memory job storage
personalized_jobs: dict = {}

# Check if personalized pipeline is enabled
ENABLE_PERSONALIZED = os.getenv("ENABLE_PERSONALIZED_PIPELINE", "true").lower() == "true"


class PersonalizedGenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str


class PersonalizedStatusResponse(BaseModel):
    job_id: str
    status: str  # pending, researching, scripting, cloning_voice, generating_voice, uploading_image, generating_video, merging, completed, failed
    progress: int  # 0-100
    research: Optional[dict] = None
    script: Optional[str] = None
    voice_profile_id: Optional[str] = None
    audio_path: Optional[str] = None
    video_path: Optional[str] = None
    final_path: Optional[str] = None
    error: Optional[str] = None


@router.post("/generate", response_model=PersonalizedGenerateResponse)
async def generate_personalized_video(
    background_tasks: BackgroundTasks,
    company_url: str = Form(..., description="Target company URL to research"),
    person_image: UploadFile = File(..., description="Face photo (JPEG/PNG, min 512x512)"),
    voice_sample: Optional[UploadFile] = File(None, description="Voice sample (MP3/WAV/M4A, 10s-5min)"),
    voice_profile_id: Optional[str] = Form(None, description="Existing voice profile ID (alternative to voice_sample)"),
    our_product: str = Form("AI-powered sales automation platform", description="Your product description"),
):
    """Generate a personalized sales video

    Requires either voice_sample (to create new clone) or voice_profile_id (to use existing).
    The person_image will be used for the talking head video.
    """
    if not ENABLE_PERSONALIZED:
        raise HTTPException(
            status_code=503,
            detail="Personalized pipeline is disabled. Set ENABLE_PERSONALIZED_PIPELINE=true"
        )

    # Validate we have either voice sample or profile ID
    if not voice_sample and not voice_profile_id:
        raise HTTPException(
            status_code=400,
            detail="Either voice_sample or voice_profile_id is required"
        )

    # Read image file
    try:
        image_bytes = await person_image.read()
        image_filename = person_image.filename or "image.jpg"
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read image: {str(e)}")

    # Read voice sample if provided
    voice_bytes = None
    voice_filename = None
    if voice_sample:
        try:
            voice_bytes = await voice_sample.read()
            voice_filename = voice_sample.filename or "voice.mp3"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read voice sample: {str(e)}")

    # Create job
    job_id = uuid.uuid4().hex[:12]

    personalized_jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "research": None,
        "script": None,
        "voice_profile_id": voice_profile_id,
        "audio_path": None,
        "video_path": None,
        "final_path": None,
        "error": None,
        # Store request data for background task
        "request": {
            "company_url": company_url,
            "our_product": our_product,
            "voice_profile_id": voice_profile_id,
        },
        "image_data": {
            "bytes": image_bytes,
            "filename": image_filename,
        },
        "voice_data": {
            "bytes": voice_bytes,
            "filename": voice_filename,
        } if voice_bytes else None,
    }

    background_tasks.add_task(run_personalized_pipeline, job_id)

    return PersonalizedGenerateResponse(
        job_id=job_id,
        status="pending",
        message="Personalized video generation started. Poll /api/personalized/status/{job_id} for updates."
    )


async def run_personalized_pipeline(job_id: str):
    """Background task to run the personalized video pipeline"""
    job = personalized_jobs[job_id]
    request = job["request"]
    image_data = job["image_data"]
    voice_data = job.get("voice_data")

    try:
        client = get_client()

        # Step 1: Research company (20%)
        job["status"] = "researching"
        job["progress"] = 5

        scraped = await scrape_company_info(request["company_url"])

        scraped_text = f"""
Company: {scraped.company_name or scraped.domain}
Title: {scraped.title or ""}
Description: {scraped.meta_description or ""}
About: {scraped.about_text or ""}
Services: {', '.join(scraped.services)}
Contact: {scraped.contact_info}
"""

        prompt = RESEARCH_PROMPT
        prompt = prompt.replace("{company_url}", request["company_url"])
        prompt = prompt.replace("{company_name}", scraped.company_name or scraped.domain)
        prompt = prompt.replace("{additional_context}", "")
        prompt = prompt.replace("{scraped_data}", scraped_text)

        research_text = await client.generate_text(prompt)

        # Parse research JSON
        clean_text = research_text.strip()
        clean_text = re.sub(r'<think>.*?</think>', '', clean_text, flags=re.DOTALL).strip()

        if clean_text.startswith("```"):
            parts = clean_text.split("```")
            if len(parts) >= 2:
                clean_text = parts[1]
                if clean_text.startswith("json"):
                    clean_text = clean_text[4:]

        clean_text = clean_text.strip()
        json_start = clean_text.find("{")
        json_end = clean_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            clean_text = clean_text[json_start:json_end]

        research = json.loads(clean_text)
        job["research"] = research
        job["progress"] = 20

        # Step 2: Generate script (35%)
        job["status"] = "scripting"

        script_prompt = SCRIPT_PROMPT
        script_prompt = script_prompt.replace("{research_profile}", json.dumps(research, indent=2))
        script_prompt = script_prompt.replace("{sender_name}", request["our_product"])

        script = await client.generate_text(script_prompt, max_tokens=1000)

        clean_script = re.sub(r'<think>.*?</think>', '', script, flags=re.DOTALL).strip()

        if clean_script.startswith("```"):
            parts = clean_script.split("```")
            if len(parts) >= 2:
                clean_script = parts[1].strip()

        if "SCRIPT:" in clean_script:
            script_start = clean_script.find("SCRIPT:") + 7
            script_end = clean_script.find("WORD_COUNT:") if "WORD_COUNT:" in clean_script else len(clean_script)
            clean_script = clean_script[script_start:script_end].strip()

        job["script"] = clean_script
        job["progress"] = 35

        # Step 3: Handle voice (clone or use existing) (45%)
        voice_id = None

        if voice_data:
            # Clone new voice
            job["status"] = "cloning_voice"
            job["progress"] = 38

            profile_name = f"personalized_{job_id}"
            profile = await create_voice_profile(
                voice_data["bytes"],
                voice_data["filename"],
                profile_name
            )
            voice_id = profile.minimax_voice_id
            job["voice_profile_id"] = profile.id
        else:
            # Use existing profile
            profile = get_voice_profile(request["voice_profile_id"])
            if not profile:
                raise Exception(f"Voice profile not found: {request['voice_profile_id']}")
            voice_id = profile.minimax_voice_id
            job["voice_profile_id"] = profile.id

        job["progress"] = 45

        # Step 4: Generate audio with cloned voice (55%)
        job["status"] = "generating_voice"

        audio_bytes = await client.generate_speech(
            text=clean_script,
            voice_id=voice_id,
            speed=1.0,
            emotion="happy"
        )

        audio_filename = f"personalized_audio_{job_id}.mp3"
        audio_path = OUTPUT_DIR / audio_filename
        audio_path.write_bytes(audio_bytes)
        job["audio_path"] = str(audio_path)
        job["progress"] = 55

        # Step 5: Upload image to get public URL (60%)
        job["status"] = "uploading_image"

        image_url = await save_and_upload_image(
            image_data["bytes"],
            image_data["filename"]
        )
        job["progress"] = 60

        # Step 6: Generate S2V-01 video with subject reference (85%)
        job["status"] = "generating_video"

        company_name = research.get("company_name", "your company")
        video_prompt = (
            f"Professional person talking to camera in modern office setting. "
            f"Natural head movements and expressions. Confident and friendly demeanor. "
            f"Speaking about business solutions for {company_name}. "
            f"High quality, well-lit, corporate environment."
        )

        video_result = await client.generate_subject_video(
            image_url=image_url,
            prompt=video_prompt,
            duration=6
        )

        task_id = video_result.get("task_id")
        if not task_id:
            raise Exception("No task_id returned from video generation")

        # Wait for video completion
        final_video = await client.wait_for_video(task_id, poll_interval=10, timeout=600)

        # Download video
        file_id = final_video.get("file_id")
        if not file_id:
            raise Exception("No file_id in completed video response")

        video_bytes = await client.download_video(file_id)
        video_filename = f"personalized_video_{job_id}.mp4"
        video_path = OUTPUT_DIR / video_filename
        video_path.write_bytes(video_bytes)
        job["video_path"] = str(video_path)
        job["progress"] = 85

        # Step 7: Merge audio and video (100%)
        job["status"] = "merging"

        final_filename = f"personalized_final_{job_id}.mp4"
        final_path = await merge_audio_video(
            str(audio_path),
            str(video_path),
            final_filename
        )
        job["final_path"] = final_path
        job["status"] = "completed"
        job["progress"] = 100

        # Clean up stored bytes from memory
        del job["image_data"]
        if "voice_data" in job:
            del job["voice_data"]

    except AssetValidationError as e:
        job["status"] = "failed"
        job["error"] = f"Validation error: {str(e)}"
    except Exception as e:
        job["status"] = "failed"
        job["error"] = str(e)


@router.get("/status/{job_id}", response_model=PersonalizedStatusResponse)
async def get_personalized_status(job_id: str):
    """Check status of a personalized video generation job"""

    if job_id not in personalized_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = personalized_jobs[job_id]

    return PersonalizedStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        research=job.get("research"),
        script=job.get("script"),
        voice_profile_id=job.get("voice_profile_id"),
        audio_path=job.get("audio_path"),
        video_path=job.get("video_path"),
        final_path=job.get("final_path"),
        error=job.get("error")
    )
