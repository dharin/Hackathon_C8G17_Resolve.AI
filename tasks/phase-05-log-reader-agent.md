# Phase 5 — Log Reader Agent

## Objective
Parse uploaded logs and detect all incidents, laying the groundwork for the LangGraph orchestrator.

## Scope
- Log Reader Agent: parse, categorize, assign severity, extract metadata, calculate confidence, for ALL incidents in the uploaded log.
- `GET /incidents` and `GET /incidents/{id}` endpoints (incidents only — no RCA/remediation/cookbook data yet, those come in later phases).
- No Jira creation. No Slack notification (explicitly out of scope for this agent).
- Wire real incident data into the Phase 3 `IncidentList` UI (replacing mock data).

## Dependencies
- Phase 4 (log upload, provides the file/`uploadId` to parse).
- Phase 3 (dashboard UI, to display results).

## Implementation Tasks
- `backend/agents/log_reader.py`: parsing logic (rule-based/LLM-assisted) producing a list of `Incident` objects.
- `backend/models/incident.py`: `Incident` Pydantic model (id, title, service, timestamp, severity, category, confidence, metadata).
- `backend/graph/`: initial LangGraph node wrapping the Log Reader Agent, seeding the shared state's `Uploaded Log` → `Incident List`.
- `api/incidents.py`: `GET /incidents`, `GET /incidents/{id}`.
- Frontend: replace mock data in `IncidentList` with a real API call via React Query.

## Deliverables
- Incident list populated from real log parsing, per uploaded file.

## Acceptance Criteria
- Uploading a log with multiple distinct issues produces multiple correctly categorized/severity-tagged incidents.
- No Jira or Slack calls occur anywhere in this phase.

## Definition of Done
- `GET /incidents` returns parsed incidents for a given upload; UI reflects them.

## Suggested Git Commit
`feat: add log reader agent`
