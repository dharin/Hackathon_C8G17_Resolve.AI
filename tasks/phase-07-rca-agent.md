# Phase 7 — RCA Agent

## Objective
Generate explainable root cause analysis for a selected incident.

## Scope
- RCA Agent outputs: Primary Cause, Evidence, Alternative Causes, Confidence.
- Never recommends fixes (fixes are Remediation Agent's job, Phase 8).
- Wire into LangGraph shared state after incident selection.
- Populate the "RCA" tab in the dashboard.

## Dependencies
- Phase 5 (Log Reader Agent, provides the incident to analyze).
- Phase 3 (dashboard tabs to display results).

## Implementation Tasks
- `backend/agents/rca.py`: LLM-driven RCA generation grounded in the selected incident's log evidence.
- `backend/models/rca_report.py`: `RCAReport` Pydantic model.
- Extend LangGraph: `Selected Incident` → `RCA` state transition.
- Extend `GET /incidents/{id}` to include the RCA report once generated.
- Frontend: RCA tab renders Primary Cause, Evidence, Alternative Causes, Confidence.

## Deliverables
- RCA report generated and displayed per selected incident.

## Acceptance Criteria
- RCA output never contains remediation/fix suggestions.
- Confidence and evidence are always present and traceable to the source log lines.

## Definition of Done
- Selecting an incident in the UI produces and displays a complete RCA report.

## Suggested Git Commit
`feat: add RCA agent`
