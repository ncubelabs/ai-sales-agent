"""Script generation endpoint"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json

from services.minimax import get_client

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
from pathlib import Path
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "script.txt"
SCRIPT_PROMPT = PROMPT_PATH.read_text()


@router.post("/script", response_model=ScriptResponse)
async def generate_script(request: ScriptRequest):
    """Generate a personalized sales script from research"""
    
    try:
        # Build prompt
        prompt = SCRIPT_PROMPT.format(
            research=json.dumps(request.research, indent=2),
            our_product=request.our_product
        )
        
        if request.tone:
            prompt += f"\n\nUse a {request.tone} tone."
        
        prompt += f"\n\nKeep it under {request.max_words} words."
        
        # Call MiniMax M2.1
        client = get_client()
        script = await client.generate_text(prompt, max_tokens=1000)
        
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
