# Phase 10 — Jira Integration

## Objective
Automate ticket creation for critical incidents; support manual creation for non-critical ones.

## Scope
- `POST /create-jira` endpoint using the Jira payload built in Phase 8.
- Critical incidents: automatic ticket creation (triggered by the Notification/Decision step in the graph).
- Non-critical incidents: manual creation via the Cookbook tab's "Create Jira Ticket" button (Phase 9).

## Dependencies
- Phase 8 (Jira payload), Phase 9 (manual trigger button).

## Implementation Tasks
- `backend/integrations/jira.py`: Jira REST client (create issue from `JiraPayload`).
- Add `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN` to `.env.example`.
- `api/jira.py`: `POST /create-jira` route, returns created ticket reference (key/URL).
- Extend LangGraph decision node: `Critical?` → auto-invoke Jira creation; non-critical → wait for manual trigger.
- Frontend: wire the Cookbook "Create Jira Ticket" button to `POST /create-jira`; show resulting ticket link/confirmation.
- Graceful error handling/retry (exponential backoff) on Jira API failures, per Risk Register.

## Deliverables
- Working Jira ticket creation, automatic for critical and manual for non-critical incidents.

## Acceptance Criteria
- A critical incident automatically produces a Jira ticket without user action.
- A non-critical incident produces a ticket only after the user clicks "Create Jira Ticket".

## Definition of Done
- Verified ticket creation against a test Jira project (or mocked client if no live project is available for the demo).

## Suggested Git Commit
`feat: integrate Jira`
