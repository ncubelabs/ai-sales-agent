# AI Sales Agent

Generate personalized AI-powered video sales pitches in seconds. Upload your photo and voice sample, enter a company URL, and get a custom talking-head video with your face, your cloned voice, and a personalized script.

![AI Sales Agent](https://img.shields.io/badge/AI-Sales%20Agent-6366f1?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square)
![MiniMax](https://img.shields.io/badge/MiniMax-API-ff6b6b?style=flat-square)

## Features

- **Personalized Videos** - Your face + your cloned voice in every video
- **Voice Cloning** - Clone any voice from a 10-20 second sample
- **Company Research** - AI analyzes target company websites
- **Custom Scripts** - AI generates personalized 30-second sales pitches
- **Talking Head Videos** - S2V-01 subject-reference video generation
- **Voice Profiles** - Save and reuse cloned voices

## Demo

```
User Input: Photo + 20s Voice + https://stripe.com
     ↓
[Research] → Company analysis, pain points, opportunities
     ↓
[Script] → "Hey, saw Stripe's expanding into banking services..."
     ↓
[Voice Clone] → Clone user's voice
     ↓
[TTS] → Generate speech with cloned voice
     ↓
[S2V-01] → Talking head video with user's face
     ↓
[Output] → Personalized sales video
```

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.12+
- FFmpeg
- MiniMax API credentials ([Get API Key](https://www.minimax.io/platform))

### 1. Clone the repository

```bash
git clone https://github.com/ncubelabs/ai-sales-agent.git
cd ai-sales-agent
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
MINIMAX_API_KEY=your-api-key-here
MINIMAX_GROUP_ID=your-group-id-here
MINIMAX_BASE_URL=https://api.minimax.io/v1
ENABLE_PERSONALIZED_PIPELINE=true
EOF

# Start server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 4. Open the App

Navigate to http://localhost:3000

## Usage

### Web Interface

**Standard Mode:**
1. Enter a company URL
2. Enter your name
3. Select a preset voice
4. Click "Generate Video"

**Personalized Mode:**
1. Switch to "Personalized" tab
2. Upload your photo (JPEG/PNG, min 512x512)
3. Upload voice sample (MP3/WAV/M4A, 10s-5min)
4. Enter target company URL
5. Click "Generate Personalized Video"

### API

```bash
# Personalized video generation
curl -X POST http://localhost:8000/api/personalized/generate \
  -F "company_url=https://stripe.com" \
  -F "person_image=@photo.jpg" \
  -F "voice_sample=@voice.mp3" \
  -F "our_product=AI consulting services"

# Check job status
curl http://localhost:8000/api/personalized/status/{job_id}

# Clone a voice (save for later use)
curl -X POST http://localhost:8000/api/voice/clone \
  -F "audio=@voice.mp3" \
  -F "name=MyVoice"

# List saved voice profiles
curl http://localhost:8000/api/voice/profiles

# Standard generation (preset voices)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://stripe.com",
    "our_product": "AI consulting services",
    "voice_id": "male-qn-qingse"
  }'
```

### API Documentation

Interactive docs available at http://localhost:8000/docs

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Frontend     │  HTTP   │     Backend     │  HTTPS  │   MiniMax APIs  │
│   Next.js 16    │◄───────►│    FastAPI      │◄───────►│  M2/TTS/Video   │
│   Port: 3000    │         │   Port: 8000    │         │  Voice Clone    │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### Personalized Pipeline Flow

| Step | Duration | Description |
|------|----------|-------------|
| Research | 5-10s | Scrape URL + AI company analysis |
| Script | 5-8s | Generate personalized pitch |
| Voice Clone | 2-3s | Clone voice from sample |
| TTS | 5-10s | Generate speech with cloned voice |
| Video | 3-4min | S2V-01 talking head generation |
| Merge | 2-5s | FFmpeg audio+video combine |

## Tech Stack

### Frontend
- Next.js 16.1.6 (Turbopack)
- React 18
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Python 3.12
- httpx (async HTTP)
- BeautifulSoup4 (web scraping)
- Pydantic (validation)

### MiniMax APIs
| API | Model | Purpose |
|-----|-------|---------|
| Text Generation | `MiniMax-M2` | Company research & script writing |
| Voice Cloning | `/v1/voice_clone` | Clone voice from audio sample |
| Text-to-Speech | `speech-02-hd` | Generate speech with cloned voice |
| Video Generation | `S2V-01` (Hailuo) | Subject-reference talking head videos |
| File Upload | `/v1/files/upload` | Upload audio for voice cloning |

### Infrastructure
- FFmpeg - Audio/video processing
- uguu.se - Temporary image hosting (for S2V-01)

## Project Structure

```
ai-sales-agent/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── routers/
│   │   ├── generate.py            # Standard pipeline endpoint
│   │   ├── personalized.py        # Personalized video pipeline
│   │   ├── voice.py               # Voice clone & TTS endpoints
│   │   ├── research.py            # Company research
│   │   ├── script.py              # Script generation
│   │   └── video.py               # Video endpoint
│   ├── services/
│   │   ├── minimax.py             # MiniMax API client
│   │   ├── voice_profile.py       # Voice profile management
│   │   ├── asset_storage.py       # File upload handling
│   │   ├── scraper.py             # Web scraper
│   │   └── assembler.py           # FFmpeg wrapper
│   ├── prompts/                   # LLM prompt templates
│   ├── data/                      # Voice profiles storage
│   ├── uploads/                   # Uploaded files
│   ├── outputs/                   # Generated files
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Main page
│   │   ├── layout.tsx             # Root layout
│   │   └── globals.css            # Styles
│   ├── components/
│   │   └── PersonalizedForm.tsx   # Personalized mode form
│   ├── lib/
│   │   └── api.ts                 # API client
│   └── package.json
├── pitch-deck.html                # Hackathon presentation
└── docs/
    └── SYSTEM_ARCHITECTURE.md
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MINIMAX_API_KEY` | Yes | MiniMax API key |
| `MINIMAX_GROUP_ID` | Yes | MiniMax Group ID (for TTS & voice clone) |
| `MINIMAX_BASE_URL` | No | API base URL (default: https://api.minimax.io/v1) |
| `ENABLE_PERSONALIZED_PIPELINE` | No | Enable personalized mode (default: true) |

### Preset Voice Options

| ID | Name | Description |
|----|------|-------------|
| `male-qn-qingse` | James | Professional & confident |
| `male-qn-jingying` | Marcus | Warm & friendly |
| `female-shaonv` | Sarah | Energetic & dynamic |
| `female-yujie` | Emma | Calm & trustworthy |

## Output Files

Generated files are stored in `backend/outputs/`:

```
outputs/
├── personalized_audio_{job_id}.mp3   # Cloned voice narration
├── personalized_video_{job_id}.mp4   # S2V-01 video
├── personalized_final_{job_id}.mp4   # Merged output
├── audio_{job_id}.mp3                # Standard voice
├── video_{job_id}.mp4                # Standard video
└── final_{job_id}.mp4                # Standard merged
```

## Cost Estimation

| Component | Cost per Video |
|-----------|----------------|
| Text Generation (M2) | ~$0.01 |
| Voice Cloning | ~$0.02 |
| TTS (speech-02-hd) | ~$0.02 |
| Video (S2V-01) | ~$0.40 |
| **Total** | **~$0.45** |

## Limitations

- **Development only** - No authentication, CORS allows all origins
- **In-memory storage** - Job state lost on server restart
- **Video duration** - Fixed 6-second AI videos
- **Rate limits** - Subject to MiniMax API limits
- **Image hosting** - Uses external service (uguu.se) for S2V-01

## Roadmap

- [ ] User authentication
- [ ] Persistent job storage (Redis)
- [ ] Custom video duration
- [ ] Direct image upload to MiniMax (when supported)
- [ ] Batch processing
- [ ] CRM integrations
- [ ] Lip-sync improvement with D-ID

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built by [Ncubelabs.com](https://ncubelabs.com) for MiniMax Hackathon 2025.

Powered by:
- [MiniMax](https://www.minimax.io/) - AI APIs (M2, Speech-02-HD, S2V-01)
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python API framework
