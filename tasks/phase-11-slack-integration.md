# Phase 11 — Slack Integration

## Objective
Notify operations teams in Slack for critical incidents, after the Jira ticket exists.

## Scope
- `POST /notify-slack` endpoint.
- Critical incidents only; Slack notification always fires after Jira creation, never before or independently.

## Dependencies
- Phase 10 (Jira ticket must exist first for critical incidents).

## Implementation Tasks
- `backend/integrations/slack.py`: Slack Web API client (post message to configured channel).
- Add `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID` to `.env.example`.
- `api/slack.py`: `POST /notify-slack` route, message includes incident summary + Jira ticket link.
- Extend LangGraph: `Jira` → `Slack` sequential edge for critical incidents only (per Sequence Diagram in project-spec.md).
- Frontend: surface notification status (sent/failed) in the Bottom Action Panel for critical incidents.

## Deliverables
- Automatic Slack notification for critical incidents, fired only after successful Jira creation.

## Acceptance Criteria
- Non-critical incidents never trigger a Slack notification.
- Slack message is only sent after the Jira ticket is successfully created; a Jira failure blocks the Slack notification.

## Definition of Done
- Verified message delivery to a test Slack channel (or mocked client if no live workspace is available for the demo).

## Suggested Git Commit
`feat: integrate Slack notifications`
