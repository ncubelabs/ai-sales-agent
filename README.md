# AI Sales Agent

Generate personalized AI-powered video sales pitches in seconds. Upload your photo and voice sample, enter a company URL, and get a custom talking-head video with your face, your cloned voice, and a personalized script.

![AI Sales Agent](https://img.shields.io/badge/AI-Sales%20Agent-6366f1?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-16-black?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square)
![Self-Hosted](https://img.shields.io/badge/Self--Hosted-OSS-22c55e?style=flat-square)
![MiniMax](https://img.shields.io/badge/MiniMax-Fallback-ff6b6b?style=flat-square)

## Features

- **Personalized Videos** - Your face + your cloned voice in every video
- **Voice Cloning** - Clone any voice from a 10-20 second sample
- **Company Research** - AI analyzes target company websites
- **Custom Scripts** - AI generates personalized 30-second sales pitches
- **Talking Head Videos** - S2V-01 subject-reference video generation
- **Voice Profiles** - Save and reuse cloned voices
- **Self-Hosted Option** - Run entirely on your own infrastructure (NEW!)

## Architecture

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────────────┐
│    Frontend     │  HTTP   │     Backend     │         │   AI Providers          │
│   Next.js 16    │◄───────►│    FastAPI      │◄───────►├─────────────────────────┤
│   Port: 3000    │         │   Port: 8000    │         │ Text: vLLM / MiniMax    │
└─────────────────┘         └────────┬────────┘         │ TTS:  Edge TTS / Coqui  │
                                     │                  │ Video: SadTalker / S2V  │
                            ┌────────▼────────┐         └─────────────────────────┘
                            │  TTS Service    │
                            │  (Docker)       │
                            │  Port: 5050     │
                            └─────────────────┘
```

## Provider Options

| Component | Self-Hosted (OSS) | Cloud (MiniMax) |
|-----------|-------------------|-----------------|
| **Text** | vLLM + Llama 3.1 70B | MiniMax-M2 |
| **TTS** | Edge TTS (Docker) | speech-02-hd |
| **Voice Clone** | Edge TTS voices* | MiniMax Clone |
| **Video** | SadTalker | S2V-01/Hailuo |

*Note: Edge TTS uses Microsoft Neural voices. Full voice cloning via XTTS requires compatible GPU/PyTorch configuration.

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.12+
- Docker (for TTS service)
- FFmpeg

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

# Copy environment template
cp .env.example .env
# Edit .env with your configuration
```

### 3. Start TTS Service (Docker)

```bash
cd backend
docker compose up -d xtts
```

This starts the TTS microservice on port 5050.

### 4. Start Backend

```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev
```

### 6. Open the App

Navigate to http://localhost:3000

## Configuration

### Environment Variables (.env)

```env
# =============================================================================
# Provider Selection
# =============================================================================
PROVIDER_TEXT=vllm          # Options: vllm, minimax
PROVIDER_TTS=coqui          # Options: coqui, edge, minimax
PROVIDER_VIDEO=sadtalker    # Options: sadtalker, minimax

# Fallback chain (if primary fails)
PROVIDER_TEXT_FALLBACK=vllm,minimax
PROVIDER_TTS_FALLBACK=coqui,edge,minimax
PROVIDER_VIDEO_FALLBACK=sadtalker,minimax

# =============================================================================
# vLLM Configuration (Self-hosted text generation)
# =============================================================================
PROVIDER_VLLM_BASE_URL=http://localhost:8000
PROVIDER_VLLM_MODEL=meta-llama/Llama-3.1-70B-Instruct

# =============================================================================
# Coqui/Edge TTS Configuration (Docker microservice)
# =============================================================================
PROVIDER_COQUI_MODE=service
PROVIDER_COQUI_SERVICE_URL=http://localhost:5050
PROVIDER_COQUI_VOICES_DIR=./voices

# =============================================================================
# SadTalker Configuration (Self-hosted video)
# =============================================================================
PROVIDER_SADTALKER_CHECKPOINT=./models/sadtalker
PROVIDER_SADTALKER_DEVICE=cuda
PROVIDER_SADTALKER_PREPROCESS=crop

# =============================================================================
# MiniMax API (Fallback / Cloud option)
# =============================================================================
MINIMAX_API_KEY=your-api-key-here
MINIMAX_GROUP_ID=your-group-id-here
MINIMAX_BASE_URL=https://api.minimax.io/v1

# =============================================================================
# Pipeline
# =============================================================================
ENABLE_PERSONALIZED_PIPELINE=true
```

## Services Status

Check all services are running:

```bash
# TTS Service
curl http://localhost:5050/health
# Expected: {"status":"healthy","cuda":false,"model_loaded":true,"backend":"edge-tts"}

# Backend API
curl http://localhost:8000/health
# Expected: {"status":"healthy"}

# Provider status
curl http://localhost:8000/providers
```

## API Usage

### Personalized Video Generation

```bash
curl -X POST http://localhost:8000/api/personalized/generate \
  -F "company_url=https://stripe.com" \
  -F "person_image=@photo.jpg" \
  -F "voice_sample=@voice.mp3" \
  -F "our_product=AI consulting services"
```

### Text-to-Speech

```bash
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice_id": "en-US-AriaNeural"}' \
  --output speech.mp3
```

### Available TTS Voices

| Voice ID | Name | Language |
|----------|------|----------|
| en-US-AriaNeural | Aria | English (US) |
| en-US-GuyNeural | Guy | English (US) |
| en-US-JennyNeural | Jenny | English (US) |
| en-GB-SoniaNeural | Sonia | English (UK) |
| en-GB-RyanNeural | Ryan | English (UK) |
| zh-CN-XiaoxiaoNeural | Xiaoxiao | Chinese |
| ja-JP-NanamiNeural | Nanami | Japanese |
| es-ES-ElviraNeural | Elvira | Spanish |
| fr-FR-DeniseNeural | Denise | French |

### API Documentation

Interactive docs available at http://localhost:8000/docs

## Project Structure

```
ai-sales-agent/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── docker-compose.yml         # TTS service orchestration
│   ├── providers/                 # Provider abstraction layer
│   │   ├── base.py               # Abstract interfaces
│   │   ├── config.py             # Environment configuration
│   │   ├── registry.py           # Provider factory + fallbacks
│   │   ├── text/                 # Text generation providers
│   │   │   ├── minimax.py        # MiniMax M2 (cloud)
│   │   │   └── vllm.py           # vLLM + Llama (self-hosted)
│   │   ├── tts/                  # TTS providers
│   │   │   ├── minimax.py        # MiniMax Speech (cloud)
│   │   │   ├── coqui.py          # XTTS/Edge TTS service
│   │   │   └── edge.py           # Edge TTS direct
│   │   └── video/                # Video providers
│   │       ├── minimax.py        # MiniMax Hailuo (cloud)
│   │       └── sadtalker.py      # SadTalker (self-hosted)
│   ├── services/
│   │   ├── ai_service.py         # Unified AI service layer
│   │   ├── minimax.py            # Legacy MiniMax client
│   │   └── xtts-service/         # TTS Docker microservice
│   │       ├── Dockerfile
│   │       ├── server.py         # Edge TTS FastAPI server
│   │       └── requirements.txt
│   ├── routers/                   # API endpoints
│   ├── prompts/                   # LLM prompt templates
│   ├── voices/                    # Cloned voice samples
│   └── outputs/                   # Generated files
├── frontend/
│   ├── app/                       # Next.js app router
│   ├── components/                # React components
│   └── lib/                       # API client
├── docs/
│   ├── OSS_MIGRATION.md          # Self-hosted setup guide
│   ├── SYSTEM_ARCHITECTURE.md    # Detailed architecture
│   └── PROMPTS.md                # LLM prompt documentation
└── pitch-deck.html               # Hackathon presentation
```

## GPU Requirements (Self-Hosted)

| Model | VRAM |
|-------|------|
| vLLM (Llama 70B) | ~40GB |
| SadTalker | ~8GB |
| **Total** | ~48GB |

TTS runs in Docker without GPU (Edge TTS is cloud-based synthesis).

Recommended hardware:
- NVIDIA A100 80GB
- 2x A100 40GB (tensor parallelism)
- DGX SPARK

## Pipeline Flow

| Step | Duration | Description |
|------|----------|-------------|
| Research | 5-10s | Scrape URL + AI company analysis |
| Script | 5-8s | Generate personalized pitch |
| TTS | 2-5s | Generate speech (Edge TTS) |
| Video | 3-4min | Talking head generation |
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
- Provider abstraction layer
- httpx (async HTTP)
- Pydantic (validation)

### TTS Service (Docker)
- Edge TTS (Microsoft Neural voices)
- FastAPI microservice
- Lightweight Python 3.11 image

### AI Providers
| Provider | Self-Hosted | Cloud |
|----------|-------------|-------|
| Text | vLLM + Llama 3.1 | MiniMax M2 |
| TTS | Edge TTS | MiniMax speech-02-hd |
| Video | SadTalker | MiniMax S2V-01 |

## Troubleshooting

### TTS Service Not Responding
```bash
docker compose logs xtts
docker compose restart xtts
```

### Backend Connection Error
Ensure TTS service is running:
```bash
curl http://localhost:5050/health
```

### Provider Fallback
If you see "Using fallback provider", check primary provider logs.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

Built by [Ncubelabs.com](https://ncubelabs.com) for MiniMax Hackathon 2025.

Powered by:
- [MiniMax](https://www.minimax.io/) - AI APIs (fallback)
- [Edge TTS](https://github.com/rany2/edge-tts) - Microsoft Neural TTS
- [vLLM](https://github.com/vllm-project/vllm) - Fast LLM inference
- [SadTalker](https://github.com/OpenTalker/SadTalker) - Talking head generation
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Python API framework
