"""SadTalker talking head video generation provider."""

import os
import sys
import uuid
import asyncio
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor

from ..base import VideoProvider, VideoGenerationResult
from ..config import ProviderConfig

logger = logging.getLogger(__name__)

# Thread pool for blocking video operations
_executor = ThreadPoolExecutor(max_workers=1)


class SadTalkerVideoProvider(VideoProvider):
    """Talking head video generation using SadTalker.

    SadTalker generates realistic talking head videos from:
    - A face image (portrait photo)
    - An audio file (speech)

    Clone and set up from: https://github.com/OpenTalker/SadTalker

    Setup:
        git clone https://github.com/OpenTalker/SadTalker
        cd SadTalker
        pip install -r requirements.txt
        # Download checkpoints from:
        # https://github.com/OpenTalker/SadTalker#-2-download-trained-models
    """

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.checkpoint_dir = Path(config.sadtalker_checkpoint)
        self.device = config.sadtalker_device
        self.preprocess = config.sadtalker_preprocess
        self.still = config.sadtalker_still
        self.enhancer = config.sadtalker_enhancer

        self._initialized = False
        self._sadtalker = None

    def _ensure_initialized(self):
        """Lazy initialization of SadTalker."""
        if self._initialized:
            return

        # Check if checkpoint exists
        if not self.checkpoint_dir.exists():
            raise FileNotFoundError(
                f"SadTalker checkpoint not found at {self.checkpoint_dir}. "
                f"Download from: https://github.com/OpenTalker/SadTalker#-2-download-trained-models"
            )

        logger.info(f"SadTalker checkpoints at {self.checkpoint_dir}")
        self._initialized = True

    @property
    def name(self) -> str:
        return "sadtalker"

    async def generate(
        self,
        prompt: str,
        duration: int = 6,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate video from text prompt.

        Note: SadTalker is a talking head generator and requires audio + face image.
        For text-to-video, use a different provider like MiniMax.
        This method will raise NotImplementedError.
        """
        raise NotImplementedError(
            "SadTalker requires audio + face image. Use generate_talking_head() instead, "
            "or use a text-to-video provider like MiniMax for prompt-based generation."
        )

    async def generate_talking_head(
        self,
        audio_path: str,
        face_image_path: str,
        output_path: Optional[str] = None,
        **kwargs,
    ) -> VideoGenerationResult:
        """Generate talking head video from audio and face image.

        Args:
            audio_path: Path to audio file (WAV, MP3)
            face_image_path: Path to face image (PNG, JPG)
            output_path: Optional output path for video
            **kwargs: Additional SadTalker options

        Returns:
            VideoGenerationResult with video bytes or path
        """
        self._ensure_initialized()

        audio_path = Path(audio_path)
        face_image_path = Path(face_image_path)

        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not face_image_path.exists():
            raise FileNotFoundError(f"Face image not found: {face_image_path}")

        # Generate output path if not provided
        if output_path is None:
            output_dir = Path(tempfile.gettempdir()) / "sadtalker_output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"talking_head_{uuid.uuid4().hex}.mp4")

        # Run SadTalker in thread pool
        loop = asyncio.get_event_loop()
        result_path = await loop.run_in_executor(
            _executor,
            self._run_sadtalker,
            str(audio_path),
            str(face_image_path),
            output_path,
        )

        # Read video bytes
        result_path = Path(result_path)
        if result_path.exists():
            video_bytes = result_path.read_bytes()
            return VideoGenerationResult(
                video_bytes=video_bytes,
                video_path=str(result_path),
                status="completed",
            )
        else:
            raise RuntimeError(f"SadTalker output not found at {result_path}")

    def _run_sadtalker(
        self,
        audio_path: str,
        face_image_path: str,
        output_path: str,
    ) -> str:
        """Run SadTalker inference (blocking operation)."""
        # Try Python API first (if SadTalker is installed as a package)
        try:
            return self._run_python_api(audio_path, face_image_path, output_path)
        except ImportError:
            logger.info("SadTalker Python API not available, trying CLI")

        # Fall back to CLI
        return self._run_cli(audio_path, face_image_path, output_path)

    def _run_python_api(
        self,
        audio_path: str,
        face_image_path: str,
        output_path: str,
    ) -> str:
        """Run SadTalker using Python API."""
        # Add SadTalker to path if needed
        sadtalker_path = self.checkpoint_dir.parent
        if str(sadtalker_path) not in sys.path:
            sys.path.insert(0, str(sadtalker_path))

        try:
            from inference import main as sadtalker_inference
        except ImportError:
            # Try alternative import paths
            try:
                from src.inference import main as sadtalker_inference
            except ImportError:
                raise ImportError("SadTalker inference module not found")

        # Build arguments
        class Args:
            driven_audio = audio_path
            source_image = face_image_path
            result_dir = str(Path(output_path).parent)
            checkpoint_dir = str(self.checkpoint_dir)
            device = self.device
            preprocess = self.preprocess
            still = self.still
            enhancer = self.enhancer
            background_enhancer = None
            cpu = self.device == "cpu"
            face3dvis = False
            expression_scale = 1.0
            input_yaw = None
            input_pitch = None
            input_roll = None
            ref_eyeblink = None
            ref_pose = None
            pose_style = 0
            batch_size = 2
            size = 256
            old_version = False

        args = Args()

        logger.info(f"Running SadTalker: audio={audio_path}, image={face_image_path}")
        result = sadtalker_inference(args)

        # Find output file
        if isinstance(result, str) and Path(result).exists():
            return result

        # Look for output in result directory
        result_dir = Path(output_path).parent
        for video_file in result_dir.glob("*.mp4"):
            return str(video_file)

        raise RuntimeError("SadTalker did not produce output")

    def _run_cli(
        self,
        audio_path: str,
        face_image_path: str,
        output_path: str,
    ) -> str:
        """Run SadTalker using CLI."""
        sadtalker_script = self.checkpoint_dir.parent / "inference.py"
        if not sadtalker_script.exists():
            raise FileNotFoundError(
                f"SadTalker inference.py not found. "
                f"Expected at: {sadtalker_script}"
            )

        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(sadtalker_script),
            "--driven_audio", audio_path,
            "--source_image", face_image_path,
            "--result_dir", str(output_dir),
            "--checkpoint_dir", str(self.checkpoint_dir),
            "--preprocess", self.preprocess,
        ]

        if self.still:
            cmd.append("--still")

        if self.enhancer:
            cmd.extend(["--enhancer", self.enhancer])

        if self.device == "cpu":
            cmd.append("--cpu")

        logger.info(f"Running SadTalker CLI: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.checkpoint_dir.parent),
        )

        if result.returncode != 0:
            logger.error(f"SadTalker stderr: {result.stderr}")
            raise RuntimeError(f"SadTalker failed: {result.stderr}")

        # Find output file
        for video_file in output_dir.glob("*.mp4"):
            return str(video_file)

        raise RuntimeError(f"SadTalker output not found in {output_dir}")

    async def close(self) -> None:
        """Clean up resources."""
        self._sadtalker = None
        self._initialized = False
