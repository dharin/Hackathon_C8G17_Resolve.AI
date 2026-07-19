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

# --- RAG: Confluence Cloud (see project-spec.md "RAG Design") ---
CONFLUENCE_SITE_URL = os.environ.get("CONFLUENCE_SITE_URL", "")
CONFLUENCE_EMAIL = os.environ.get("CONFLUENCE_EMAIL", "")
CONFLUENCE_API_TOKEN = os.environ.get("CONFLUENCE_API_TOKEN", "")
CONFLUENCE_CLOUD_ID = os.environ.get("CONFLUENCE_CLOUD_ID", "")
CONFLUENCE_INCLUDED_SPACE_KEYS = [
    key.strip() for key in os.environ.get("CONFLUENCE_INCLUDED_SPACE_KEYS", "").split(",") if key.strip()
]
CONFLUENCE_PAGE_LIMIT = int(os.environ.get("CONFLUENCE_PAGE_LIMIT", "100"))
CONFLUENCE_SYNC_CONCURRENCY = int(os.environ.get("CONFLUENCE_SYNC_CONCURRENCY", "3"))

# --- RAG: Local SOP directory ---
LOCAL_SOP_DIRECTORY = Path(os.environ.get("LOCAL_SOP_DIRECTORY", str(BACKEND_ROOT / "data" / "sops")))
LOCAL_SOP_ALLOWED_EXTENSIONS = {
    ext.strip().lower()
    for ext in os.environ.get("LOCAL_SOP_ALLOWED_EXTENSIONS", ".md,.txt,.pdf,.docx").split(",")
    if ext.strip()
}
LOCAL_SOP_RECURSIVE = os.environ.get("LOCAL_SOP_RECURSIVE", "true").lower() == "true"

# --- RAG: chunking, embedding, and storage ---
RAG_EMBEDDING_MODEL = os.environ.get("RAG_EMBEDDING_MODEL", "BAAI/bge-small-en")
RAG_CHUNK_TARGET_TOKENS = int(os.environ.get("RAG_CHUNK_TARGET_TOKENS", "650"))
RAG_CHUNK_MAX_TOKENS = int(os.environ.get("RAG_CHUNK_MAX_TOKENS", "900"))
RAG_CHUNK_OVERLAP_TOKENS = int(os.environ.get("RAG_CHUNK_OVERLAP_TOKENS", "100"))
RAG_MIN_CHUNK_TOKENS = int(os.environ.get("RAG_MIN_CHUNK_TOKENS", "100"))
RAG_SYNC_SCHEDULE = os.environ.get("RAG_SYNC_SCHEDULE", "manual")
LANCEDB_PATH = Path(os.environ.get("LANCEDB_PATH", str(BACKEND_ROOT / "data" / "lancedb")))
RAG_SYNC_STATE_DB_PATH = Path(
    os.environ.get("RAG_SYNC_STATE_DB_PATH", str(BACKEND_ROOT / "data" / "rag_sync_state.sqlite3"))
)
