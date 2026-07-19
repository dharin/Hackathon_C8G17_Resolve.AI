# Phase 12 — Testing

## Objective
Validate the end-to-end workflow across frontend, backend, AI agents, and integrations.

## Scope
- Frontend component tests.
- Backend API tests.
- AI prompt validation (RCA/Remediation/Cookbook agents produce well-formed, grounded output).
- Integration tests for Jira, Slack, Confluence, and the local SOP loader (mocked where live credentials are unavailable).

## Dependencies
- Phases 1–11 (entire feature set must exist to test end-to-end).

## Implementation Tasks
- Frontend: component tests for `IncidentList`, `Tabs` (RCA/Recommendations/Cookbook), `FooterActions` (Jira/Slack triggers).
- Backend: API tests for the actual implemented contract — `POST /api/v1/logs/upload`, `POST /api/v1/logs/{upload_id}/analyze`, `GET /api/v1/analyses/{analysis_id}/incidents`, `GET /api/v1/analyses/{analysis_id}/incidents/{incident_id}`, `POST /api/v1/rag/sync`, `GET /api/v1/rag/retrieve`, `/create-jira`, `/notify-slack`. (The original project-spec.md contract — flat `/upload-log`, `/incidents`, `/incidents/{id}` — was never implemented; Phase 5 diverged from it and Phase 7 documented why. Test against what's real.)
- Backend: graph tests for `backend/graph/orchestrator.py` — both `get_detection_graph()` and the full `get_incident_workflow_graph()` chain (`"rca" -> "remediation" -> "cookbook"`, assembled across Phases 7-9) end to end.
- AI: golden-output/prompt tests asserting RCA never contains remediation, Remediation never fabricates sources, Cookbook steps trace to remediation.
- Integration: mocked Jira/Slack/Confluence clients exercised in CI-style tests (Confluence loader tests already exist from Phase 6, see `backend/tests/test_rag_confluence_loader.py`); document what's mocked vs. live.
- End-to-end manual test script: upload sample log → walk through full workflow → verify critical vs non-critical branching.

## Deliverables
- Test suites for frontend and backend.
- A documented manual E2E test script for demo verification.

## Acceptance Criteria
- All automated tests pass locally.
- Manual E2E script completes without errors for both a critical and a non-critical incident.

## Definition of Done
- Test results documented; known gaps (if any) listed under Known Limitations.

## Suggested Git Commit
`test: end-to-end validation`
