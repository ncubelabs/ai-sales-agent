# OSS Migration Guide

This document describes the migration from MiniMax cloud APIs to self-hosted open-source models.

## Architecture Overview

```
backend/
├── providers/           # Provider abstraction layer
│   ├── base.py         # Abstract interfaces
│   ├── config.py       # Environment configuration
│   ├── registry.py     # Provider factory + fallbacks
│   ├── text/           # Text generation providers
│   │   ├── minimax.py  # MiniMax M2 (cloud)
│   │   └── vllm.py     # vLLM + Llama 3.1 (self-hosted)
│   ├── tts/            # Text-to-speech providers
│   │   ├── minimax.py  # MiniMax Speech (cloud)
│   │   ├── coqui.py    # XTTS/Edge TTS service
│   │   └── edge.py     # Edge TTS direct
│   └── video/          # Video generation providers
│       ├── minimax.py  # MiniMax Hailuo/S2V (cloud)
│       └── sadtalker.py # SadTalker (self-hosted)
├── services/
│   ├── ai_service.py   # Unified service layer
│   └── xtts-service/   # TTS Docker microservice
│       ├── Dockerfile
│       ├── server_edge.py
│       └── requirements.txt
└── .env                # Provider configuration
```

## Provider Comparison

| Component | MiniMax (Cloud) | OSS (Self-hosted) |
|-----------|-----------------|-------------------|
| **Text** | MiniMax-M2 | Llama 3.1 70B via vLLM |
| **TTS** | speech-02-hd | Edge TTS (Docker) |
| **Voice Clone** | MiniMax Clone | Edge TTS presets* |
| **Video** | T2V-01/S2V-01 | SadTalker (talking head) |

*Note: True voice cloning via XTTS requires compatible PyTorch/torchaudio on ARM64. Voice references are stored for future use.

## Quick Start

### 1. Keep Using MiniMax (Default)

No changes needed. The default configuration uses MiniMax:

```env
PROVIDER_TEXT=minimax
PROVIDER_TTS=minimax
PROVIDER_VIDEO=minimax
```

### 2. Switch to Self-Hosted

Update `.env`:

```env
PROVIDER_TEXT=vllm
PROVIDER_TTS=coqui
PROVIDER_VIDEO=sadtalker
```

## Setting Up Self-Hosted Providers

### TTS Service (Docker) - Recommended

The TTS service runs as a Docker microservice using Edge TTS (Microsoft Neural voices).

1. Start the service:
```bash
cd backend
docker compose up -d xtts
```

2. Verify it's running:
```bash
curl http://localhost:5050/health
# Expected: {"status":"healthy","cuda":false,"model_loaded":true,"backend":"edge-tts"}
```

3. Configure backend:
```env
PROVIDER_TTS=coqui
PROVIDER_COQUI_MODE=service
PROVIDER_COQUI_SERVICE_URL=http://localhost:5050
```

#### Available Voices

| Voice ID | Name | Language | Gender |
|----------|------|----------|--------|
| en-US-AriaNeural | Aria | English (US) | Female |
| en-US-GuyNeural | Guy | English (US) | Male |
| en-US-JennyNeural | Jenny | English (US) | Female |
| en-GB-SoniaNeural | Sonia | English (UK) | Female |
| en-GB-RyanNeural | Ryan | English (UK) | Male |
| zh-CN-XiaoxiaoNeural | Xiaoxiao | Chinese | Female |
| zh-CN-YunxiNeural | Yunxi | Chinese | Male |
| ja-JP-NanamiNeural | Nanami | Japanese | Female |
| es-ES-ElviraNeural | Elvira | Spanish | Female |
| fr-FR-DeniseNeural | Denise | French | Female |

#### TTS API Usage

```bash
# Synthesize speech
curl -X POST http://localhost:5050/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice_id": "en-US-AriaNeural"}' \
  --output speech.mp3

# List available voices
curl http://localhost:5050/voices

# Store voice reference (for future XTTS support)
curl -X POST http://localhost:5050/clone \
  -F "audio=@voice_sample.mp3" \
  -F "name=MyVoice"
```

### vLLM (Text Generation)

1. Install vLLM:
```bash
pip install vllm>=0.4.0
```

2. Start the server:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-70B-Instruct \
    --tensor-parallel-size 2  # For multi-GPU
```

3. Configure:
```env
PROVIDER_TEXT=vllm
PROVIDER_VLLM_BASE_URL=http://localhost:8000
PROVIDER_VLLM_MODEL=meta-llama/Llama-3.1-70B-Instruct
```

### SadTalker (Talking Head Video)

1. Clone and set up:
```bash
git clone https://github.com/OpenTalker/SadTalker
cd SadTalker
pip install -r requirements.txt

# Download checkpoints
# See: https://github.com/OpenTalker/SadTalker#-2-download-trained-models
```

2. Configure:
```env
PROVIDER_VIDEO=sadtalker
PROVIDER_SADTALKER_CHECKPOINT=./models/sadtalker
PROVIDER_SADTALKER_DEVICE=cuda
```

## GPU Requirements

| Model | VRAM | Notes |
|-------|------|-------|
| vLLM (Llama 70B) | ~40GB | Requires tensor parallelism on smaller GPUs |
| SadTalker | ~8GB | |
| **Total** | ~48GB | |

TTS (Edge TTS) runs in Docker without GPU - it uses Microsoft's cloud synthesis.

Recommended hardware:
- NVIDIA A100 80GB
- 2x A100 40GB (tensor parallelism)
- DGX SPARK

## Fallback Chains

Configure automatic fallbacks:

```env
PROVIDER_TEXT_FALLBACK=vllm,minimax
PROVIDER_TTS_FALLBACK=coqui,edge,minimax
PROVIDER_VIDEO_FALLBACK=sadtalker,minimax
```

If the primary provider fails, the system automatically tries the next one.

## Docker Compose

The `backend/docker-compose.yml` orchestrates services:

```yaml
services:
  xtts:
    build: ./services/xtts-service
    ports:
      - "5050:5050"
    volumes:
      - ./voices:/app/voices
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5050/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Start all services:
```bash
docker compose up -d
```

## API Compatibility

All existing API endpoints work identically regardless of provider:

```bash
# Research a company
curl -X POST http://localhost:8000/api/research \
    -H "Content-Type: application/json" \
    -d '{"url": "https://example.com"}'

# Generate speech
curl -X POST http://localhost:8000/api/voice \
    -H "Content-Type: application/json" \
    -d '{"text": "Hello world", "voice_id": "en-US-AriaNeural"}'

# Check current providers
curl http://localhost:8000/providers
```

## Testing

Run the test script:

```bash
cd backend
source venv/bin/activate
python test_oss_providers.py
```

## Verification

1. Check TTS service:
```bash
curl http://localhost:5050/health
```

2. Check backend:
```bash
curl http://localhost:8000/health
```

3. Check provider status:
```bash
curl http://localhost:8000/providers
```

4. Start the server and check logs:
```bash
uvicorn main:app --reload
```

You should see:
```
=== Provider Configuration ===
Text provider: vllm
TTS provider: coqui
Video provider: sadtalker

Available providers:
  Text: minimax, vllm
  TTS: minimax, coqui, edge
  Video: minimax, sadtalker
```

## Troubleshooting

### TTS Service Not Responding
```bash
docker compose logs xtts
docker compose restart xtts
```

### vLLM Connection Error
```
Cannot connect to vLLM server at http://localhost:8000
```
→ Start vLLM server first

### SadTalker Checkpoint Error
```
SadTalker checkpoint not found
```
→ Download checkpoints from the SadTalker repo

### Fallback to MiniMax
If you see "Using fallback provider: minimax", your primary provider failed.
Check the logs for the specific error.

## ARM64/aarch64 Notes (DGX SPARK)

When running on ARM64 architecture (like NVIDIA DGX SPARK with GB10 GPU):

1. **PyTorch**: Use NVIDIA's PyTorch container or build from source. Standard wheels may not support sm_121 compute capability.

2. **torchaudio**: NVIDIA's custom PyTorch build (2.10.0a0+) has ABI incompatibilities with standard torchaudio. This is why we use Edge TTS (no torchaudio needed).

3. **Voice Cloning**: True voice cloning via XTTS v2 requires compatible torchaudio. Voice references are stored in `/app/voices` for future use when torchaudio compatibility is resolved.

4. **Edge TTS**: Works on all architectures since it uses Microsoft's cloud API for synthesis. High quality Neural voices with no GPU requirements.

## Future Improvements

1. **XTTS v2 Integration**: When torchaudio compatibility is resolved for NVIDIA's ARM64 PyTorch builds, enable true voice cloning.

2. **Local LLM**: For fully offline operation, integrate local Llama inference.

3. **Offline TTS**: Implement Piper TTS for completely offline voice synthesis.
