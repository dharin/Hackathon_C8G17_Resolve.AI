# Phase 7 — RCA Agent

## Objective
Generate explainable root cause analysis for a selected incident.

## Scope
- RCA Agent outputs: Primary Cause, Evidence, Alternative Causes, Confidence.
- Never recommends fixes (fixes are Remediation Agent's job, Phase 8).
- Wire into the LangGraph incident-workflow graph after incident selection.
- Populate the "RCA" tab in the dashboard.

## Two carry-over issues from Phase 5, resolved as part of this phase's prerequisites
Phase 5 explicitly deferred both of these (see tasks/phase-05-log-reader-agent.md "Scope" and "Known Limitations"). They are now resolved in `backend/graph/` and `backend/api/analyze.py` ahead of this phase, so Phase 7 has real infrastructure to extend rather than assuming it exists:
- **LangGraph orchestrator**: `backend/graph/orchestrator.py` now defines `get_detection_graph()` (Upload → Incidents, already wired into `POST /api/v1/logs/{upload_id}/analyze`) and `get_incident_workflow_graph()` (Selected Incident → RCA → Remediation → Cookbook → Notification). The latter is currently a `START -> END` passthrough over `graph/state.py`'s `IncidentWorkflowState` — Phase 7 is the first phase to give it a real node.
- **API contract**: the original `project-spec.md` contract (`GET /incidents/{id}`) was never implemented; Phase 5 shipped `POST /api/v1/logs/{upload_id}/analyze` + `GET /api/v1/analyses/{analysis_id}/incidents` instead. A `GET /api/v1/analyses/{analysis_id}/incidents/{incident_id}` detail endpoint now exists (`models/incident_detail.py`'s `IncidentDetail`, returned by `api/analyze.py::get_incident_detail`), with `rca`/`recommendations`/`cookbook` fields present but `None` until Phases 7-9 populate them. This is the endpoint to extend below — not `GET /incidents/{id}`.

## Dependencies
- Phase 5 (Log Reader Agent, provides the incident to analyze; also see the two carry-over items above).
- Phase 3 (dashboard tabs to display results).

## Implementation Tasks
- `backend/agents/rca.py`: LLM-driven RCA generation grounded in the selected incident's log evidence.
- `backend/models/rca_report.py`: `RCAReport` Pydantic model.
- In `backend/graph/orchestrator.py::get_incident_workflow_graph()`, add an `"rca"` node wrapping the new agent and replace the `START -> END` edge with `START -> "rca" -> END`. Update `IncidentWorkflowState.root_cause` in `graph/state.py` from `dict[str, Any] | None` to `RCAReport | None`.
- In `models/incident_detail.py`, change `IncidentDetail.rca` from `dict[str, Any] | None` to `RCAReport | None`, and populate it in `api/analyze.py::get_incident_detail` (by running the incident-workflow graph, or loading/caching a prior run).
- Frontend: RCA tab renders Primary Cause, Evidence, Alternative Causes, Confidence.

## Deliverables
- RCA report generated and displayed per selected incident.

## Acceptance Criteria
- RCA output never contains remediation/fix suggestions.
- Confidence and evidence are always present and traceable to the source log lines.

## Definition of Done
- Selecting an incident in the UI produces and displays a complete RCA report.
- `get_incident_workflow_graph()` has a real `"rca"` node (no more passthrough) and `GET /api/v1/analyses/{analysis_id}/incidents/{incident_id}` returns a populated `rca` field.

## Suggested Git Commit
`feat: add RCA agent`
