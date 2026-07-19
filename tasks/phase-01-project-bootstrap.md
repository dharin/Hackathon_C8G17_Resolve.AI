# Phase 1 — Project Bootstrap

## Objective
Establish the repository skeleton and base architecture for both frontend and backend so the application runs locally end-to-end (empty shell).

## Scope
- Initialize Next.js 15 frontend with Tailwind CSS and shadcn/ui.
- Initialize FastAPI backend with a minimal health-check endpoint.
- Establish the shared top-level project structure (`frontend/`, `backend/`, `docs/`, `tasks/`, `.env`).
- No auth, no agents, no UI features yet — placeholder pages/routes only.

## Dependencies
None (first phase).

## Implementation Tasks
- `frontend/`: `create-next-app` (App Router, TypeScript, Tailwind), install and configure shadcn/ui.
- `frontend/`: add base folders — `app/`, `components/`, `features/`, `hooks/`, `lib/`, `services/`, `types/`.
- `backend/`: FastAPI app with `api/`, `agents/`, `graph/`, `rag/`, `integrations/`, `models/`, `services/`, `config/` package structure (empty `__init__.py` placeholders where needed).
- `backend/`: `GET /health` endpoint returning `{status: "ok"}`.
- Root `.env.example` listing all environment variables from project-spec.md (no real values).
- `README.md` with local run instructions for both apps.

## Deliverables
- Frontend scaffold that runs with `npm run dev`.
- Backend scaffold that runs with `uvicorn` and serves `/health`.
- Shared project structure matching project-spec.md's "Detailed Folder Structure".

## Acceptance Criteria
- Application runs locally (frontend and backend both start without errors).

## Definition of Done
- Frontend and backend start successfully.
- `/health` returns 200.
- No secrets committed; `.env` is git-ignored, `.env.example` is committed.

## Suggested Git Commit
`feat: bootstrap project structure`
