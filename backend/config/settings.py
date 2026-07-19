from pathlib import Path

from dotenv import load_dotenv

# Repo root .env, shared by frontend and backend (see project-spec.md).
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
