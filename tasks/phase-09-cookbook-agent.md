# Phase 9 — Cookbook Agent

## Objective
Produce an executable runbook from the root cause and remediation recommendations.

## Scope
- Cookbook Agent outputs: Root Cause, Recommended Steps, Executable Commands, Validation, Rollback.
- Allow manual Jira ticket creation for non-critical incidents from this view (the button itself; wiring happens in Phase 10).

## Dependencies
- Phase 7 (RCA), Phase 8 (Remediation).

## Implementation Tasks
- `backend/agents/cookbook.py`: transform RCA + Recommendations into a structured runbook (commands, validation steps, rollback steps).
- `backend/models/cookbook.py`: `Cookbook` Pydantic model.
- Extend LangGraph: `Remediation` → `Cookbook` state transition.
- Extend `GET /incidents/{id}` to include the cookbook.
- Frontend: "Cookbook" tab rendering Root Cause, Recommended Steps, Commands, Validation, Rollback; "Create Jira Ticket" button shown only for non-critical incidents (disabled/no-op until Phase 10).

## Deliverables
- Full runbook displayed per incident.

## Acceptance Criteria
- Every command in the cookbook traces back to a remediation recommendation (no invented steps).
- Manual Jira button is visible only for non-critical severity.

## Definition of Done
- Cookbook tab renders complete runbook content for a selected incident.

## Suggested Git Commit
`feat: add cookbook analyzer`
