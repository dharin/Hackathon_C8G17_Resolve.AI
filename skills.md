# SKILLS.md

# Multi-Agent DevOps Incident Analysis Suite

## Claude Code Skills Configuration

This document defines the Claude Code skills recommended for building the **Multi-Agent DevOps Incident Analysis Suite**.

The project specification in `docs/project-spec.md` remains the single source of truth. Skills provide implementation guidance only and must not override the approved architecture, workflows, agent responsibilities, or business rules.

---

# 1. Skill Usage Principles

Claude Code must follow these rules:

1. Read `docs/project-spec.md` before starting any implementation.
2. Read the relevant file under `/tasks` before implementing a phase.
3. Use installed skills only as implementation guidance.
4. Do not allow a skill to change requirements defined in `project-spec.md`.
5. Use only skills relevant to the current development phase.
6. Avoid unnecessary abstractions because this is a hackathon project.
7. Prefer simple, modular, testable implementations.
8. Verify each phase before marking it complete.
9. Do not install unknown or unverified skills merely because their names match the technology.
10. Use official documentation for FastAPI, LangGraph, LangChain, LanceDB, Clerk, Jira, Slack, Confluence, and Google Drive when a dedicated skill is unavailable.

---

# 2. Initial Skills

Install these skills before starting the Master Prompt and Phase 1.

## 2.1 Find Skills

**Purpose**

Helps discover additional skills later when a new technical need appears.

```bash
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```

**Use for**

* Discovering testing skills
* Discovering deployment skills
* Discovering framework-specific guidance
* Finding skills for future enhancements

**Do not use for**

* Automatically installing every suggested skill
* Replacing official framework documentation

---

## 2.2 Writing Plans

**Purpose**

Converts the project specification into structured implementation plans.

```bash
npx skills add https://github.com/obra/superpowers --skill writing-plans
```

**Use for**

* Phase planning
* Task breakdown
* Dependency identification
* Acceptance-criteria planning
* File-change planning

**Required before**

* Repository setup
* Phase 1
* Any major architectural change

---

## 2.3 Executing Plans

**Purpose**

Executes approved implementation plans incrementally.

```bash
npx skills add https://github.com/obra/superpowers --skill executing-plans
```

**Use for**

* Implementing one phase at a time
* Tracking completed tasks
* Preventing accidental implementation of future phases
* Maintaining phase boundaries

**Rule**

Claude must complete and verify the current phase before moving to the next phase.

---

## 2.4 Verification Before Completion

**Purpose**

Prevents Claude from declaring a phase complete without validating it.

```bash
npx skills add https://github.com/obra/superpowers --skill verification-before-completion
```

**Use for**

* Build verification
* Test execution
* Lint verification
* API validation
* Acceptance-criteria review
* Final phase reporting

**Mandatory verification**

Before marking any phase complete, Claude must report:

* Commands executed
* Tests executed
* Build status
* Acceptance criteria status
* Known limitations
* Remaining issues

---

# 3. Frontend Skills

Install these before implementing the frontend bootstrap and dashboard.

## 3.1 Next.js App Router Patterns

Replaces the retired `vercel-labs/next-skills` `next-best-practices` skill (that repo no longer ships installable skills). Use this high-adoption App Router skill instead:

```bash
npx skills add https://github.com/wshobson/agents --skill nextjs-app-router-patterns
```

**Use for**

* Next.js App Router
* Server and Client Component boundaries
* Route organization
* Streaming and Suspense
* Server Actions and Route Handlers
* Error and loading boundaries
* Data-fetching and caching conventions
* Metadata
* Performance-conscious application structure

**Project-specific rules**

* Use Next.js 15.
* Use TypeScript.
* Keep interactive dashboard components as Client Components only where required.
* Keep authentication and route protection centralized.
* Do not place backend secrets in frontend environment variables.
* Do not access Jira, Slack, Confluence, Google Drive, or OpenAI directly from the browser.

---

## 3.2 React Best Practices

```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices
```

**Use for**

* Component composition
* React Query integration
* Avoiding unnecessary rerenders
* Avoiding data-fetching waterfalls
* Managing loading and error states
* Keeping component APIs small

**Project-specific rules**

* React Query owns server state.
* Local React state owns temporary UI state.
* Avoid duplicating API data in multiple state stores.
* Do not introduce Redux unless the approved project specification changes.
* Keep incident, RCA, remediation, cookbook, Jira, and Slack states clearly separated.

---

## 3.3 shadcn/ui

```bash
npx skills add https://github.com/shadcn/ui --skill shadcn
```

**Use for**

* Tabs
* Cards
* Badges
* Buttons
* Dialogs
* Tooltips
* Dropdowns
* Progress indicators
* Skeleton loaders
* Alerts
* Forms

**Project-specific rules**

* Use shadcn/ui as a component foundation.
* Customize components to match the approved design language.
* Avoid copying large prebuilt dashboards that do not match the specification.
* Maintain a dark sidebar, light workspace, and purple accent.
* Keep styling consistent across all screens.

---

## 3.4 Frontend Design

```bash
npx skills add https://github.com/anthropics/skills --skill frontend-design
```

**Use for**

* Enterprise dashboard layout
* Visual hierarchy
* Typography
* Spacing
* Responsive behavior
* Empty states
* Error states
* Recommendation source cards
* Incident severity presentation
* Workflow progress design

**Approved design language**

* Dark sidebar
* Light main workspace
* Purple accent
* Rounded cards
* Minimal enterprise design
* Subtle shadows
* Limited glassmorphism
* Clear information hierarchy
* Subtle motion only

**Do not**

* Use excessive gradients
* Use excessive animations
* Overuse glassmorphism
* Hide important incident data behind animations
* Sacrifice readability for visual decoration

---

## 3.5 Web Design Guidelines

```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines
```

**Use for**

* Accessibility review
* Keyboard navigation
* Color contrast
* Focus indicators
* Form usability
* Responsive behavior
* Link and button semantics

**Required checks**

* Severity badges must not rely on color alone.
* Source links must be keyboard accessible.
* Loading states must be understandable.
* Error messages must explain corrective actions.
* Buttons must use descriptive labels.
* Tabs must support accessible keyboard navigation.

---

## 3.6 Taste Skills

Anti-generic frontend design guidance from [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill).

Install the default taste skill plus the restrained product-UI skill that fits this enterprise dashboard:

```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill design-taste-frontend
npx skills add https://github.com/Leonxlnx/taste-skill --skill minimalist-ui
```

**Use for**

* Avoiding templated "AI slop" layouts
* Typography, spacing, hierarchy, and motion decisions
* Restrained product UI closer to Linear/Notion for the incident dashboard
* Pre-flight visual review before declaring UI work complete
* Redesigning screens while preserving approved product rules

**Which skill when**

* `design-taste-frontend` — general anti-slop taste rules; stronger for marketing/landing surfaces
* `minimalist-ui` — prefer this for dashboard, tables, steppers, and multi-step product UI

**Project-specific rules**

* Still follow the approved design language: dark sidebar, light workspace, purple accent, rounded cards, minimal enterprise look.
* Prefer restrained product UI over experimental or brutalist directions.
* Do not override severity colors, source links, workflow stepper behavior, or other rules in `project-spec.md`.
* Pair with `frontend-design` and `web-design-guidelines`; Taste Skills guide aesthetics, those skills guide structure and accessibility.

**Optional related skills from the same package**

Install only when needed:

```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill redesign-existing-projects
npx skills add https://github.com/Leonxlnx/taste-skill --skill full-output-enforcement
```

* `redesign-existing-projects` — audit-first UI redesigns
* `full-output-enforcement` — reduce incomplete UI output and placeholders

Do not install conflicting directional skills (`industrial-brutalist-ui`, `high-end-visual-design`) unless the approved design language changes.

---

# 4. Testing and Debugging Skills

Install these before the AI pipeline becomes complex or before Phase 12.

## 4.1 Test-Driven Development

```bash
npx skills add https://github.com/obra/superpowers --skill test-driven-development
```

**Use for**

* Log classification
* Severity assignment
* RCA boundaries
* RAG grounding rules
* Jira decision logic
* Slack-after-Jira behavior
* Duplicate prevention
* API validation

**Priority test cases**

1. All incidents are returned regardless of severity.
2. Log Reader never creates Jira.
3. Log Reader never sends Slack.
4. RCA never recommends fixes.
5. Remediation recommendations require supporting documentation.
6. Missing documentation returns `No supporting documentation found`.
7. Critical incidents trigger automatic Jira.
8. Non-critical incidents require manual Jira action.
9. Slack is sent only after Jira succeeds.
10. Duplicate Jira tickets are prevented.
11. Duplicate Slack notifications are prevented.
12. Supporting source URLs appear in Jira.

---

## 4.2 Systematic Debugging

```bash
npx skills add https://github.com/obra/superpowers --skill systematic-debugging
```

**Use for**

* LangGraph state-transition errors
* FastAPI validation failures
* Clerk authentication failures
* LanceDB retrieval problems
* Confluence synchronization problems
* Google Drive ingestion problems
* Jira payload failures
* Slack notification failures
* Frontend/backend contract mismatches

**Required debugging process**

1. Reproduce the issue.
2. Capture the exact error.
3. Identify the failing layer.
4. Form one testable hypothesis.
5. Apply the smallest correction.
6. Re-run the affected tests.
7. Run regression tests.
8. Document the root cause.

**Do not**

* Make multiple unrelated changes at once.
* Disable validation to hide errors.
* Replace failing integrations with silent success responses.
* claim success without reproducing and verifying the fix.

---

## 4.3 Web Application Testing

```bash
npx skills add https://github.com/anthropics/skills --skill webapp-testing
```

**Use for**

* Frontend component testing
* API integration tests
* User-flow validation
* Loading states
* Error states
* Responsive UI checks
* Accessibility checks

**Required UI scenarios**

* User logs in.
* User uploads a valid log.
* Invalid file type is rejected.
* All incidents appear in the incident list.
* User selects an incident.
* RCA tab displays the diagnosis.
* Recommended Steps displays supporting sources.
* Source links open correctly.
* Cookbook displays commands, validation, and rollback.
* Critical incidents show automatic Jira and Slack statuses.
* Non-critical incidents show the Create Jira Ticket button.

---

## 4.4 Playwright Best Practices

Install before end-to-end testing if Playwright is selected.

```bash
npx skills add https://github.com/currents-dev/playwright-best-practices-skill --skill playwright-best-practices
```

**Use for**

* End-to-end demo validation
* Authentication flow
* Log-upload flow
* Incident-selection flow
* Tab navigation
* Manual Jira creation
* Critical automation-status validation

**Do not**

* Use browser tests as a replacement for backend unit tests.
* Call real Jira or Slack services in normal automated test runs.
* Depend on unstable production data.

---

# 5. Deployment Skills

## 5.1 Deploy to Vercel

Install before Phase 13 if the frontend will be deployed on Vercel.

```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel
```

**Use for**

* Vercel project configuration
* Frontend environment variables
* Preview deployments
* Production builds
* Deployment troubleshooting

**Project-specific rules**

* Only public frontend configuration may use `NEXT_PUBLIC_` variables.
* Backend secrets must remain in the backend deployment environment.
* The frontend must communicate with FastAPI through the configured backend URL.
* Verify CORS before the demo.
* Verify Clerk production-domain configuration before the demo.

---

# 6. Optional Skills

Install these only when necessary.

## 6.1 React Composition Patterns

```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-composition-patterns
```

Use when:

* Dashboard components become too large.
* Components receive too many boolean props.
* Shared recommendation, source, or incident components require reusable composition.

Do not install solely to introduce additional abstractions.

---

## 6.2 Parallel Agent Execution

```bash
npx skills add https://github.com/obra/superpowers --skill dispatching-parallel-agents
```

Use only when:

* Multiple independent workstreams are being implemented simultaneously.
* Frontend, backend, RAG, and integration work are clearly separated.
* Each agent has an explicitly defined folder and task scope.

Do not use when one developer or one Claude session is implementing sequentially.

---

## 6.3 Git Worktrees

```bash
npx skills add https://github.com/obra/superpowers --skill using-git-worktrees
```

Use only when:

* Multiple Claude Code sessions are working in parallel.
* Each session has a dedicated branch.
* Merge conflicts can be actively managed.

For a small hackathon team, normal feature branches are usually sufficient.

---

# 7. Skill Installation Stages

## Before Master Prompt

Install:

```text
find-skills
writing-plans
executing-plans
verification-before-completion
nextjs-app-router-patterns
vercel-react-best-practices
shadcn
frontend-design
web-design-guidelines
design-taste-frontend
minimalist-ui
```

## Before Phase 5 — Log Reader Agent

Install:

```text
test-driven-development
systematic-debugging
```

## Before Phase 12 — Testing

Install:

```text
webapp-testing
playwright-best-practices
```

## Before Phase 13 — Deployment

Install:

```text
deploy-to-vercel
```

---

# 8. Recommended Initial Installation Commands

```bash
npx skills add https://github.com/vercel-labs/skills --skill find-skills

npx skills add https://github.com/obra/superpowers --skill writing-plans

npx skills add https://github.com/obra/superpowers --skill executing-plans

npx skills add https://github.com/obra/superpowers --skill verification-before-completion

npx skills add https://github.com/wshobson/agents --skill nextjs-app-router-patterns

npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices

npx skills add https://github.com/shadcn/ui --skill shadcn

npx skills add https://github.com/anthropics/skills --skill frontend-design

npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines

npx skills add https://github.com/Leonxlnx/taste-skill --skill design-taste-frontend

npx skills add https://github.com/Leonxlnx/taste-skill --skill minimalist-ui
```

---

# 9. Later Installation Commands

## Before AI and integration-heavy phases

# ```bash
# npx skills add https://github.com/obra/superpowers --skill test-driven-development

# npx skills add https://github.com/obra/superpowers --skill systematic-debugging
# ```

## Before end-to-end testing

# ```bash
# npx skills add https://github.com/anthropics/skills --skill webapp-testing

# npx skills add https://github.com/currents-dev/playwright-best-practices-skill --skill playwright-best-practices
# ```

## Before frontend deployment

```bash
npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel
```

---

# 10. Technology Areas Requiring Official Documentation

A skill does not replace official documentation.

For these technologies, Claude Code must consult current official documentation when needed:

* FastAPI
* Pydantic
* LangGraph
* LangChain
* OpenAI API
* LanceDB
* Clerk
* Atlassian Confluence REST API
* Jira Cloud REST API
* Atlassian Document Format
* Google Drive API
* Slack API
* React Query
* Next.js
* Vercel
* Render or Railway

Claude must not install an unverified skill simply because it contains words such as:

* LangGraph
* Agentic AI
* RAG
* OpenAI
* LanceDB
* Jira
* Slack

The repository specification and official documentation take precedence.

---

# 11. Phase-to-Skill Mapping

| Phase                   | Primary Skills                                               |
| ----------------------- | ------------------------------------------------------------ |
| Repository Setup        | Writing Plans, Executing Plans                               |
| Phase 1: Bootstrap      | Next.js App Router Patterns, React Best Practices            |
| Phase 2: Authentication | Next.js App Router Patterns, Systematic Debugging            |
| Phase 3: Dashboard UI   | shadcn/ui, Frontend Design, Web Design Guidelines, Taste Skills |
| Phase 4: Log Upload     | React Best Practices, Test-Driven Development                |
| Phase 5: Log Reader     | Test-Driven Development, Systematic Debugging                |
| Phase 6: RAG Pipeline   | Writing Plans, Test-Driven Development, Systematic Debugging |
| Phase 7: RCA Agent      | Test-Driven Development, Verification Before Completion      |
| Phase 8: Remediation    | Test-Driven Development, Systematic Debugging                |
| Phase 9: Cookbook       | Test-Driven Development, Verification Before Completion      |
| Phase 10: Jira          | Systematic Debugging, Verification Before Completion         |
| Phase 11: Slack         | Systematic Debugging, Verification Before Completion         |
| Phase 12: Testing       | Web Application Testing, Playwright Best Practices           |
| Phase 13: Deployment    | Deploy to Vercel, Verification Before Completion             |

---

# 12. Claude Code Instruction

Use the following instruction at the start of the Claude Code session:

```text
Read SKILLS.md, docs/project-spec.md, and the relevant file under tasks/ before starting work.

Treat docs/project-spec.md as the architectural and functional source of truth.

Use SKILLS.md only to determine which implementation guidance is relevant to the current phase.

Do not allow skills to change approved business rules or agent responsibilities.

Implement one phase at a time.

Before editing files, state:
1. Current phase
2. Relevant skills
3. Files to create or modify
4. Acceptance criteria

After implementation, verify the result and report:
1. Completed work
2. Tests and commands executed
3. Acceptance criteria status
4. Known limitations
5. Suggested Git commit
```

---

# 13. Conflict Resolution Order

If instructions conflict, use this priority:

1. Explicit user instruction
2. `docs/project-spec.md`
3. Relevant `/tasks/phase-XX-*.md`
4. `SKILLS.md`
5. Installed skill guidance
6. Framework defaults
7. Claude-generated assumptions

Claude must request clarification only when a conflict materially prevents implementation. For small ambiguities, choose the simplest hackathon-friendly option and document the assumption.

---

# 14. Hackathon Guardrails

Skills must not cause the project to become unnecessarily complex.

Do not introduce unless explicitly approved:

* Kubernetes
* Kafka
* Microservices
* Service mesh
* Redis
* Multiple databases
* Complex event-driven architecture
* Enterprise observability platforms
* Multi-region deployment
* Full RBAC
* Multi-tenancy
* Automatic execution of generated commands
* Autonomous production remediation

Preferred approach:

* Next.js frontend
* FastAPI backend
* LangGraph orchestration
* LanceDB
* Local storage
* Mock integrations when credentials are unavailable
* Simple cloud deployment
* One reliable end-to-end demo path

---

# 15. Definition of Skill Success

The skill configuration is successful when:

* Claude follows the project specification.
* Phases remain isolated and manageable.
* Frontend components are consistent.
* Backend services remain modular.
* AI outputs use structured models.
* RAG recommendations remain source-grounded.
* Jira and Slack rules are preserved.
* Tests cover critical business rules.
* Claude verifies work before declaring completion.
* The application remains achievable within a hackathon timeline.

---

**End of SKILLS.md**
