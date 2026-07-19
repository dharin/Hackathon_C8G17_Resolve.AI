import os
import threading
from contextlib import asynccontextmanager

import config.settings  # noqa: F401  (loads .env before anything reads os.environ)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.analyze import router as analyze_router
from api.jira import router as jira_router
from api.me import router as me_router
from api.rag import router as rag_router
from api.slack import router as slack_router
from api.upload import router as upload_router
from rag.pipeline import ensure_index_ready


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Non-blocking: the server starts accepting requests immediately.
    # /rag/retrieve just returns fewer/no results until this finishes if
    # the index was empty (see rag/pipeline.py::ensure_index_ready).
    # Skipped under pytest (PYTEST_CURRENT_TEST is set by pytest itself
    # during test runs) — the test suite is meant to stay fully offline
    # and deterministic, and this would otherwise download a real
    # embedding model / hit the live Confluence API from a background
    # thread on every TestClient(app) instantiation.
    if not os.environ.get("PYTEST_CURRENT_TEST"):
        threading.Thread(target=ensure_index_ready, daemon=True).start()
    yield


app = FastAPI(title="DevOps Incident Analysis Suite API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(me_router)
app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(rag_router)
app.include_router(jira_router)
app.include_router(slack_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
