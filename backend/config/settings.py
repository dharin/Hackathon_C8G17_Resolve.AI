import os
from pathlib import Path

import certifi
from dotenv import load_dotenv

# Some Python installs (notably python.org's on macOS) don't wire up the
# system CA trust store, so stdlib-based HTTPS calls — e.g. PyJWT's
# PyJWKClient fetching Clerk's JWKS — fail with CERTIFICATE_VERIFY_FAILED.
# Pointing OpenSSL at certifi's bundle via this env var fixes it for the
# whole process, regardless of how Python was installed.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

# Repo root .env, shared by frontend and backend (see project-spec.md).
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(REPO_ROOT / ".env")

BACKEND_ROOT = REPO_ROOT / "backend"
UPLOAD_DIR = BACKEND_ROOT / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ANALYSES_DIR = BACKEND_ROOT / "analyses"
ANALYSES_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_LOG_EXTENSIONS = {".log", ".txt"}
MAX_UPLOAD_SIZE_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "10")) * 1024 * 1024

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or None
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openai/gpt-4.1-mini")
