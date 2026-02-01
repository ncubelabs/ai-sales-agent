"""Voice Profile Management - Store and manage cloned voice profiles

Provides persistent storage for cloned voice profiles so they can be
reused across multiple video generations without re-cloning.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any
from pydantic import BaseModel, field_validator

from services.minimax import get_client
from services.asset_storage import save_and_upload_audio, AssetValidationError

# Storage location
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
PROFILES_FILE = DATA_DIR / "voice_profiles.json"


class VoiceProfile(BaseModel):
    """A saved voice profile"""
    id: str
    name: str
    minimax_voice_id: str
    minimax_file_id: str
    created_at: str
    audio_duration_estimate: Optional[int] = None  # seconds

    @field_validator('minimax_file_id', mode='before')
    @classmethod
    def coerce_file_id_to_str(cls, v: Any) -> str:
        """Ensure file_id is always a string (API may return int)"""
        return str(v) if v is not None else ""


class VoiceProfileStore:
    """Manages voice profile persistence"""

    def __init__(self):
        self._profiles: dict[str, VoiceProfile] = {}
        self._load()

    def _load(self):
        """Load profiles from disk"""
        if PROFILES_FILE.exists():
            try:
                data = json.loads(PROFILES_FILE.read_text())
                for profile_data in data.get("profiles", []):
                    profile = VoiceProfile(**profile_data)
                    self._profiles[profile.id] = profile
            except (json.JSONDecodeError, Exception):
                # Start fresh if file is corrupt
                self._profiles = {}

    def _save(self):
        """Save profiles to disk"""
        data = {
            "profiles": [p.model_dump() for p in self._profiles.values()]
        }
        PROFILES_FILE.write_text(json.dumps(data, indent=2))

    def add(self, profile: VoiceProfile) -> None:
        """Add a new profile"""
        self._profiles[profile.id] = profile
        self._save()

    def get(self, profile_id: str) -> Optional[VoiceProfile]:
        """Get a profile by ID"""
        return self._profiles.get(profile_id)

    def get_by_name(self, name: str) -> Optional[VoiceProfile]:
        """Get a profile by name"""
        for profile in self._profiles.values():
            if profile.name.lower() == name.lower():
                return profile
        return None

    def list_all(self) -> List[VoiceProfile]:
        """List all profiles"""
        return list(self._profiles.values())

    def delete(self, profile_id: str) -> bool:
        """Delete a profile by ID"""
        if profile_id in self._profiles:
            del self._profiles[profile_id]
            self._save()
            return True
        return False


# Singleton store instance
_store: Optional[VoiceProfileStore] = None


def get_store() -> VoiceProfileStore:
    """Get the voice profile store singleton"""
    global _store
    if _store is None:
        _store = VoiceProfileStore()
    return _store


async def create_voice_profile(
    audio_bytes: bytes,
    filename: str,
    profile_name: str
) -> VoiceProfile:
    """Create a new voice profile from an audio sample

    Args:
        audio_bytes: Audio file content (MP3/WAV/M4A, 10s-5min)
        filename: Original filename
        profile_name: Display name for this voice profile

    Returns:
        The created VoiceProfile

    Raises:
        AssetValidationError: If audio validation fails
        Exception: If MiniMax API calls fail
    """
    store = get_store()

    # Check for duplicate name
    existing = store.get_by_name(profile_name)
    if existing:
        raise ValueError(f"A voice profile named '{profile_name}' already exists")

    # Upload audio to MiniMax
    file_id = await save_and_upload_audio(audio_bytes, filename)

    # Generate unique voice ID for MiniMax
    # Requirements: 8+ chars, starts with letter, alphanumeric
    profile_id = uuid.uuid4().hex[:12]
    voice_id = f"voice{profile_id}"  # e.g., "voicea1b2c3d4e5f6"

    # Clone the voice - registers it with MiniMax
    client = get_client()
    voice_id = await client.clone_voice(str(file_id), voice_id)

    # Ensure file_id is a string
    file_id = str(file_id)

    # Estimate duration from file size (rough: 16KB/sec for MP3)
    duration_estimate = len(audio_bytes) // 16000

    # Create and save profile
    profile = VoiceProfile(
        id=profile_id,
        name=profile_name,
        minimax_voice_id=voice_id,
        minimax_file_id=file_id,
        created_at=datetime.utcnow().isoformat(),
        audio_duration_estimate=duration_estimate
    )

    store.add(profile)
    return profile


def get_voice_profile(profile_id: str) -> Optional[VoiceProfile]:
    """Get a voice profile by ID"""
    return get_store().get(profile_id)


def list_voice_profiles() -> List[VoiceProfile]:
    """List all saved voice profiles"""
    return get_store().list_all()


def delete_voice_profile(profile_id: str) -> bool:
    """Delete a voice profile by ID"""
    return get_store().delete(profile_id)
