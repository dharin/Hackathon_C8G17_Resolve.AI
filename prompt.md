# Claude Development Prompts

## Multi-Agent DevOps Incident Analysis Suite

---

# 0. Master System Prompt

You are acting as a senior full-stack engineer and AI platform engineer.

You are implementing the project described in the attached `project-spec.md`.

Treat `project-spec.md` as the single source of truth.

Do not change architecture, workflows, agent responsibilities, API contracts, UI structure, integration rules, or security requirements unless explicitly instructed.

This is a hackathon project. Keep the implementation:

* Simple
* Modular
* Demonstrable
* Production-inspired
* Easy to run locally
* Easy to deploy
* Free from unnecessary complexity

Before implementing any phase:

1. Read `project-spec.md`.
2. Read the relevant task file from `/tasks`.
3. Identify dependencies from earlier phases.
4. List the files that will be created or modified.
5. Implement only the requested phase.
6. Do not implement future phases unless required for a minimal interface or placeholder.
7. Use mock data where an external integration is not yet available.
8. Keep all secrets in environment variables.
9. Never hardcode API keys, tokens, credentials, URLs, user emails, or channel IDs.
10. Update documentation whenever architecture or configuration is affected.

After each phase, provide:

* Summary of work completed
* Files created
* Files modified
* Environment variables added
* How to run and test the phase
* Acceptance criteria status
* Known limitations
* Suggested Git commit message

Do not generate unrelated features.

---

# 1. Repository and Task Setup Prompt

Read `project-spec.md`.

Create the initial repository planning structure without implementing the application logic yet.

Required output:

```text
project-root/
├── frontend/
├── backend/
├── docs/
│   └── project-spec.md
├── tasks/
├── .env.example
├── .gitignore
└── README.md
```

Create the following task files:

```text
tasks/
├── phase-01-project-bootstrap.md
├── phase-02-authentication.md
├── phase-03-dashboard-ui.md
├── phase-04-log-upload.md
├── phase-05-log-reader-agent.md
├── phase-06-rag-pipeline.md
├── phase-07-rca-agent.md
├── phase-08-remediation-agent.md
├── phase-09-cookbook-agent.md
├── phase-10-jira-integration.md
├── phase-11-slack-integration.md
├── phase-12-testing.md
└── phase-13-deployment.md
```

Each task file must include:

* Objective
* Scope
* Dependencies
* Deliverables
* Folder structure
* Implementation tasks
* Acceptance criteria
* Definition of done
* Suggested commits
* Known risks

Do not implement product code in this step.

---

# 2. Phase 1 Prompt — Project Bootstrap

Implement Phase 1: Project Bootstrap.

Read:

* `project-spec.md`
* `tasks/phase-01-project-bootstrap.md`

Set up:

## Frontend

* Next.js 15
* React
* TypeScript
* Tailwind CSS
* shadcn/ui-ready structure
* React Query provider
* Framer Motion
* Environment variable support

## Backend

* Python
* FastAPI
* Pydantic
* LangGraph
* LangChain
* Modular folder structure
* Health endpoint
* Environment configuration
* CORS for local frontend

Use this structure:

```text
frontend/
├── app/
├── components/
├── features/
├── hooks/
├── lib/
├── services/
├── types/
└── public/

backend/
├── app/
│   ├── api/
│   ├── agents/
│   ├── graph/
│   ├── rag/
│   ├── integrations/
│   ├── models/
│   ├── services/
│   ├── config/
│   └── main.py
├── tests/
└── requirements.txt
```

Requirements:

* Add `.env.example`
* Add startup documentation
* Add frontend and backend health checks
* Add a basic API client in the frontend
* Do not implement agents or integrations yet

Validate that both applications start locally.

---

# 3. Phase 2 Prompt — Clerk Authentication

Implement Phase 2: Authentication.

Read:

* `project-spec.md`
* `tasks/phase-02-authentication.md`

Implement Clerk authentication in the Next.js frontend.

Requirements:

* Clerk sign-in
* Clerk sign-out
* Protected application routes
* Logged-in username displayed in the header/sidebar
* Loading state while user session resolves
* Redirect unauthenticated users to sign-in
* Do not expose Clerk secret keys in the client

Backend requirements:

* Add authentication middleware or dependency abstraction
* Accept and validate Clerk-issued bearer tokens
* Keep validation modular
* Add an authenticated `/api/v1/me` endpoint
* Return a safe user identity object

Do not implement role-based access control.

Add required Clerk variables to `.env.example`.

Use a clean abstraction so authentication can be mocked in local development if necessary.

---

# 4. Phase 3 Prompt — Dashboard UI

Implement Phase 3: Dashboard UI.

Read:

* `project-spec.md`
* `tasks/phase-03-dashboard-ui.md`

Build the UI to match the approved design language:

* Dark sidebar
* Light workspace
* Purple accent
* Rounded cards
* Minimal enterprise design
* Responsive layout
* Subtle glassmorphism only where appropriate

Sidebar items:

* Dashboard
* Upload Logs
* Knowledge Base
* RAG Configuration
* Integrations
* Audit Logs
* Settings
* Help

Main workspace:

* Workflow progress stepper
* Incident list panel
* Incident details panel
* Tabs:

  * Overview
  * RCA
  * Recommended Steps
  * Cookbook
  * Logs
  * Metadata

Workflow steps:

1. Log Reader
2. RCA
3. Remediation
4. Cookbook
5. Notification

Incident cards must show:

* Title
* Timestamp
* Service
* Severity badge

Use mock data only.

Create reusable components:

* `Sidebar`
* `TopHeader`
* `WorkflowStepper`
* `IncidentList`
* `IncidentCard`
* `IncidentDetails`
* `SeverityBadge`
* `RcaPanel`
* `RecommendationCard`
* `SourceReferenceList`
* `CookbookPanel`
* `BottomActionPanel`

Do not connect to backend APIs yet except the health endpoint.

---

# 5. Phase 4 Prompt — Log Upload

Implement Phase 4: Log Upload.

Read:

* `project-spec.md`
* `tasks/phase-04-log-upload.md`

Frontend requirements:

* Drag-and-drop upload
* File browser upload
* Accept `.log` and `.txt`
* Validate extension
* Validate configurable file-size limit
* Show upload progress
* Show file name and size
* Show clear error messages
* Prevent duplicate submissions
* Display upload result

Backend requirements:

Create:

```text
POST /api/v1/logs/upload
```

The endpoint must:

* Accept one log file
* Validate type and size
* Store the file locally
* Generate an upload ID
* Return metadata
* Never execute or interpret file contents as code

Suggested response:

```json
{
  "upload_id": "string",
  "file_name": "application.log",
  "size_bytes": 1000,
  "status": "uploaded"
}
```

Use safe generated file names.

Do not run agent analysis yet.

---

# 6. Phase 5 Prompt — Log Reader Agent

Implement Phase 5: Log Reader Agent.

Read:

* `project-spec.md`
* `tasks/phase-05-log-reader-agent.md`

Implement the Log Reader Agent only.

Responsibilities:

* Read uploaded logs
* Parse timestamps where possible
* Detect all incidents
* Classify category
* Assign severity
* Extract service name
* Extract category-specific fields
* Preserve raw excerpts
* Calculate confidence
* Return all incidents regardless of severity

Supported categories:

* OOM kill
* Disk-space exhaustion
* Authentication failure
* Timeout
* Database connection error
* HTTP 5xx spike
* Unknown

Important rules:

* The Log Reader Agent must not create Jira tickets
* The Log Reader Agent must not send Slack notifications
* All detected incidents must be returned
* Unknown patterns must not be forced into known categories

Create Pydantic models for:

* Issue category
* Severity
* Log issue
* Upload analysis result

Create API endpoint:

```text
POST /api/v1/logs/{upload_id}/analyze
```

Create endpoint:

```text
GET /api/v1/analyses/{analysis_id}/incidents
```

Use deterministic parsing rules first and use the LLM only where necessary.

Add sample logs and tests covering every incident category.

---

# 7. Phase 6 Prompt — RAG Pipeline

Implement Phase 6: RAG Pipeline.

Read:

* `project-spec.md`
* `tasks/phase-06-rag-pipeline.md`

Build a simple modular RAG pipeline using:

* LangChain
* LanceDB
* Configurable embedding provider
* Confluence
* Google Drive
* Local document metadata

Supported embedding options:

* `BAAI/bge-small-en`
* `nomic-embed-text`

Create configurable parameters:

* Chunk size
* Chunk overlap
* Top K
* Embedding model
* Context-window size
* Maximum tokens

Implement document metadata containing:

* Source type
* Document title
* Source URL
* Section
* Page ID
* Document ID
* Version
* Last updated date
* Retrieved excerpt
* Content hash

Confluence requirements:

* Weekly incremental synchronization
* Fetch page metadata first
* Detect pages modified since last successful sync
* Re-chunk only changed pages
* Replace stale chunks for changed pages
* Never re-index the entire space during routine sync
* Persist synchronization metadata locally

Google Drive requirements:

* Retrieve configured SOP files
* Preserve original source URLs
* Support a manual ingestion trigger for the hackathon

Create APIs for:

* RAG configuration
* Manual sync
* Sync status
* Knowledge-source listing
* Retrieval testing

Do not connect the RAG pipeline to the agents yet.

Use mocks when credentials are unavailable.

---

# 8. Phase 7 Prompt — RCA Agent

Implement Phase 7: RCA Agent.

Read:

* `project-spec.md`
* `tasks/phase-07-rca-agent.md`

The RCA Agent receives one selected incident and produces:

* Primary cause
* Confidence
* Evidence
* Alternative causes
* Confidence for each alternative

Strict rules:

* Do not recommend remediation
* Do not generate commands
* Do not create Jira
* Do not send Slack
* Clearly separate observed evidence from inferred diagnosis
* Preserve raw-log traceability
* Use structured Pydantic output
* Return insufficient-evidence status where appropriate

Create API endpoint:

```text
POST /api/v1/incidents/{incident_id}/rca
```

Create tests for:

* Strong evidence
* Conflicting evidence
* Unknown incident
* Insufficient evidence
* Multiple alternative causes

Update the RCA UI tab to consume the backend result.

---

# 9. Phase 8 Prompt — Remediation Agent

Implement Phase 8: Remediation Agent.

Read:

* `project-spec.md`
* `tasks/phase-08-remediation-agent.md`

The Remediation Agent receives:

* Incident
* RCA report
* Retrieved RAG context

It must return ranked recommendations.

Each recommendation must contain:

* Rank
* Recommendation
* Confidence
* Reason
* Supporting sources

Each supporting source must contain:

* Source type
* Document title
* Confluence or Google Drive URL
* Section
* Page ID or document ID
* Document version
* Last-updated date
* Retrieved excerpt

Strict grounding rule:

* Recommendations must be supported by retrieved documentation
* Never invent a remediation
* If no relevant source is available, return exactly:

  * `No supporting documentation found`
* Clearly mark unsupported actions as withheld
* Do not create a Jira ticket directly inside the LLM prompt
* Build a structured Jira payload object for the Jira integration phase

Create API endpoint:

```text
POST /api/v1/incidents/{incident_id}/remediation
```

Update the Recommended Steps UI.

Each recommendation card must display:

* Recommendation
* Confidence
* Reason
* Supporting sources
* Document icon
* Source badge
* Section
* Last updated
* Open Link button

Ensure original source links remain clickable.

---

# 10. Phase 9 Prompt — Cookbook Agent

Implement Phase 9: Cookbook Agent.

Read:

* `project-spec.md`
* `tasks/phase-09-cookbook-agent.md`

The Cookbook Agent receives:

* Incident
* RCA
* Ranked remediation recommendations
* Supporting source references

It must produce:

* Root-cause summary
* Recommended steps
* Executable commands
* Validation steps
* Rollback steps
* Safety notes
* Source references

Rules:

* Do not invent commands not supported by source material
* If executable instructions are unavailable, state that no supported runbook was found
* Do not execute commands
* Keep commands display-only
* Preserve traceability to source documents

Create API endpoint:

```text
POST /api/v1/incidents/{incident_id}/cookbook
```

Update the Cookbook UI tab.

For non-critical incidents, display:

```text
Create Jira Ticket
```

For critical incidents, display:

* Automatic Jira status
* Automatic Slack status

Do not implement Jira or Slack calls in this phase.

---

# 11. Phase 10 Prompt — Jira Integration

Implement Phase 10: Jira Integration.

Read:

* `project-spec.md`
* `tasks/phase-10-jira-integration.md`

Implement Jira ticket creation.

Rules:

* The Log Reader Agent must never create Jira
* Jira creation occurs only after remediation and cookbook outputs exist
* Critical incidents create Jira automatically
* Non-critical incidents require explicit user action
* Prevent duplicate Jira creation for the same incident
* Store the created Jira key and URL

The Jira description must contain:

* Incident ID
* Title
* Service
* Timestamp
* Severity
* Category
* Root cause
* Evidence
* Alternative causes
* Recommendations
* Recommendation confidence
* Reasons
* Executable runbook
* Validation
* Rollback
* Supporting documentation

All Confluence and Google Drive URLs must be clickable.

Use Atlassian Document Format when appropriate.

Create:

```text
POST /api/v1/incidents/{incident_id}/jira
```

The endpoint should support:

* Automatic critical flow
* Manual non-critical flow
* Idempotency

Return:

* Jira ticket key
* Jira URL
* Creation status

Update the bottom action panel.

---

# 12. Phase 11 Prompt — Slack Integration

Implement Phase 11: Slack Integration.

Read:

* `project-spec.md`
* `tasks/phase-11-slack-integration.md`

Rules:

* Slack notification is only for critical incidents
* Slack notification occurs only after Jira creation succeeds
* If Jira creation fails, Slack must not claim a ticket was created
* Prevent duplicate Slack notifications

Slack message must include:

* Incident
* Severity
* Service
* Root cause
* Top recommendation
* Jira ticket link
* Supporting-source summary
* Link back to the application incident view, if available

Create:

```text
POST /api/v1/incidents/{incident_id}/notify
```

Update workflow status in the UI.

Include graceful failure and retry handling.

---

# 13. LangGraph Orchestration Prompt

Implement the LangGraph orchestration after the individual agents and integrations exist.

Read `project-spec.md`.

Create a graph with these logical nodes:

* Load incident
* Log Reader
* RCA
* Retrieve knowledge
* Remediation
* Cookbook
* Severity decision
* Create Jira
* Send Slack
* Complete

Required behavior:

```text
Upload log
→ Log Reader
→ Return all incidents
→ User selects incident
→ RCA
→ RAG retrieval
→ Remediation
→ Cookbook
→ Severity decision

Critical:
→ Jira
→ Slack
→ Complete

Non-critical:
→ Wait for user Jira request
→ Complete
```

Important:

* Do not run RCA and remediation automatically for every detected incident unless explicitly requested
* Use selected-incident analysis to reduce hackathon cost and latency
* Persist graph state sufficiently to resume after user selection
* Track node status for the frontend workflow stepper
* Track errors without losing completed outputs

Define the LangGraph state contract using Pydantic-compatible models.

Add tests for both critical and non-critical paths.

---

# 14. Phase 12 Prompt — Testing

Implement Phase 12: Testing.

Read:

* `project-spec.md`
* `tasks/phase-12-testing.md`

Create a focused hackathon testing suite.

Backend tests:

* Upload validation
* Log classification
* All incidents returned
* RCA produces no remediation
* Remediation is source-grounded
* No-document fallback
* Cookbook generation
* Critical automatic Jira path
* Non-critical manual Jira path
* Slack only after Jira
* Duplicate prevention
* Source URLs included in Jira

Frontend tests:

* Incident list displays all severities
* Severity badges
* Tab navigation
* Recommendation sources
* Open Link behavior
* Critical action state
* Non-critical Jira button
* Loading and error states

Integration tests:

* Mock Confluence
* Mock Google Drive
* Mock Jira
* Mock Slack
* Mock LLM where practical

Create one end-to-end demo scenario using a sample log.

Do not overbuild the test suite.

---

# 15. Phase 13 Prompt — Deployment

Implement Phase 13: Deployment.

Read:

* `project-spec.md`
* `tasks/phase-13-deployment.md`

Prepare the project for hackathon deployment.

Preferred deployment:

* Frontend: Vercel
* Backend: Render or Railway
* LanceDB: persistent mounted storage where available
* Local fallback for demo

Requirements:

* Production environment validation
* CORS configuration
* Secure secret handling
* Health endpoints
* Startup checks
* Deployment documentation
* Sample demo data
* Seed or ingestion instructions
* Clear fallback behavior when integrations are unavailable

Create:

* Deployment README
* Environment-variable checklist
* Demo runbook
* Troubleshooting guide

Do not introduce Kubernetes or enterprise infrastructure unless explicitly requested.

---

# 16. End-to-End Validation Prompt

Perform an end-to-end validation of the completed application against `project-spec.md`.

Use this scenario:

1. User logs in with Clerk.
2. User uploads a log containing:

   * Database connection error
   * HTTP 5xx spike
   * Timeout
   * Low-severity authentication failure
3. The UI displays every incident.
4. User selects the critical database incident.
5. RCA returns connection-pool exhaustion.
6. Remediation retrieves Confluence and Google Drive sources.
7. Recommended Steps display clickable source links.
8. Cookbook displays commands, validation, and rollback.
9. Critical incident creates Jira automatically.
10. Jira description contains source links.
11. Slack is sent only after Jira succeeds.
12. User selects a medium incident.
13. Jira is not automatically created.
14. Manual Jira button is displayed.
15. User manually creates the ticket.

Report:

* Passed requirements
* Failed requirements
* Missing implementation
* Security concerns
* Demo blockers
* Recommended minimal fixes

Do not add features during validation.

---

# 17. UI Refinement Prompt

Review the frontend against the approved UI specification.

Do not change workflows or business logic.

Refine:

* Dark enterprise sidebar
* Light main workspace
* Purple accent
* Rounded cards
* Consistent spacing
* Severity colors
* Workflow progress
* Incident-card readability
* Recommendation source cards
* Clickable source links
* RCA evidence hierarchy
* Runbook command presentation
* Critical and non-critical action states
* Responsive layout
* Loading skeletons
* Empty states
* Error states

Keep animations subtle.

Do not overuse glassmorphism.

Provide a list of changed components and screenshots or a clear visual verification checklist.

---

# 18. Security Review Prompt

Perform a security review against `project-spec.md`.

Review:

* Clerk token validation
* API authorization
* File-upload safety
* File-size limits
* File-name sanitization
* Secret management
* Confluence credentials
* Google Drive credentials
* Jira credentials
* Slack tokens
* URL validation
* Log injection
* Prompt injection inside logs
* Prompt injection inside Confluence and SOP content
* Output rendering
* Command display safety
* Duplicate Jira/Slack prevention
* Audit logging

Implement only high-priority, hackathon-appropriate fixes.

Do not introduce complex enterprise security platforms.

---

# 19. Documentation Completion Prompt

Review all project documentation.

Ensure the repository contains:

* `README.md`
* `docs/project-spec.md`
* Phase task files
* Environment-variable documentation
* Local development guide
* Deployment guide
* RAG ingestion guide
* Integration setup guide
* Demo scenario
* Troubleshooting guide
* API summary
* Architecture summary

The documentation must reflect the actual implementation.

Remove stale instructions and placeholders.

---

# 20. Final Hackathon Readiness Prompt

Act as the technical lead conducting the final hackathon readiness review.

Evaluate:

* Can the project run locally?
* Can it be deployed?
* Can a user log in?
* Can a log be uploaded?
* Are all incidents displayed?
* Does selected-incident analysis work?
* Does RCA avoid remediation?
* Are remediations source-grounded?
* Are source links displayed in the UI?
* Are source links included in Jira?
* Is the cookbook traceable?
* Does critical automation work?
* Does non-critical manual Jira work?
* Does Slack run only after Jira?
* Are missing SOPs handled without hallucination?
* Is the demo flow reliable?

Return:

* Ready / Not Ready
* Critical blockers
* Recommended fixes
* Demo script
* Recovery plan if Confluence, Google Drive, Jira, Slack, or OpenAI is unavailable during the hackathon

Do not add new features.
