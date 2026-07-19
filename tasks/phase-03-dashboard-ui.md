# Phase 3 — Dashboard UI

## Objective
Build the enterprise dashboard shell that hosts the incident-analysis workflow.

## Scope
- Sidebar navigation: Dashboard, Upload Logs, Knowledge Base, RAG Configuration, Integrations, Audit Logs, Settings, Help.
- Header with username (from Phase 2) and workflow stepper (Log Reader → RCA → Remediation → Cookbook → Notification).
- Incident list left panel (static/mock data for now).
- Main tab layout: Overview, RCA, Recommended Steps, Cookbook, Logs, Metadata.
- Dark theme.

## Dependencies
- Phase 1 (scaffold), Phase 2 (auth, for header username).

## Implementation Tasks
- Build `components/` for `Sidebar`, `Header`, `WorkflowStepper`, `IncidentList`, `IncidentDetails`, `Tabs`, `FooterActions` per project-spec.md's Component Hierarchy.
- Wire dark theme via Tailwind config.
- Use mock incident data (no backend call yet) to populate `IncidentList` cards (Title, Service, Timestamp, Severity).
- Empty-state placeholders for each tab until later phases populate them.

## Deliverables
- Fully navigable dashboard shell with mock data.

## Acceptance Criteria
- Sidebar, header, stepper, incident list, and tabs render correctly in dark theme.
- Layout matches project-spec.md's UI Specification section.

## Definition of Done
- Dashboard shell renders with no console errors; responsive on common breakpoints.

## Suggested Git Commit
`feat: build dashboard layout`
