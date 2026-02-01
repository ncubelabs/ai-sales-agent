"""Asset Storage Service - Handle file uploads and validation

Validates and stores uploaded images (for face reference) and voice samples
(for voice cloning), then uploads to MiniMax and returns file IDs.
"""
import os
import base64
import httpx
from pathlib import Path
from typing import Optional, Tuple
import uuid

# Optional: import PIL for image validation if available
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from services.minimax import get_client

# Storage directories
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Validation constants
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a'}
MIN_IMAGE_SIZE = 512  # pixels
MIN_AUDIO_DURATION = 10  # seconds
MAX_AUDIO_DURATION = 300  # seconds (5 minutes)


class AssetValidationError(Exception):
    """Raised when asset validation fails"""
    pass


def validate_image(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """Validate an image file for face reference

    Requirements:
    - JPEG or PNG format
    - Minimum 512x512 pixels
    - Should contain a face (not validated here, left to MiniMax)

    Returns:
        (is_valid, error_message or empty string)
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f"Invalid image format. Allowed: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"

    if len(file_bytes) < 1000:
        return False, "Image file is too small or corrupt"

    if HAS_PIL:
        try:
            import io
            img = Image.open(io.BytesIO(file_bytes))
            width, height = img.size
            if width < MIN_IMAGE_SIZE or height < MIN_IMAGE_SIZE:
                return False, f"Image must be at least {MIN_IMAGE_SIZE}x{MIN_IMAGE_SIZE} pixels. Got {width}x{height}"
        except Exception as e:
            return False, f"Failed to read image: {str(e)}"
    else:
        # Basic header check without PIL
        if ext in {'.jpg', '.jpeg'}:
            if not file_bytes[:2] == b'\xff\xd8':
                return False, "Invalid JPEG file header"
        elif ext == '.png':
            if not file_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                return False, "Invalid PNG file header"

    return True, ""


def validate_audio(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """Validate an audio file for voice cloning

    Requirements:
    - MP3, WAV, or M4A format
    - 10 seconds to 5 minutes duration
    - Clear speech content (not validated here)

    Returns:
        (is_valid, error_message or empty string)
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        return False, f"Invalid audio format. Allowed: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"

    # Minimum file size check (very small files are likely corrupt)
    # Even highly compressed audio at 32kbps for 10 sec = ~40KB
    if len(file_bytes) < 5000:
        return False, "Audio file is too small or corrupt."

    # Basic header validation
    if ext == '.mp3':
        # Check for MP3 magic bytes (ID3 or frame sync)
        if not (file_bytes[:3] == b'ID3' or file_bytes[:2] == b'\xff\xfb' or file_bytes[:2] == b'\xff\xfa'):
            return False, "Invalid MP3 file header"
    elif ext == '.wav':
        if not file_bytes[:4] == b'RIFF':
            return False, "Invalid WAV file header"
    elif ext == '.m4a':
        # M4A files start with ftyp box (offset 4)
        if b'ftyp' not in file_bytes[:32]:
            return False, "Invalid M4A file header"

    # Note: Duration validation is left to MiniMax API which will reject
    # files shorter than 10 seconds or longer than 5 minutes
    return True, ""


async def save_and_upload_image(file_bytes: bytes, filename: str) -> str:
    """Save an image locally and upload to a public hosting service

    Args:
        file_bytes: Image file content
        filename: Original filename

    Returns:
        Public URL for the uploaded image (for use with subject_reference)

    Raises:
        AssetValidationError: If validation fails
    """
    is_valid, error = validate_image(file_bytes, filename)
    if not is_valid:
        raise AssetValidationError(error)

    # Save locally with unique name
    ext = Path(filename).suffix.lower()
    local_filename = f"image_{uuid.uuid4().hex[:12]}{ext}"
    local_path = UPLOAD_DIR / local_filename
    local_path.write_bytes(file_bytes)

    # Upload to uguu.se (free, no API key needed) to get a public URL
    # This is needed because MiniMax subject_reference requires image URLs, not file uploads
    async with httpx.AsyncClient(timeout=60.0) as client:
        files = {"files[]": (filename, file_bytes)}
        response = await client.post("https://uguu.se/upload", files=files)

        if response.status_code != 200:
            raise AssetValidationError(f"Failed to upload image to hosting service: {response.text}")

        try:
            data = response.json()
            if not data.get("success") or not data.get("files"):
                raise AssetValidationError(f"Image upload failed: {data}")
            image_url = data["files"][0]["url"]
        except Exception as e:
            raise AssetValidationError(f"Failed to parse image host response: {str(e)}")

    return image_url


async def save_and_upload_audio(file_bytes: bytes, filename: str) -> str:
    """Save an audio file locally and upload to MiniMax

    Args:
        file_bytes: Audio file content
        filename: Original filename

    Returns:
        MiniMax file_id for the uploaded audio

    Raises:
        AssetValidationError: If validation fails
    """
    is_valid, error = validate_audio(file_bytes, filename)
    if not is_valid:
        raise AssetValidationError(error)

    # Save locally with unique name
    ext = Path(filename).suffix.lower()
    local_filename = f"audio_{uuid.uuid4().hex[:12]}{ext}"
    local_path = UPLOAD_DIR / local_filename
    local_path.write_bytes(file_bytes)

    # Upload to MiniMax for voice cloning
    client = get_client()
    file_id = await client.upload_file(file_bytes, filename, purpose="voice_clone")

    return file_id
