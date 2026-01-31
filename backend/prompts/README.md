# AI Sales Agent - Prompts & Research Module

## Pipeline Flow

```
URL Input → scraper.py → research.txt → script.txt → video_prompt.txt
                ↓              ↓             ↓              ↓
         Scraped Data    Research JSON   30sec Script   Video Prompt
```

## Files

| File | Purpose | Input | Output |
|------|---------|-------|--------|
| `scraper.py` | Web scraping | URL | Structured company data |
| `research.txt` | Company research | Scraped data + URL | JSON research profile |
| `script.txt` | Script generation | Research profile | 75-word video script |
| `video_prompt.txt` | Video generation | Script + industry | Hailuo video prompt |

## Usage Example

### 1. Scrape Company Info
```python
from services.scraper import scrape_company_info

scraped = await scrape_company_info("https://acmeclinic.com")
prompt_context = scraped.to_prompt_context()
```

### 2. Run Research Prompt
```python
research_prompt = open("prompts/research.txt").read()
filled_prompt = research_prompt.format(
    company_url="https://acmeclinic.com",
    company_name="Acme Medical Clinic",
    additional_context="",
    scraped_data=prompt_context
)
# Send to LLM → Get research JSON
```

### 3. Generate Script
```python
script_prompt = open("prompts/script.txt").read()
filled_prompt = script_prompt.format(
    research_profile=research_json,
    sender_name="Alex"
)
# Send to LLM → Get 30-sec script
```

### 4. Generate Video Prompt
```python
video_prompt = open("prompts/video_prompt.txt").read()
filled_prompt = video_prompt.format(
    script=generated_script,
    industry=research_json["industry"]["primary"],
    company_overview=research_json["company"]["overview"],
    mood="professional, innovative"
)
# Send to LLM → Get Hailuo prompt
```

## Sample Output Chain

**Input:** `https://acmeclinic.com`

**→ Research Output (summary):**
```json
{
  "company": {"name": "Acme Medical Clinic", "overview": "Regional healthcare provider..."},
  "industry": {"primary": "Healthcare - Primary Care"},
  "pain_points": {"primary": "Patient scheduling and no-show management"},
  "ai_opportunities": {"immediate": "AI-powered appointment scheduling"}
}
```

**→ Script Output:**
```
Hey Dr. Martinez—

Running three clinic locations means your front desk is probably drowning 
in phone calls. Appointment scheduling, rescheduling, no-shows... it never stops.

What if patients could book, reschedule, and get reminders through an AI 
assistant that works 24/7? We've helped practices cut no-shows by 40% 
while freeing up staff for actual patient care.

Worth a 15-minute call to see if it fits? Link's below.
```
(72 words)

**→ Video Prompt Output:**
```
MAIN PROMPT:
Smooth cinematic motion through an abstract healthcare environment. 
Soft blue and teal color palette. Floating calendar icons transform 
into flowing medical cross symbols. Gentle particle effects suggest 
digital connection...

STYLE MODIFIERS:
corporate, medical, abstract, motion graphics, clean, professional

NEGATIVE PROMPT:
human faces, specific people, text, medical gore
```

## Quality Notes

- **research.txt**: Works with minimal info (just URL). Provides confidence levels.
- **script.txt**: Enforces 75-word limit. Founder-to-founder tone, not salesy.
- **video_prompt.txt**: Abstract visuals only, no faces (avoids uncanny valley).
- **scraper.py**: Graceful error handling. Works without dependencies (degrades).

---
Created by BERNARD 🔍 for NCube Labs Hackathon
