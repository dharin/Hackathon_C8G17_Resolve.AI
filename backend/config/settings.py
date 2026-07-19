import os
from pathlib import Path

from dotenv import load_dotenv

# Repo root .env, shared by frontend and backend (see project-spec.md).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

BACKEND_ROOT = REPO_ROOT / "backend"
UPLOAD_DIR = BACKEND_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_LOG_EXTENSIONS = {".log", ".txt"}
MAX_UPLOAD_SIZE_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024
