#!/usr/bin/env python3
"""AI Sales Agent - Interactive Startup Script

This script helps you choose between:
1. API Mode (MiniMax cloud) - Quick start, no GPU needed
2. Self-Hosted Mode (OSS) - Full privacy, requires GPU

Models are cached locally in ./models/ to avoid re-downloading.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Optional

# Directories
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
VOICES_DIR = BASE_DIR / "voices"
VENV_DIR = BASE_DIR / "venv"
ENV_FILE = BASE_DIR / ".env"

# Model paths
XTTS_MODEL_DIR = MODELS_DIR / "xtts_v2"
SADTALKER_DIR = MODELS_DIR / "sadtalker"
LLAMA_MODEL = "meta-llama/Llama-3.1-70B-Instruct"

# Colors for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_info(text: str):
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def run_command(cmd: list, check: bool = True, capture: bool = False) -> Optional[str]:
    """Run a command and optionally capture output."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            cwd=str(BASE_DIR)
        )
        if capture:
            return result.stdout
        return None
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {' '.join(cmd)}")
        if e.stderr:
            print(e.stderr)
        return None


def check_gpu() -> bool:
    """Check if NVIDIA GPU is available."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            gpus = result.stdout.strip().split('\n')
            print_info(f"Found {len(gpus)} GPU(s):")
            for gpu in gpus:
                print(f"    {gpu}")
            return True
    except FileNotFoundError:
        pass
    return False


def check_vram() -> int:
    """Get total VRAM in GB."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            lines = [x.strip() for x in result.stdout.strip().split('\n') if x.strip()]
            total = 0
            for line in lines:
                try:
                    total += int(line)
                except ValueError:
                    # Handle [N/A] or other non-numeric values (DGX SPARK unified memory)
                    pass
            if total > 0:
                return total // 1024  # Convert MB to GB

        # Fallback: check for unified memory systems (Grace Hopper)
        result = subprocess.run(
            ["nvidia-smi", "-q", "-d", "MEMORY"],
            capture_output=True,
            text=True
        )
        if "Total" in result.stdout:
            for line in result.stdout.split('\n'):
                if "Total" in line and "MiB" in line:
                    try:
                        mem = int(line.split(':')[1].strip().split()[0])
                        return mem // 1024
                    except:
                        pass
    except:
        pass

    # Default for DGX SPARK with unified memory (128GB accessible)
    return 128


def get_python_version() -> tuple:
    """Get Python major.minor version."""
    return (sys.version_info.major, sys.version_info.minor)


def get_architecture() -> str:
    """Get system architecture."""
    import platform
    return platform.machine()


def update_env(mode: str):
    """Update .env file with provider configuration."""
    # Always use coqui for TTS (runs in Docker container)
    # Edge-tts as fallback (no voice cloning but works everywhere)
    tts_provider = "coqui"
    tts_fallback = "coqui,edge,minimax"

    if mode == "api":
        config = """# =============================================================================
# API MODE - Using MiniMax Cloud
# =============================================================================
PROVIDER_TEXT=minimax
PROVIDER_TTS=minimax
PROVIDER_VIDEO=minimax

# Fallback chains
PROVIDER_TEXT_FALLBACK=minimax
PROVIDER_TTS_FALLBACK=minimax
PROVIDER_VIDEO_FALLBACK=minimax
"""
    else:
        config = f"""# =============================================================================
# SELF-HOSTED MODE - Using Local OSS Models
# =============================================================================
PROVIDER_TEXT=vllm
PROVIDER_TTS={tts_provider}
PROVIDER_VIDEO=sadtalker

# Fallback to API if local fails
PROVIDER_TEXT_FALLBACK=vllm,minimax
PROVIDER_TTS_FALLBACK={tts_fallback}
PROVIDER_VIDEO_FALLBACK=sadtalker,minimax

# vLLM Configuration
PROVIDER_VLLM_BASE_URL=http://localhost:8000
PROVIDER_VLLM_MODEL=meta-llama/Llama-3.1-70B-Instruct

# Coqui XTTS Configuration (Docker microservice)
PROVIDER_COQUI_MODE=service
PROVIDER_COQUI_SERVICE_URL=http://localhost:5050
PROVIDER_COQUI_VOICES_DIR=./voices

# SadTalker Configuration
PROVIDER_SADTALKER_CHECKPOINT=./models/sadtalker
PROVIDER_SADTALKER_DEVICE=cuda
PROVIDER_SADTALKER_PREPROCESS=crop
"""

    # Read existing env to preserve API keys
    existing_keys = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                if key in ['MINIMAX_API_KEY', 'MINIMAX_GROUP_ID', 'MINIMAX_BASE_URL']:
                    existing_keys[key] = value

    # Add preserved keys
    if existing_keys:
        config += "\n# MiniMax API (preserved)\n"
        for key, value in existing_keys.items():
            config += f"{key}={value}\n"

    config += "\n# Pipeline\nENABLE_PERSONALIZED_PIPELINE=true\n"

    ENV_FILE.write_text(config)
    print_success(f"Updated {ENV_FILE}")


def install_base_deps():
    """Install base dependencies."""
    print_info("Installing base dependencies...")

    # Activate venv and install
    pip = VENV_DIR / "bin" / "pip"
    if not pip.exists():
        print_error("Virtual environment not found. Run: python -m venv venv")
        return False

    run_command([str(pip), "install", "-q", "-r", "requirements.txt"])
    print_success("Base dependencies installed")
    return True


def install_oss_deps():
    """Install OSS model dependencies."""
    pip = VENV_DIR / "bin" / "pip"
    python = VENV_DIR / "bin" / "python"

    py_version = get_python_version()
    arch = get_architecture()

    print_info("Installing OSS dependencies...")
    print_info(f"  Python: {py_version[0]}.{py_version[1]}, Arch: {arch}")

    # Check Python version compatibility
    if py_version >= (3, 12):
        print_warning(f"Python {py_version[0]}.{py_version[1]} detected!")
        print_warning("Coqui TTS requires Python 3.9-3.11")
        print_info("Options:")
        print("    1. Use API mode (MiniMax) for TTS")
        print("    2. Create a Python 3.11 venv: python3.11 -m venv venv311")
        print("    3. Use alternative TTS (edge-tts, pyttsx3)")

    # Install PyTorch based on architecture
    print_info("  Installing PyTorch...")
    if arch == "aarch64":
        # ARM64 (DGX SPARK, Jetson, etc.) - use pip default or NGC container
        print_info("    ARM64 detected - using PyTorch from PyPI")
        result = run_command([
            str(pip), "install", "-q", "torch", "torchaudio"
        ], check=False)

        # If that fails, try NVIDIA's PyTorch for Jetson/ARM
        if result is None:
            print_info("    Trying NVIDIA PyTorch wheel...")
            run_command([
                str(pip), "install", "-q",
                "--extra-index-url", "https://pypi.nvidia.com",
                "torch"
            ], check=False)
    else:
        # x86_64 - use CUDA wheels
        run_command([
            str(pip), "install", "-q",
            "torch>=2.2.0", "torchaudio>=2.2.0",
            "--index-url", "https://download.pytorch.org/whl/cu121"
        ], check=False)

    # Check if PyTorch installed successfully
    torch_check = run_command([
        str(python), "-c", "import torch; print(f'PyTorch {torch.__version__}')"
    ], check=False, capture=True)

    if torch_check:
        print_success(f"  {torch_check.strip()}")
    else:
        print_warning("  PyTorch installation failed - TTS/Video may not work")

    # Coqui TTS runs in Docker container, no need to install locally
    print_info("  Coqui XTTS will run in Docker (Python 3.11 container)")
    print_info("  Installing edge-tts as backup...")
    run_command([str(pip), "install", "-q", "edge-tts"], check=False)

    # Audio processing
    run_command([str(pip), "install", "-q", "pydub", "scipy"], check=False)

    print_success("OSS dependencies installation complete")
    return True


def check_docker() -> bool:
    """Check if Docker is available."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_xtts_service() -> bool:
    """Check if XTTS service is running."""
    try:
        import httpx
        response = httpx.get("http://localhost:5050/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_xtts_service():
    """Start XTTS Docker service."""
    print_info("Setting up XTTS voice cloning service (Docker)...")

    if not check_docker():
        print_error("Docker not found!")
        print_info("Install Docker: https://docs.docker.com/get-docker/")
        return False

    if check_xtts_service():
        print_success("XTTS service already running")
        return True

    # Check if docker-compose.yml exists
    compose_file = BASE_DIR / "docker-compose.yml"
    if not compose_file.exists():
        print_error(f"docker-compose.yml not found at {compose_file}")
        return False

    print_info("Building and starting XTTS container (first run downloads ~6GB)...")
    print_info("This may take several minutes...")

    # Build and start
    result = subprocess.run(
        ["docker-compose", "up", "-d", "--build", "xtts"],
        cwd=str(BASE_DIR),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        # Try docker compose (v2) instead of docker-compose
        result = subprocess.run(
            ["docker", "compose", "up", "-d", "--build", "xtts"],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True
        )

    if result.returncode != 0:
        print_error("Failed to start XTTS service")
        print(result.stderr)
        return False

    # Wait for service to be ready
    print_info("Waiting for XTTS service to initialize...")
    import time
    for i in range(60):  # Wait up to 5 minutes
        time.sleep(5)
        if check_xtts_service():
            print_success("XTTS service started!")
            return True
        print(f"    Still initializing... ({(i+1)*5}s)")

    print_warning("XTTS service may still be loading models")
    print_info("Check status with: docker-compose logs xtts")
    return True


def download_xtts_model():
    """Download XTTS v2 model - now handled by Docker service."""
    # With Docker service, the model is downloaded inside the container
    # and persisted via Docker volume
    print_info("XTTS model will be downloaded by Docker service on first use")
    return True


def setup_sadtalker():
    """Setup SadTalker if not present."""
    print_info("Checking SadTalker...")

    SADTALKER_DIR.mkdir(parents=True, exist_ok=True)

    checkpoints_dir = SADTALKER_DIR / "checkpoints"

    if checkpoints_dir.exists() and list(checkpoints_dir.glob("*.pth")):
        print_success("SadTalker checkpoints found")
        return True

    print_warning("SadTalker checkpoints not found")
    print_info("To enable video generation, download checkpoints from:")
    print(f"    https://github.com/OpenTalker/SadTalker#-2-download-trained-models")
    print(f"    Place them in: {SADTALKER_DIR}")

    return False


def check_vllm_server() -> bool:
    """Check if vLLM server is running."""
    try:
        import httpx
        response = httpx.get("http://localhost:8000/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def start_vllm_server():
    """Start vLLM server in background."""
    if check_vllm_server():
        print_success("vLLM server already running")
        return True

    vram = check_vram()
    if vram < 40:
        print_warning(f"vLLM requires ~40GB VRAM for Llama 70B (found {vram}GB)")
        print_info("Consider using a smaller model or API mode")

        # Ask user
        choice = input(f"\n{Colors.YELLOW}Try to start anyway? [y/N]: {Colors.END}").strip().lower()
        if choice != 'y':
            return False

    print_info("Starting vLLM server (this may take a few minutes)...")
    print_info(f"Model: {LLAMA_MODEL}")

    python = VENV_DIR / "bin" / "python"

    # Check if vllm is installed
    result = run_command([str(python), "-c", "import vllm"], check=False, capture=True)
    if result is None:
        print_info("Installing vLLM...")
        pip = VENV_DIR / "bin" / "pip"
        run_command([str(pip), "install", "vllm>=0.4.0"], check=False)

    # Start vLLM in background
    log_file = BASE_DIR / "vllm.log"

    cmd = [
        str(python), "-m", "vllm.entrypoints.openai.api_server",
        "--model", LLAMA_MODEL,
        "--host", "0.0.0.0",
        "--port", "8000",
    ]

    # Add tensor parallelism for multi-GPU
    try:
        result = subprocess.run(
            ["nvidia-smi", "-L"],
            capture_output=True,
            text=True
        )
        gpu_count = len(result.stdout.strip().split('\n'))
        if gpu_count > 1:
            cmd.extend(["--tensor-parallel-size", str(gpu_count)])
            print_info(f"Using {gpu_count} GPUs with tensor parallelism")
    except:
        pass

    print_info(f"vLLM log: {log_file}")

    with open(log_file, 'w') as f:
        subprocess.Popen(
            cmd,
            stdout=f,
            stderr=subprocess.STDOUT,
            start_new_session=True
        )

    print_info("Waiting for vLLM to start (checking every 10s)...")

    import time
    for i in range(30):  # Wait up to 5 minutes
        time.sleep(10)
        if check_vllm_server():
            print_success("vLLM server started!")
            return True
        print(f"    Still loading... ({(i+1)*10}s)")

    print_error("vLLM server failed to start. Check vllm.log")
    return False


def start_api_server():
    """Start the FastAPI server."""
    print_header("Starting AI Sales Agent")

    python = VENV_DIR / "bin" / "python"

    print_info("Server starting at http://localhost:8001")
    print_info("API docs at http://localhost:8001/docs")
    print_info("Press Ctrl+C to stop\n")

    os.execv(
        str(python),
        [str(python), "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
    )


def main():
    print_header("AI Sales Agent Setup")

    # Create directories
    MODELS_DIR.mkdir(exist_ok=True)
    VOICES_DIR.mkdir(exist_ok=True)

    # Check for venv
    if not VENV_DIR.exists():
        print_error("Virtual environment not found!")
        print_info("Create it with: python -m venv venv")
        sys.exit(1)

    # Menu
    print(f"{Colors.BOLD}Choose your mode:{Colors.END}\n")
    print(f"  {Colors.CYAN}1){Colors.END} API Mode (MiniMax Cloud)")
    print(f"     - Quick start, no GPU needed")
    print(f"     - Requires MINIMAX_API_KEY\n")

    print(f"  {Colors.CYAN}2){Colors.END} Self-Hosted Mode (OSS)")
    print(f"     - Llama 3.1 70B + XTTS v2 + SadTalker")
    print(f"     - Requires ~54GB VRAM")
    print(f"     - Models cached in ./models/\n")

    print(f"  {Colors.CYAN}3){Colors.END} Hybrid Mode")
    print(f"     - Self-hosted with API fallback\n")

    # Check GPU
    has_gpu = check_gpu()
    vram = check_vram()

    if has_gpu:
        if vram > 0 and vram < 1000:  # Valid VRAM reading
            print(f"\n{Colors.GREEN}GPU detected: {vram}GB VRAM{Colors.END}")
            if vram >= 54:
                print(f"{Colors.GREEN}Sufficient for full self-hosted mode{Colors.END}")
            elif vram >= 8:
                print(f"{Colors.YELLOW}Can run TTS + Video, but not Llama 70B{Colors.END}")
        else:
            # Unified memory system (DGX SPARK / Grace Hopper)
            print(f"\n{Colors.GREEN}GPU detected (unified memory architecture){Colors.END}")
            print(f"{Colors.GREEN}DGX SPARK detected - sufficient for all models{Colors.END}")
            vram = 128  # Assume 128GB for DGX SPARK
    else:
        print(f"\n{Colors.YELLOW}No GPU detected - API mode recommended{Colors.END}")

    # Get choice
    while True:
        choice = input(f"\n{Colors.BOLD}Select mode [1/2/3]: {Colors.END}").strip()
        if choice in ['1', '2', '3']:
            break
        print_error("Invalid choice. Enter 1, 2, or 3.")

    # Install base deps
    if not install_base_deps():
        sys.exit(1)

    if choice == '1':
        # API Mode
        print_header("API Mode Setup")
        update_env("api")

        # Check for API key
        if not os.getenv("MINIMAX_API_KEY"):
            env_content = ENV_FILE.read_text() if ENV_FILE.exists() else ""
            if "MINIMAX_API_KEY=" not in env_content or "your-api-key" in env_content:
                print_warning("MINIMAX_API_KEY not configured!")
                print_info("Get your API key from: https://www.minimax.io/")
                api_key = input(f"{Colors.CYAN}Enter API key (or press Enter to skip): {Colors.END}").strip()
                if api_key:
                    content = ENV_FILE.read_text()
                    content += f"\nMINIMAX_API_KEY={api_key}\n"
                    ENV_FILE.write_text(content)
                    print_success("API key saved")

        start_api_server()

    elif choice == '2':
        # Self-Hosted Mode
        print_header("Self-Hosted Mode Setup")
        update_env("oss")

        if not has_gpu:
            print_error("Self-hosted mode requires a GPU!")
            sys.exit(1)

        # Install OSS deps
        install_oss_deps()

        # Start XTTS Docker service (voice cloning)
        if not start_xtts_service():
            print_warning("XTTS service failed - voice cloning will use API fallback")

        # Setup SadTalker
        setup_sadtalker()

        # Start vLLM
        if not start_vllm_server():
            print_warning("Continuing without vLLM - text generation will use fallback")

        start_api_server()

    else:
        # Hybrid Mode
        print_header("Hybrid Mode Setup")
        update_env("oss")  # Same as OSS but with fallbacks

        # Install OSS deps if GPU available
        if has_gpu:
            install_oss_deps()

            # Start XTTS Docker service
            start_xtts = input(f"\n{Colors.CYAN}Start XTTS voice cloning service (Docker)? [Y/n]: {Colors.END}").strip().lower()
            if start_xtts != 'n':
                start_xtts_service()

            setup_sadtalker()

            # Optionally start vLLM
            if vram >= 40:
                start_vllm = input(f"\n{Colors.CYAN}Start vLLM server? [y/N]: {Colors.END}").strip().lower()
                if start_vllm == 'y':
                    start_vllm_server()

        start_api_server()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Cancelled{Colors.END}")
        sys.exit(0)
