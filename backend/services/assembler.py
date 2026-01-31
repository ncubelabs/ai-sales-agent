"""FFmpeg assembler for combining audio and video"""
import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional


OUTPUT_DIR = Path(__file__).parent.parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


async def merge_audio_video(
    audio_path: str,
    video_path: str,
    output_filename: Optional[str] = None
) -> str:
    """Merge audio and video files using FFmpeg"""
    
    if output_filename is None:
        output_filename = f"final_{uuid.uuid4().hex[:8]}.mp4"
    
    output_path = OUTPUT_DIR / output_filename
    
    # FFmpeg command to merge audio and video
    # -y: overwrite output
    # -i: input files
    # -c:v copy: copy video codec
    # -c:a aac: encode audio as AAC
    # -shortest: end when shortest stream ends
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"FFmpeg failed: {stderr.decode()}")
    
    return str(output_path)


async def create_video_from_audio_and_image(
    audio_path: str,
    image_path: str,
    output_filename: Optional[str] = None
) -> str:
    """Create video from static image and audio (fallback if no video generation)"""
    
    if output_filename is None:
        output_filename = f"slideshow_{uuid.uuid4().hex[:8]}.mp4"
    
    output_path = OUTPUT_DIR / output_filename
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        raise Exception(f"FFmpeg failed: {stderr.decode()}")
    
    return str(output_path)


async def download_file(url: str, output_dir: Path = OUTPUT_DIR) -> str:
    """Download a file from URL"""
    import httpx
    
    filename = f"download_{uuid.uuid4().hex[:8]}"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        
        # Try to get extension from content-type
        content_type = response.headers.get("content-type", "")
        if "video" in content_type:
            filename += ".mp4"
        elif "audio" in content_type:
            filename += ".mp3"
        else:
            filename += ".bin"
        
        output_path = output_dir / filename
        output_path.write_bytes(response.content)
    
    return str(output_path)
