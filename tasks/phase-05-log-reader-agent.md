# Phase 5 — Log Reader Agent

## Objective
Parse uploaded logs and detect all incidents.

## Scope (narrowed explicitly this turn)
This phase was scoped to **the Log Reader Agent only** — deterministic parsing, models, the two API endpoints, and tests. Explicitly out of scope for this turn (deferred to later phases):
- LangGraph node wiring (`backend/graph/`) — no orchestrator exists yet to wire into.
- Frontend integration (replacing `lib/mock-incidents.ts` in the dashboard) — not requested this turn.
- No Jira creation, no Slack notification — structurally guaranteed (see Tests).

## API deviation from the original task file (explicitly instructed this turn)
Originally `GET /incidents` / `GET /incidents/{id}` (a flat incident store). Implemented instead as an explicit two-step contract:
- `POST /api/v1/logs/{upload_id}/analyze` — runs the agent against an uploaded file, persists the run, returns the full `UploadAnalysisResult`.
- `GET /api/v1/analyses/{analysis_id}/incidents` — retrieves just the incidents from a previous analysis run.

This makes each log upload support multiple independent analysis runs (each POST creates a new `analysis_id`), rather than one global incident list per upload.

## Supported categories
`oom_kill`, `disk_space_exhaustion`, `auth_failure`, `timeout`, `database_connection_error`, `http_5xx_spike`, `unknown`.

## Implementation Tasks
- **Models**: `models/severity.py` (`Severity`), `models/issue_category.py` (`IssueCategory`), `models/log_issue.py` (`LogIssue` — category, severity, title, service, timestamp, confidence, category-specific `fields`, `raw_excerpt`, `detection_method`), `models/upload_analysis.py` (`UploadAnalysisResult`).
- **Deterministic parsing** (`services/log_reader/`):
  - `timestamp_parser.py` — best-effort ISO 8601 and syslog-style timestamp extraction; returns `None` rather than raising when nothing recognizable is found.
  - `service_extractor.py` — heuristic service-name extraction (`service=`/`svc=`/`app=`/`component=` key-value, `[bracket]`, or a leading `prefix:`).
  - `patterns.py` — one regex-based detector per category, checked in priority order (most specific first — e.g. a DB-flavored timeout resolves to `database_connection_error`, not the generic `timeout` bucket, because DB is checked first). Also exposes `has_problem_signal()` for the LLM-eligibility check.
  - `agent.py` — `LogReaderAgent.analyze(text)`: scans line by line, runs deterministic detectors first, falls back to the LLM classifier only for lines with an evident problem signal (ERROR/FATAL/WARN/exception-like) that matched no rule; groups nearby same-category/same-service matches into one incident (occurrence count, merged fields, severity escalates one tier at ≥3 occurrences and two tiers at ≥5, capped at critical); never imports anything Jira/Slack-related (see Tests).
  - `llm_classifier.py` — optional fallback via OpenRouter (OpenAI-compatible API, using the `openai` SDK pointed at `https://openrouter.ai/api/v1`). Returns `None` (never raises) if `OPENROUTER_API_KEY` isn't configured or the SDK/call fails; callers treat `None` as "classify as unknown," never as an error. Unknown is never forced into a known category, whether or not the LLM was consulted. Model is configurable via `OPENROUTER_MODEL` (default `openai/gpt-4.1-mini`).
- **Persistence**: `services/analysis_store.py` — analyses saved as JSON under `backend/analyses/` (git-ignored, mirrors the `uploads/` pattern from Phase 4). No database, per hackathon scope.
- **API**: `api/analyze.py` — both endpoints, both behind the existing `get_current_user` auth dependency; 404 on unknown `upload_id`/`analysis_id`.
- **Config**: `config/settings.py` — added `ANALYSES_DIR`, `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`.
- **Tests**: `backend/pytest.ini` (adds `backend/` to `pythonpath` so the app's flat import style — `from models... `, `from services...` — resolves under pytest), `backend/tests/conftest.py` (forces `AUTH_PROVIDER=mock` and blanks `OPENROUTER_API_KEY` regardless of the developer's local `.env`, so the suite is fully offline and deterministic), `backend/tests/test_log_reader_agent.py` (one test per category + a mixed-log multi-incident test + a structural "never imports jira/slack" test via AST inspection), `backend/tests/test_analyze_api.py` (upload → analyze → fetch-incidents end-to-end, 404s, auth requirement).
- **Sample logs**: `backend/tests/fixtures/sample_logs/` — one file per category (`oom_kill.log`, `disk_space_exhaustion.log`, `auth_failure.log`, `timeout.log`, `database_connection_error.log`, `http_5xx_spike.log`, `unknown.log`) plus `mixed.log` combining several categories and an informational-only line (to prove non-anomalous lines never become incidents).

## Deliverables
- `LogReaderAgent` producing `LogIssue` objects for every detected incident, regardless of severity.
- `POST /api/v1/logs/{upload_id}/analyze` and `GET /api/v1/analyses/{analysis_id}/incidents`, both working end-to-end (verified via `curl` against the live server, in addition to the automated tests).

## Acceptance Criteria
- A log with multiple distinct issues produces multiple correctly categorized/severity-tagged incidents — verified by `test_mixed_log_detects_all_incidents_regardless_of_severity` and a live `curl` run against `mixed.log`.
- No Jira or Slack calls occur anywhere in this phase — structurally guaranteed (the log-reader package imports nothing Jira/Slack-related; verified by AST-based test) and behaviorally trivial (no such integration exists yet in the codebase at all).
- Unknown patterns are never forced into a known category — verified by `test_unknown_pattern_not_forced_into_known_category`.

## Definition of Done
- `pytest` — **14/14 tests pass** (`backend/tests/`), fully offline (no real Clerk or OpenRouter credentials used).
- Live end-to-end smoke test via `curl` (upload → analyze → fetch incidents) confirmed correct output.

## Known Limitations / Follow-ups
- The LLM fallback path (`llm_classifier.py`) is implemented but **not exercised by any test** — tests deliberately blank `OPENROUTER_API_KEY` to stay deterministic and avoid real API calls/costs. If you configure a real key locally, a genuinely unclassifiable ERROR/WARN line will now get one classification attempt before falling back to `unknown`; this is unverified against a live OpenRouter account.
- Service-name and timestamp extraction are heuristic (regex-based), not a full log-format parser — logs in unusual formats may end up with `service: null` or `timestamp: null`. Both fields are explicitly optional in `LogIssue` for exactly this reason.
- No LangGraph node yet — this agent is currently only reachable via its direct API endpoints, not as part of a larger orchestrated workflow.

## Suggested Git Commit
`feat: add log reader agent`
