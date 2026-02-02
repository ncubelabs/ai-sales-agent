"""Script generation endpoint"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

from services.ai_service import get_ai_service

router = APIRouter(prefix="/api", tags=["script"])


class ScriptRequest(BaseModel):
    research: dict  # Research data from /api/research
    our_product: str = "AI-powered sales automation platform that helps B2B companies create personalized video outreach at scale"
    tone: Optional[str] = None  # Override tone from research
    max_words: int = 150


class ScriptResponse(BaseModel):
    script: str
    word_count: int
    estimated_duration_seconds: int


# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "script.txt"
SCRIPT_PROMPT = PROMPT_PATH.read_text()


@router.post("/script", response_model=ScriptResponse)
async def generate_script(request: ScriptRequest):
    """Generate a personalized sales script from research"""

    try:
        ai = get_ai_service()

        # Generate script using AIService
        script = await ai.generate_script(
            script_prompt=SCRIPT_PROMPT,
            research=request.research,
            sender_name=request.our_product,
        )

        # Apply additional modifiers
        if request.tone:
            # If tone override specified, regenerate with custom prompt
            custom_prompt = SCRIPT_PROMPT
            custom_prompt = custom_prompt.replace("{research_profile}", json.dumps(request.research, indent=2))
            custom_prompt = custom_prompt.replace("{sender_name}", request.our_product)
            custom_prompt += f"\n\nUse a {request.tone} tone."
            custom_prompt += f"\n\nKeep it under {request.max_words} words."

            script = await ai.generate_text(custom_prompt, max_tokens=1000)
            script = ai._clean_script(script)

        # Clean up script
        script = script.strip()

        # Count words (rough estimate)
        word_count = len(script.split())

        # Estimate duration (average speaking rate: 150 words/min)
        duration = int((word_count / 150) * 60)

        return ScriptResponse(
            script=script,
            word_count=word_count,
            estimated_duration_seconds=duration
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
