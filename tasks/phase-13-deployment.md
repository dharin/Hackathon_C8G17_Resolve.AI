# Phase 13 — Deployment

## Objective
Deploy a hackathon-ready, demoable version of the solution.

## Scope
- Frontend deployment (Vercel).
- Backend deployment (Render or Railway).
- Vector DB stays local (LanceDB) — no managed vector DB for the hackathon.
- Environment configuration for deployed environments.
- Demo documentation.

## Dependencies
- Phases 1–12 (feature-complete and tested).

## Implementation Tasks
- Frontend: Vercel project config, environment variables set in Vercel dashboard (never committed).
- Backend: Render/Railway deploy config (`Procfile`/`render.yaml`/equivalent), environment variables set in provider dashboard.
- Verify LanceDB persistence strategy works within the chosen backend host's storage constraints (document limitation if ephemeral).
- Update `README.md` with deployed URLs (placeholders), setup steps, and a demo walkthrough script.
- Final smoke test against the deployed environment.

## Deliverables
- Live frontend and backend deployments.
- Demo documentation (`README.md` / `docs/`) describing how to run the live demo end-to-end.

## Acceptance Criteria
- Deployed frontend can reach the deployed backend and complete the full workflow for a sample log.

## Definition of Done
- Smoke test passes on the deployed environment; demo doc is accurate and complete.

## Suggested Git Commit
`chore: deploy hackathon release`
