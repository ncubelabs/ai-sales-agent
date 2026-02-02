# TTS Microservice - Edge TTS (Microsoft's free TTS API)
# Fast, reliable, high-quality voices with no GPU requirements
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Edge TTS and dependencies
RUN pip install --no-cache-dir \
    edge-tts \
    fastapi==0.109.0 \
    uvicorn==0.27.0 \
    python-multipart==0.0.9 \
    aiofiles==23.2.1 \
    pydub==0.25.1 \
    soundfile

# Copy application
COPY requirements.txt .
COPY server_edge.py ./server.py

# Create directories for voices (reference samples for future XTTS)
RUN mkdir -p /app/voices

# Expose port
EXPOSE 5050

# Environment
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5050/health || exit 1

# Run server
CMD ["python", "server.py"]
