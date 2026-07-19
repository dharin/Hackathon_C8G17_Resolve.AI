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
- In `backend/graph/orchestrator.py::get_incident_workflow_graph()`, add a `"cookbook"` node between `"remediation"` (added in Phase 8) and `END`. Update `IncidentWorkflowState.cookbook` in `graph/state.py` from `dict[str, Any] | None` to `Cookbook | None`.
- In `models/incident_detail.py`, change `IncidentDetail.cookbook` from `dict[str, Any] | None` to `Cookbook | None`, and populate it in `api/analyze.py::get_incident_detail`. (Note: `GET /incidents/{id}` from the original project-spec.md contract was never implemented — Phase 5 shipped `GET /api/v1/analyses/{analysis_id}/incidents/{incident_id}` instead; see tasks/phase-07-rca-agent.md for the full history.)
- Frontend: "Cookbook" tab rendering Root Cause, Recommended Steps, Commands, Validation, Rollback; "Create Jira Ticket" button shown only for non-critical incidents (disabled/no-op until Phase 10).

## Deliverables
- Full runbook displayed per incident.

## Acceptance Criteria
- Every command in the cookbook traces back to a remediation recommendation (no invented steps).
- Manual Jira button is visible only for non-critical severity.

## Definition of Done
- Cookbook tab renders complete runbook content for a selected incident.
- `get_incident_workflow_graph()` has a real `"cookbook"` node completing the `START -> "rca" -> "remediation" -> "cookbook" -> END` chain, and `GET /api/v1/analyses/{analysis_id}/incidents/{incident_id}` returns a fully populated `IncidentDetail` (rca + recommendations + cookbook all non-null).

## Suggested Git Commit
`feat: add cookbook analyzer`
