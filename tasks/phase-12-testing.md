# Phase 12 — Testing

## Objective
Validate the end-to-end workflow across frontend, backend, AI agents, and integrations.

## Scope
- Frontend component tests.
- Backend API tests.
- AI prompt validation (RCA/Remediation/Cookbook agents produce well-formed, grounded output).
- Integration tests for Jira, Slack, Confluence (mocked where live credentials are unavailable).

## Dependencies
- Phases 1–11 (entire feature set must exist to test end-to-end).

## Implementation Tasks
- Frontend: component tests for `IncidentList`, `Tabs` (RCA/Recommendations/Cookbook), `FooterActions` (Jira/Slack triggers).
- Backend: API tests for `/upload-log`, `/incidents`, `/incidents/{id}`, `/create-jira`, `/notify-slack`.
- AI: golden-output/prompt tests asserting RCA never contains remediation, Remediation never fabricates sources, Cookbook steps trace to remediation.
- Integration: mocked Jira/Slack/Confluence clients exercised in CI-style tests; document what's mocked vs. live.
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
