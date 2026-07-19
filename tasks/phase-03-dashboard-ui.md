# Phase 3 — Dashboard UI

## Objective
Build the enterprise dashboard shell that hosts the incident-analysis workflow.

## Scope
- Sidebar navigation: Dashboard, Upload Logs, Knowledge Base, RAG Configuration, Integrations, Audit Logs, Settings, Help.
- Top header with username (from Phase 2) and a per-incident workflow stepper (Log Reader → RCA → Remediation → Cookbook → Notification).
- Incident list left panel + incident details right panel (mock data).
- Tab layout: Overview, RCA, Recommended Steps, Cookbook, Logs, Metadata.
- Design language: dark sidebar, light workspace, purple accent, rounded cards, subtle glassmorphism on sticky surfaces only, responsive.

## Dependencies
- Phase 1 (scaffold), Phase 2 (auth, for header username + route protection).

## Design Language (supersedes project-spec.md's "dark theme")
The approved design explicitly splits the theme rather than applying dark mode app-wide:
- **Sidebar**: always dark, via shadcn's `--sidebar-*` CSS variables set directly in `:root` (independent of any `.dark` class) — `app/globals.css`.
- **Workspace**: light, default `:root` background/foreground.
- **Accent**: purple (`--primary`, `--ring`, `--sidebar-primary` all set to a violet oklch value).
- **Radius**: bumped to `0.85rem` for rounded cards.
- **Glassmorphism**: two narrow utility classes (`.glass-surface`, `.glass-sidebar-surface`) using `backdrop-blur` + translucent background, applied only to sticky surfaces (`TopHeader`, `BottomActionPanel`) — not used broadly.

## Implementation Tasks
- `components/sidebar.tsx` — `Sidebar` (fixed desktop) + `MobileSidebar` (Sheet-based off-canvas, `lg:hidden` trigger), active-route highlighting via `usePathname`.
- `components/top-header.tsx` — replaces Phase 2's placeholder `header.tsx`; sticky, glass surface, mobile nav trigger, Clerk loading/username/sign-out (same behavior as Phase 2, integrated into the new shell).
- `components/workflow-stepper.tsx` — renders the selected incident's 5-step workflow with complete/current/pending states.
- `components/severity-badge.tsx`, `components/incident-card.tsx`, `components/incident-list.tsx` — incident list panel.
- `components/rca-panel.tsx`, `components/recommendation-card.tsx`, `components/source-reference-list.tsx`, `components/cookbook-panel.tsx` — tab content, each with an explicit empty state (no RCA yet / "No supporting documentation found" / no runbook yet).
- `components/incident-details.tsx` — tabs (shadcn `Tabs`) wiring the above + Overview/Logs/Metadata.
- `components/bottom-action-panel.tsx` — critical incidents show auto Jira/Slack status; non-critical show a manual "Create Jira Ticket" button (local state only, no backend call).
- `features/dashboard/dashboard-shell.tsx` — client component holding `selectedIncidentId` state, composes stepper + list + details.
- `app/(dashboard)/layout.tsx` — Sidebar + TopHeader shell, applied only to dashboard routes (sign-in/sign-up stay outside the route group, unaffected).
- `app/(dashboard)/page.tsx` — renders `DashboardShell` with `lib/mock-incidents.ts` (4 incidents spanning all severities and workflow stages, to exercise every tab's populated and empty states).
- `types/incident.ts` — `Incident`, `RCAReport`, `Recommendation`, `SourceReference`, `Cookbook`, `WorkflowStep`, etc.
- Added shadcn primitives: `tabs`, `badge`, `card`, `separator`, `scroll-area`, `skeleton`, `sheet`.

## Deliverables
- Fully navigable dashboard shell with mock data across 4 incidents.

## Acceptance Criteria
- Sidebar, top header, stepper, incident list, and tabs render correctly per the approved design language (dark sidebar / light workspace / purple accent).
- Layout is responsive: sidebar collapses to an off-canvas sheet below the `lg` breakpoint; list/details stack vertically on small screens.
- No backend calls except the existing `/health` check (unused by this phase's UI — no network calls at all yet, since nothing in this phase's mock UI hits the backend).

## Definition of Done
- `npm run build` passes clean (typecheck + lint) with no errors.
- No test cases written for this phase (explicitly out of scope per this phase's instructions).

## Known Limitations / Follow-ups
- Visual/browser verification (screenshots) was skipped per instruction — verified via clean production build (typecheck + ESLint) only, not an in-browser check.
- Sidebar routes other than Dashboard (`Upload Logs`, `Knowledge Base`, etc.) are placeholder links with no destination pages yet — later phases build those out.
- `BottomActionPanel`'s "Create Jira Ticket" button only flips local UI state; Phase 10 wires it to a real API call.

## Suggested Git Commit
`feat: build dashboard layout`
