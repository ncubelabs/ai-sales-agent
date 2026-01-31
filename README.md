# AI Sales Agent

Generate personalized AI-powered video sales pitches in minutes. Simply enter a company URL and get a custom sales video with AI-generated research, script, voice, and video.

![AI Sales Agent](https://img.shields.io/badge/AI-Sales%20Agent-6366f1?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square)
![MiniMax](https://img.shields.io/badge/MiniMax-API-ff6b6b?style=flat-square)

## Features

- **Company Research** - Automatically scrapes and analyzes target company websites
- **Personalized Scripts** - AI generates custom 30-second sales pitches
- **Voice Synthesis** - Multiple AI voices with emotion control
- **Video Generation** - AI-generated professional video content
- **Audio/Video Merge** - Combines voice and video into final deliverable

## Demo

```
User Input: https://stripe.com
     ↓
[Research] → Company analysis, pain points, opportunities
     ↓
[Script] → "Hey, saw Stripe's expanding into banking services..."
     ↓
[Voice] → AI voiceover (MP3)
     ↓
[Video] → AI-generated video (MP4)
     ↓
[Output] → Final merged sales video
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

1. Enter a company URL (e.g., `https://stripe.com`)
2. Enter your name
3. Select a voice
4. Click "Generate Video"
5. Wait 3-5 minutes for full video generation

### API

```bash
# Generate with video (3-5 minutes)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://stripe.com",
    "our_product": "AI consulting services",
    "voice_id": "male-qn-qingse",
    "skip_video": false
  }'

# Generate without video (30 seconds)
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company_url": "https://stripe.com",
    "our_product": "AI consulting services",
    "voice_id": "female-shaonv",
    "skip_video": true
  }'

# Check job status
curl http://localhost:8000/api/generate/status/{job_id}
```

### API Documentation

Interactive docs available at http://localhost:8000/docs

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│    Frontend     │  HTTP   │     Backend     │  HTTPS  │   MiniMax APIs  │
│   Next.js 16    │◄───────►│    FastAPI      │◄───────►│ Text/TTS/Video  │
│   Port: 3000    │         │   Port: 8000    │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### Pipeline Flow

| Step | Duration | Description |
|------|----------|-------------|
| Research | 5-10s | Scrape URL + AI company analysis |
| Script | 5-8s | Generate personalized 30-sec pitch |
| Voice | 5-10s | Text-to-speech synthesis |
| Video | 3-4min | AI video generation |
| Merge | 2-5s | FFmpeg audio+video combine |

See [SYSTEM_ARCHITECTURE.md](docs/SYSTEM_ARCHITECTURE.md) for detailed diagrams.

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

### External APIs
- **MiniMax-M2** - Text generation
- **MiniMax speech-02-hd** - Text-to-speech
- **MiniMax T2V-01** - Video generation

### Infrastructure
- FFmpeg - Audio/video processing
- Local filesystem - Output storage

## Project Structure

```
ai-sales-agent/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── routers/
│   │   ├── generate.py      # Main pipeline endpoint
│   │   ├── research.py      # Company research
│   │   ├── script.py        # Script generation
│   │   ├── voice.py         # TTS endpoint
│   │   └── video.py         # Video endpoint
│   ├── services/
│   │   ├── minimax.py       # MiniMax API client
│   │   ├── scraper.py       # Web scraper
│   │   └── assembler.py     # FFmpeg wrapper
│   ├── prompts/             # LLM prompt templates
│   ├── outputs/             # Generated files
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx         # Main page
│   │   ├── layout.tsx       # Root layout
│   │   └── globals.css      # Styles
│   ├── components/          # React components
│   ├── lib/
│   │   └── api.ts           # API client
│   └── package.json
└── docs/
    └── SYSTEM_ARCHITECTURE.md
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MINIMAX_API_KEY` | Yes | MiniMax API key |
| `MINIMAX_GROUP_ID` | Yes | MiniMax Group ID (for TTS) |
| `MINIMAX_BASE_URL` | No | API base URL (default: https://api.minimax.io/v1) |

### Voice Options

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
├── audio_{job_id}.mp3    # Voice narration (~500KB)
├── video_{job_id}.mp4    # AI video (~1MB)
└── final_{job_id}.mp4    # Merged output (~1.1MB)
```

## Limitations

- **Development only** - No authentication, CORS allows all origins
- **In-memory storage** - Job state lost on server restart
- **Video duration** - Fixed 6-second AI videos
- **Rate limits** - Subject to MiniMax API limits

## Roadmap

- [ ] User authentication
- [ ] Persistent job storage (Redis)
- [ ] Custom video duration
- [ ] Multiple output formats
- [ ] Batch processing
- [ ] CRM integrations

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built by [NCube Labs](https://ncubelabs.ai) for Hackathon 2025.

Powered by:
- [MiniMax](https://www.minimax.io/) - AI APIs
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python API framework
