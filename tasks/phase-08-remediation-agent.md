# Phase 8 — Remediation Agent

## Objective
Recommend grounded remediations using RAG, with zero hallucination.

## Scope
- Remediation Agent queries LanceDB (Confluence, Google Drive SOPs, Historical Incidents) via the Phase 6 RAG pipeline.
- Returns ranked recommendations with confidence, rationale, and supporting documentation.
- If no documentation exists, returns exactly: "No supporting documentation found." — never hallucinates a fix.
- Builds the Jira payload (creation itself happens in Phase 10).

## Dependencies
- Phase 6 (RAG pipeline). Phase 7 (RCA, provides root cause context to ground retrieval).

## Implementation Tasks
- `backend/agents/remediation.py`: retrieve top-k relevant chunks for the RCA's primary cause, rank into recommendations.
- `backend/models/recommendation.py`, `backend/models/source_reference.py`, `backend/models/jira_payload.py` Pydantic models.
- Extend LangGraph: `RCA` → `Remediation` state transition, populating `Recommendations` and `Jira Payload` in shared state.
- Extend `GET /incidents/{id}` response to include recommendations + sources.
- Frontend: "Recommended Steps" tab — each recommendation with Confidence, Reason, Supporting Sources (icon, title, Confluence/Drive badge, section, last updated, open link).

## Deliverables
- Grounded, source-attributed remediation recommendations per incident.
- Draft Jira payload available in shared state for later phases.

## Acceptance Criteria
- Every recommendation cites at least one source, or the agent explicitly returns "No supporting documentation found."
- No recommendation is generated without a corresponding retrieved source.

## Definition of Done
- Recommended Steps tab renders real recommendations with working source links.

## Suggested Git Commit
`feat: implement remediation agent`
