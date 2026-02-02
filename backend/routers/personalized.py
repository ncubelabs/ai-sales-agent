"""Personalized Video Generation Pipeline

Generates hyper-personalized sales videos using:
- Person's face image (for talking head video)
- Person's voice sample (for voice cloning)
- Company research and script generation
"""
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel

from services.ai_service import get_ai_service
from services.scraper import scrape_company_info
from services.assembler import merge_audio_video, OUTPUT_DIR
from services.asset_storage import (
    save_and_upload_image,
    AssetValidationError,
)
from services.voice_profile import (
    create_voice_profile,
    get_voice_profile,
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
        ai = get_ai_service()

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

        research = await ai.generate_research(
            research_prompt=RESEARCH_PROMPT,
            scraped_data=scraped_text,
            company_url=request["company_url"],
            company_name=scraped.company_name or scraped.domain,
        )

        job["research"] = research
        job["progress"] = 20

        # Step 2: Generate script (35%)
        job["status"] = "scripting"

        clean_script = await ai.generate_script(
            script_prompt=SCRIPT_PROMPT,
            research=research,
            sender_name=request["our_product"],
        )

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

        audio_bytes = await ai.generate_speech(
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

        # Step 5: Save image and prepare for video (60%)
        job["status"] = "uploading_image"

        # Save image locally for SadTalker, or upload for MiniMax
        image_filename = f"face_{job_id}.jpg"
        image_path = OUTPUT_DIR / image_filename
        image_path.write_bytes(image_data["bytes"])
        job["progress"] = 60

        # Step 6: Generate talking head video (85%)
        job["status"] = "generating_video"

        company_name = research.get("company_name", "your company")
        video_prompt = (
            f"Professional person talking to camera in modern office setting. "
            f"Natural head movements and expressions. Confident and friendly demeanor. "
            f"Speaking about business solutions for {company_name}. "
            f"High quality, well-lit, corporate environment."
        )

        # Check which video provider is being used
        provider_info = ai.get_provider_info()

        if provider_info.get("video") == "sadtalker":
            # SadTalker uses local files
            video_result = await ai.generate_talking_head(
                audio_path=str(audio_path),
                face_image_path=str(image_path),
            )
        else:
            # MiniMax S2V-01 needs a public URL
            # Upload image to get public URL
            image_url = await save_and_upload_image(
                image_data["bytes"],
                image_data["filename"]
            )
            video_result = await ai.generate_talking_head(
                audio_path=str(audio_path),
                face_image_path=str(image_path),
                image_url=image_url,
                prompt=video_prompt,
                duration=6
            )

        # Save video
        if video_result.video_bytes:
            video_filename = f"personalized_video_{job_id}.mp4"
            video_path = OUTPUT_DIR / video_filename
            video_path.write_bytes(video_result.video_bytes)
            job["video_path"] = str(video_path)
        elif video_result.video_path:
            job["video_path"] = video_result.video_path

        job["progress"] = 85

        # Step 7: Merge audio and video (100%)
        job["status"] = "merging"

        if job.get("video_path"):
            final_filename = f"personalized_final_{job_id}.mp4"
            final_path = await merge_audio_video(
                str(audio_path),
                job["video_path"],
                final_filename
            )
            job["final_path"] = final_path
        else:
            # No video generated, just use audio
            job["final_path"] = str(audio_path)

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


@router.get("/providers")
async def get_personalized_providers():
    """Get current provider configuration for personalized pipeline"""
    ai = get_ai_service()
    return {
        "providers": ai.get_provider_info(),
        "available": ai.list_available_providers(),
        "enabled": ENABLE_PERSONALIZED,
    }
