# Phase 8 — Remediation Agent

## Objective
Recommend grounded remediations using RAG, with zero hallucination.

## Scope
- Remediation Agent queries LanceDB (Confluence Cloud pages and the local SOP directory — see Phase 6, which superseded the original Google Drive/Historical Incidents source list; both are explicitly out of scope, see project-spec.md "Out of Scope") via `rag.retriever.Retriever` (`rag/pipeline.py::get_retriever()`).
- Returns ranked recommendations with confidence, rationale, and supporting documentation.
- If no documentation exists, returns exactly: "No supporting documentation found." — never hallucinates a fix.
- Builds the Jira payload (creation itself happens in Phase 10).

## Dependencies
- Phase 6 (RAG pipeline — use `rag.retriever.Retriever.retrieve()`, which returns `RetrievedChunk`s already carrying `source_type` (`"confluence"` | `"local_sop"`), `title`, `source_uri`, `section_path`, and `score`; see `rag/models.py`). Phase 7 (RCA, provides root cause context to ground retrieval; also see Phase 7's task doc for the LangGraph/API-contract prerequisites this phase builds on).

## Implementation Tasks
- `backend/agents/remediation.py`: call `get_retriever().retrieve(query=<RCA primary cause>, ...)` for the RCA's primary cause, rank results into recommendations.
- `backend/models/recommendation.py` (Recommendation Pydantic model — reuse `rag.models.RetrievedChunk` directly for each recommendation's `sources` field rather than introducing a separate `source_reference.py` duplicate, since it already carries every field the UI needs), `backend/models/jira_payload.py` Pydantic model.
- In `backend/graph/orchestrator.py::get_incident_workflow_graph()`, add a `"remediation"` node between `"rca"` (added in Phase 7) and `END`. Update `IncidentWorkflowState.recommendations`/`.jira_payload` in `graph/state.py` from `dict`/`list[dict]` to the real `Recommendation`/`JiraPayload` types.
- In `models/incident_detail.py`, change `IncidentDetail.recommendations` from `list[dict[str, Any]] | None` to `list[Recommendation] | None`, and populate it in `api/analyze.py::get_incident_detail`.
- Frontend: "Recommended Steps" tab — each recommendation with Confidence, Reason, Supporting Sources (icon, title, Confluence/Local SOP badge, section, last updated, open link).

## Deliverables
- Grounded, source-attributed remediation recommendations per incident.
- Draft Jira payload available in shared state for later phases.

## Acceptance Criteria
- Every recommendation cites at least one source, or the agent explicitly returns "No supporting documentation found."
- No recommendation is generated without a corresponding retrieved source.

## Definition of Done
- Recommended Steps tab renders real recommendations with working source links.
- `get_incident_workflow_graph()` has a real `"remediation"` node and `GET /api/v1/analyses/{analysis_id}/incidents/{incident_id}` returns a populated `recommendations` field.

## Suggested Git Commit
`feat: implement remediation agent`
