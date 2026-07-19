# Phase 2 — Authentication

## Objective
Secure user access to the frontend using Clerk.

## Scope
- Clerk sign-in / sign-out flow.
- Session management via Clerk middleware.
- Display logged-in username in the header.
- Protect app routes behind authentication.

## Dependencies
- Phase 1 (Project Bootstrap) — frontend scaffold must exist.

## Implementation Tasks
- Install and configure `@clerk/nextjs`.
- Add `CLERK_SECRET_KEY` and `CLERK_PUBLISHABLE_KEY` to `.env.example`.
- Wrap app in `<ClerkProvider>`; add Clerk middleware for route protection.
- Add sign-in / sign-out UI entry points.
- Display current username in the dashboard header (placeholder until Phase 3 builds the real header).

## Deliverables
- Login page.
- Logout action.
- Username displayed when authenticated.

## Acceptance Criteria
- Unauthenticated users are redirected to sign-in.
- Authenticated users see their username and can log out.

## Definition of Done
- Auth flow works locally with a test Clerk instance.
- No Clerk secrets hardcoded — read from environment variables only.

## Suggested Git Commit
`feat: integrate Clerk authentication`
