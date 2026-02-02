"""Research endpoint - scrape and analyze company"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

from services.ai_service import get_ai_service
from services.scraper import scrape_company_info

router = APIRouter(prefix="/api", tags=["research"])


class ResearchRequest(BaseModel):
    url: str
    deep_scrape: bool = False


class ResearchResponse(BaseModel):
    """Flexible response model that accepts AI output"""
    company: Optional[dict] = None
    company_name: Optional[str] = None
    industry: Optional[dict | str] = None
    products_services: Optional[list[str]] = None
    value_proposition: Optional[str] = None
    target_audience: Optional[str] = None
    pain_points: Optional[dict | list[str]] = None
    recent_news: Optional[list[str]] = None
    company_size: Optional[dict | str] = None
    tone: Optional[str] = None
    key_decision_makers: Optional[list[str]] = None
    personalization_hooks: Optional[dict | list[str]] = None
    ai_opportunities: Optional[dict] = None
    outreach_strategy: Optional[dict] = None
    raw_content: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields from AI


# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "research.txt"
RESEARCH_PROMPT = PROMPT_PATH.read_text()


@router.post("/research", response_model=ResearchResponse)
async def research_company(request: ResearchRequest):
    """Research a company from their website URL"""

    try:
        # Scrape the website
        scraped = await scrape_company_info(request.url)

        if not scraped.company_name and not scraped.title:
            raise HTTPException(
                status_code=400,
                detail="Could not scrape any useful content from URL"
            )

        # Convert scraped data to text format for prompt
        scraped_text = f"""
Company: {scraped.company_name or scraped.domain}
Title: {scraped.title or ""}
Description: {scraped.meta_description or ""}
About: {scraped.about_text or ""}
Services: {', '.join(scraped.services)}
Contact: {scraped.contact_info}
"""

        # Use AIService for text generation
        ai = get_ai_service()

        research_data = await ai.generate_research(
            research_prompt=RESEARCH_PROMPT,
            scraped_data=scraped_text,
            company_url=request.url,
            company_name=scraped.company_name or scraped.domain or "Unknown",
        )

        # Add raw content if requested
        if request.deep_scrape:
            research_data["raw_content"] = scraped.combined_content

        return ResearchResponse(**research_data)

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
