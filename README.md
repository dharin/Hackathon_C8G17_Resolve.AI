# Multi-Agent DevOps Incident Analysis Suite

Hackathon build of an AI-powered DevOps incident analysis platform. See [project-spec.md](project-spec.md) for the full specification and [tasks/](tasks/) for the phase-by-phase implementation plan.

## Project Structure

```
frontend/   Next.js 15 app (dashboard UI)
backend/    FastAPI app (agents, RAG, integrations)
docs/       Architecture and supporting docs
tasks/      Phase-by-phase implementation tasks
```

## Prerequisites

- Node.js 20+ (Next.js 15 / Tailwind v4 / shadcn require it — use `nvm use` in `frontend/`, an `.nvmrc` pinning Node 22 is provided)
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
```

Creates the git-ignored `backend/.venv/` directory with all Python dependencies installed inside it.

Once both are set up, run each app as below (repeat step 3's `source backend/.venv/bin/activate` in any new terminal before running the backend).

## Running the Frontend

```
cd frontend
nvm use
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

## Current Status

Phase 1 (Project Bootstrap) and Phase 2 (Authentication) complete: Clerk-backed sign-in/sign-out and route protection on the frontend, a mockable auth-provider abstraction and authenticated `/api/v1/me` on the backend. See [tasks/phase-01-project-bootstrap.md](tasks/phase-01-project-bootstrap.md), [tasks/phase-02-authentication.md](tasks/phase-02-authentication.md), and subsequent phase files for what's next.
