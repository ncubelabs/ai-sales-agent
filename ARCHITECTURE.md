# AI Sales Agent — Architecture

## Overview
Personalized video sales outreach at scale using MiniMax multimodal APIs.

**Input:** Prospect company URL/info
**Output:** Personalized video pitch ready to send

---

## Flow

```
[Prospect URL/Info]
        ↓
[1. RESEARCH] ← MiniMax M2.2
    - Scrape company info
    - Identify pain points
    - Find AI opportunities
        ↓
[2. SCRIPT] ← MiniMax M2.2
    - Generate personalized script
    - Tailor to prospect's industry
    - Include specific value props
        ↓
[3. VOICE] ← MiniMax Speech
    - Convert script to voiceover
    - Professional tone
    - Optional: voice clone
        ↓
[4. VIDEO] ← MiniMax Hailuo
    - Generate video visuals
    - Match script timing
    - Professional quality
        ↓
[5. ASSEMBLE]
    - Combine audio + video
    - Add branding
    - Export final video
        ↓
[Personalized Video Pitch]
```

---

## Tech Stack

### Backend
- **Python/Node.js** — API orchestration
- **FastAPI/Express** — REST API
- **MiniMax APIs:**
  - M2.2 for text generation
  - Speech for TTS
  - Hailuo for video

### Frontend
- **React/Next.js** — Web UI
- **Simple form** — Input prospect info
- **Preview + Download** — Final video

### Infrastructure
- Local dev for hackathon
- Future: Deploy on Vercel/Railway

---

## API Integration

### MiniMax M2.2 (Text)
```python
# Research + Script Generation
response = minimax.chat.completions.create(
    model="abab6.5s-chat",
    messages=[
        {"role": "system", "content": "You are a sales research expert..."},
        {"role": "user", "content": f"Research {company} and write a pitch..."}
    ]
)
```

### MiniMax Speech (TTS)
```python
# Voice Generation
audio = minimax.speech.create(
    model="speech-01",
    text=script,
    voice="professional-male-1"
)
```

### MiniMax Hailuo (Video)
```python
# Video Generation
video = minimax.video.create(
    model="hailuo-01",
    prompt=f"Professional business presentation about {topic}",
    duration=30
)
```

---

## MVP Scope (Hackathon)

### Must Have
- [ ] Company URL input
- [ ] Research generation (M2.2)
- [ ] Script generation (M2.2)
- [ ] Voiceover (Speech)
- [ ] Basic video (Hailuo)
- [ ] Download final video

### Nice to Have
- [ ] Voice clone option
- [ ] Multiple video styles
- [ ] CRM integration
- [ ] Email sending built-in

### Future (Post-hackathon)
- Bulk processing
- Analytics/tracking
- A/B testing scripts
- Integration with Salesforce/HubSpot

---

## Demo Script (2 min)

1. **Problem** (20s)
   "Cold outreach is broken. Generic emails get ignored."

2. **Solution** (20s)
   "AI Sales Agent creates personalized video pitches in seconds."

3. **Demo** (60s)
   - Input prospect URL
   - Show research output
   - Play generated video

4. **Impact** (20s)
   "Built in a day. Imagine what we do for clients. ncubelabs.ai"

---

## Winning Criteria

✅ Uses multiple MiniMax APIs (M2.2 + Speech + Video)
✅ Clear business value
✅ Working demo
✅ Creative application
✅ Polish and presentation

---

*Let's win this.* 🥇⚔️
