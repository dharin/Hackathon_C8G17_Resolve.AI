# Multi-Agent DevOps Incident Analysis Suite

An AI-powered, multi-agent platform that turns raw application logs into a fully investigated, actionable incident report — automatically detecting incidents, determining root cause, retrieving grounded remediation guidance from your own knowledge base, generating an executable runbook, and filing/notifying your team, end to end, with no hallucinated fixes.

Upload a log file and the platform's five-agent pipeline (orchestrated with **LangGraph**) takes it from raw text to resolution:

```
Log Reader → RCA → Remediation (RAG) → Cookbook → Notification (Jira + Slack)
```

Every recommendation the Remediation and Cookbook agents produce is grounded in retrieved evidence — Confluence pages and local SOP documents indexed into a vector store — never invented. If nothing relevant is found, the agents say so explicitly instead of guessing.

See [project-spec.md](project-spec.md) for the full specification and [tasks/](tasks/) for the phase-by-phase implementation plan.

## Table of Contents

- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [External Integrations](#external-integrations)
- [LLM Models](#llm-models)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Local Environment Setup](#local-environment-setup)
- [Running the Frontend](#running-the-frontend)
- [Running the Backend](#running-the-backend)
- [Running Backend Tests](#running-backend-tests)
- [Current Status](#current-status)

## Key Features

- **Automatic incident detection** — deterministic, regex-based classification across 7 incident categories (OOM kills, disk exhaustion, auth failures, timeouts, DB connection errors, HTTP 5xx spikes, plus an honest "unknown" bucket), with an optional LLM fallback for anomalies no rule matches. Severity is escalated automatically for repeated occurrences of the same issue.
- **Explainable root cause analysis** — every RCA is grounded strictly in the incident's own log evidence; a deterministic heuristic path is always available offline, with an optional LLM path that's rejected and silently falls back if it isn't fully grounded in the actual log lines or reads like a fix suggestion.
- **Zero-hallucination remediation via RAG** — recommendations are retrieved from your real Confluence spaces and local SOP files, never generated from nothing. No supporting documentation → an honest "no supporting documentation found," not an invented fix.
- **Executable, traceable cookbooks** — commands, validation steps, and rollback steps are extracted verbatim from the same retrieved sources backing each recommendation, so every runbook step traces back to a real document.
- **Automated Jira + Slack for critical incidents** — a Jira ticket is filed automatically for critical-severity incidents, and a Slack notification always fires only after that ticket exists (never before or independently). Non-critical incidents get a manual "Create Jira Ticket" button instead. Both are idempotent — revisiting an incident never creates duplicates.
- **Self-service knowledge base sync** — a "RAG Configuration" tab lets you re-index Confluence and local SOPs on demand, showing the last successful sync date and rolling back to it if a sync run fails partway.
- **Clerk-backed auth** with a mockable provider for local development without a real Clerk instance.

## Architecture

```
                     ┌────────────────────────┐
   Log file  ──────► │   Log Reader Agent      │  incident detection
                     └───────────┬─────────────┘
                                 ▼
                     ┌────────────────────────┐
                     │   RCA Agent             │  root cause, never a fix
                     └───────────┬─────────────┘
                                 ▼
                     ┌────────────────────────┐        ┌─────────────────────┐
                     │   Remediation Agent     │ ◄────► │  RAG (LanceDB)      │
                     │   (RAG-grounded)        │        │  Confluence + SOPs  │
                     └───────────┬─────────────┘        └─────────────────────┘
                                 ▼
                     ┌────────────────────────┐
                     │   Cookbook Agent        │  commands, validation, rollback
                     └───────────┬─────────────┘
                                 ▼
                     ┌────────────────────────┐
                     │  Critical?              │
                     └───┬────────────────┬────┘
                        Yes               No
                         ▼                 ▼
                 Jira ──► Slack     Manual "Create Jira Ticket" button
```

Orchestration is a **LangGraph** state graph (`backend/graph/`): one graph runs Upload → Incidents once per uploaded log; a second graph runs RCA → Remediation → Cookbook once per selected incident, with Jira/Slack layered on top as a critical-only, Jira-then-Slack side effect.

## Tech Stack

### Frontend

| Purpose | Choice |
|---|---|
| Framework | [Next.js 16](https://nextjs.org/) (App Router, Turbopack) |
| UI | React 19, Tailwind CSS v4, [shadcn/ui](https://ui.shadcn.com/) on [Base UI](https://base-ui.com/) primitives |
| Auth | [Clerk](https://clerk.com/) (`@clerk/nextjs`) |
| Icons | [lucide-react](https://lucide.dev/) |
| Language | TypeScript |

### Backend

| Purpose | Choice |
|---|---|
| API framework | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) |
| Agent orchestration | [LangGraph](https://langchain-ai.github.io/langgraph/) |
| Data validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Vector database | [LanceDB](https://lancedb.com/) (embedded, no separate service to run) |
| Embeddings | [FastEmbed](https://qdrant.github.io/fastembed/) — ONNX runtime, no GPU/torch dependency |
| LLM access | [OpenAI Python SDK](https://github.com/openai/openai-python) pointed at [OpenRouter](https://openrouter.ai/) |
| Document parsing | `pypdf`, `python-docx`, `beautifulsoup4` + `lxml` (Confluence storage-format XHTML) |
| Tokenization | `tiktoken` (chunk sizing, not tied to the embedding model) |
| Persistence | SQLite (analyses, sync state, Jira/Slack idempotency stores — no external DB required) |
| Auth verification | `pyjwt[crypto]` against Clerk's JWKS |
| Testing | `pytest` — 165+ tests, fully offline/mocked, no real credentials required |

## External Integrations

| Integration | Used for | Required? |
|---|---|---|
| **Clerk** | User authentication (sign-in/sign-out, session verification) | Optional locally — `AUTH_PROVIDER=mock` bypasses it entirely |
| **OpenRouter** | Optional LLM calls for anomaly classification, RCA drafting, and remediation-text drafting | Optional — every LLM path has a deterministic, offline fallback |
| **Confluence Cloud** | RAG knowledge source — indexes pages via the REST API (never MCP, for deterministic sync) | Optional — local SOPs alone are enough to run the RAG pipeline |
| **Jira Cloud** | Automatic ticket creation for critical incidents; manual creation for non-critical | Optional — the app runs fully without it, just skips ticket creation |
| **Slack** | Notification after a critical incident's Jira ticket is created | Optional — same graceful skip behavior |
| **Hugging Face Hub** | Anonymous or token-authenticated download of the embedding model's ONNX weights | Optional — `HF_TOKEN` just avoids anonymous rate limits |

Every integration above is designed to **degrade gracefully**: if it isn't configured, the relevant feature is skipped (and clearly reported as such in the UI), never treated as a fatal error.

## LLM Models

LLM access is routed entirely through **[OpenRouter](https://openrouter.ai/keys)**, using the OpenAI-compatible Chat Completions API — this means any model OpenRouter hosts can be dropped in via a single environment variable, with no code changes.

```env
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4.1-mini   # default
```

**Where the LLM is actually used** — always as an optional enhancement layered over a deterministic fallback, never a hard dependency:

- `services/log_reader/llm_classifier.py` — classifies a log line only when no deterministic rule matched it
- `agents/rca.py` — drafts a more specific root-cause narrative, validated against the incident's own log evidence before being trusted
- `agents/remediation.py` — drafts a recommendation's title/rationale from one retrieved document chunk, never introducing a source that wasn't actually retrieved

If `OPENROUTER_API_KEY` is unset, every one of these paths falls back to a deterministic, fully offline heuristic — the app runs completely functionally with **zero LLM calls and zero cost**.

### Free LLM models on OpenRouter

If you want the LLM-enhanced paths active without a paid plan, OpenRouter publishes a rotating set of `:free`-suffixed models — same API, no charge, generally at lower rate limits than paid tiers. A few that are commonly available at the time of writing:

- `meta-llama/llama-3.1-8b-instruct:free`
- `mistralai/mistral-7b-instruct:free`
- `google/gemini-2.0-flash-exp:free`
- `qwen/qwen-2.5-7b-instruct:free`

Availability and exact model IDs change over time — check **[openrouter.ai/models?max_price=0](https://openrouter.ai/models?max_price=0)** for the current live list before picking one, and set it as `OPENROUTER_MODEL` in `.env`.

## Project Structure

```
frontend/   Next.js 16 app (dashboard UI)
backend/    FastAPI app (agents, RAG, integrations)
docs/       Architecture and supporting docs
tasks/      Phase-by-phase implementation tasks
```

## Prerequisites

- Node.js 20+ (Next.js 16 / Tailwind v4 / shadcn require it — use `nvm use` in `frontend/`, an `.nvmrc` pinning Node 22 is provided)
- Python 3.11+
- npm

## Local Environment Setup

None of these are committed to git (see `.gitignore`) — every fresh clone needs to recreate them locally before either app will run.

### 1. Environment variables

```
cp .env.example .env
```

Creates the git-ignored root `.env` file. Fill in real values locally; never commit it.

To run the frontend with real Clerk auth, set `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, and `CLERK_JWKS_URL` from a Clerk dashboard (Configure → API Keys). Without them, the frontend's sign-in page will error. To run the **backend** without a Clerk instance, set `AUTH_PROVIDER=mock` — every request with any bearer token then resolves to a fixed local dev identity.

`NEXT_PUBLIC_API_BASE_URL` points the frontend at the backend (defaults to `http://localhost:8000`). `MAX_UPLOAD_SIZE_MB` / `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB` cap log upload size and must be kept in sync — the backend value is the source of truth, the frontend value is just for immediate client-side feedback.

### 2. Frontend dependencies

```
cd frontend
nvm use              # picks up .nvmrc (Node 22)
npm install
```

Creates the git-ignored `frontend/node_modules/` directory. `npm run dev` will also generate a git-ignored `frontend/.next/` build cache on first run.

### 3. Backend virtual environment

```
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Creates the git-ignored `backend/.venv/` directory with all Python dependencies installed inside it.

Once both are set up, run each app as below (repeat step 3's `source backend/.venv/bin/activate` in any new terminal before running the backend).

## Running the Frontend

```
cd frontend
nvm use 22.x
npm run dev
```

Frontend runs at http://localhost:3000.

## Running the Backend

```
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

Backend runs at http://localhost:8000. Health check: `GET http://localhost:8000/health` → `{"status": "ok"}`.

Authenticated identity check (requires a bearer token — a real Clerk session token, or any non-empty string when `AUTH_PROVIDER=mock`):

```
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/me
```

Log upload (same auth requirement):

```
curl -H "Authorization: Bearer <token>" -F "file=@/path/to/app.log" http://localhost:8000/api/v1/logs/upload
```

Analyze an uploaded log and fetch its incidents:

```
curl -X POST -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/logs/<upload_id>/analyze
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/analyses/<analysis_id>/incidents
```

## Running Backend Tests

```
cd backend
source .venv/bin/activate
pytest
```

Fully offline and deterministic — `backend/tests/conftest.py` forces `AUTH_PROVIDER=mock` and blanks `OPENROUTER_API_KEY`/Jira/Slack credentials regardless of your local `.env`, so no real Clerk, OpenRouter, Confluence, Jira, or Slack credentials are ever used or contacted during a test run.

## Current Status

Phases 1–11 complete — the full pipeline runs end to end, wired into the real dashboard UI:

- **Phase 1–2** — project bootstrap; Clerk-backed auth (sign-in/sign-out, route protection) with a mockable backend auth provider.
- **Phase 3–4** — dashboard shell (sidebar, workflow stepper, incident list/details) and log upload (`POST /api/v1/logs/upload`), now driven by real backend data end to end rather than mock fixtures.
- **Phase 5** — Log Reader Agent: deterministic (regex-first, LLM-fallback) detection across 7 incident categories.
- **Phase 6** — RAG pipeline: Confluence + local-SOP loaders, structure-aware chunking, LanceDB indexing, incremental sync, source-attributed retrieval. Auto-builds the index on first backend startup if empty; a "RAG Configuration" tab lets you re-sync on demand.
- **Phase 7** — RCA Agent: heuristic-by-default, LLM-enhanced-when-grounded root cause analysis, never a fix.
- **Phase 8** — Remediation Agent: RAG-grounded recommendations, zero hallucination, builds the Jira payload.
- **Phase 9** — Cookbook Agent: commands/validation/rollback extracted verbatim from the same sources backing each recommendation.
- **Phase 10** — Jira integration: automatic for critical incidents, manual button for non-critical, idempotent.
- **Phase 11** — Slack integration: automatic notification after a critical incident's Jira ticket exists, never before or independently.

Orchestration runs on a real **LangGraph** state graph (`backend/graph/`), and the full agent chain — Log Reader → RCA → Remediation → Cookbook → Jira → Slack — is exercised by 165+ automated backend tests.

See [tasks/](tasks/) for the phase-by-phase plan.
