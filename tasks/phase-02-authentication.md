# Phase 2 — Authentication

## Objective
Secure user access to the frontend using Clerk, and give the backend a modular way to verify who's calling it.

## Scope
- Clerk sign-in / sign-out flow.
- Session management via Clerk middleware.
- Display logged-in username in the header.
- Protect app routes behind authentication.
- Backend: pluggable auth-provider abstraction (Clerk / mock) validating bearer tokens.
- Backend: authenticated `GET /api/v1/me` returning a safe user identity object.
- No role-based access control (identity only).

## Dependencies
- Phase 1 (Project Bootstrap) — frontend and backend scaffolds must exist.

## Implementation Tasks
- Install and configure `@clerk/nextjs` (pinned to `6.35.6` — later 6.36+ narrows the React peer range and conflicts with the scaffolded React 19.1.0).
- Add `middleware.ts` using `clerkMiddleware` + `createRouteMatcher`, protecting all routes except `/sign-in` and `/sign-up`. (Renamed to `proxy.ts` during the later Next.js 16 upgrade — same behavior, new file convention.)
- Wrap the app in `<ClerkProvider>` in `app/layout.tsx`.
- Add `/sign-in` and `/sign-up` catch-all routes using Clerk's hosted components.
- Add `components/header.tsx`: shows a loading state while `useUser()` resolves, the username (or email/full name fallback) plus a sign-out button when signed in, and a sign-in link when signed out.
- Backend: `services/auth/base.py` (`AuthProvider` ABC + `AuthError`), `services/auth/clerk_provider.py` (verifies JWTs via Clerk's JWKS, then resolves profile via Clerk's Backend API), `services/auth/mock_provider.py` (fixed dev identity, any non-empty token), `services/auth/provider.py` (factory selecting the provider via `AUTH_PROVIDER` env var).
- Backend: `api/deps.py` (`get_current_user` FastAPI dependency using `HTTPBearer`), `api/me.py` (`GET /api/v1/me`), `models/user.py` (`UserIdentity`).
- Backend: `config/settings.py` loads the repo-root `.env` on startup.
- Add Clerk vars to `.env.example`: `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY`, `NEXT_PUBLIC_CLERK_SIGN_IN_URL`, `NEXT_PUBLIC_CLERK_SIGN_UP_URL`, `AUTH_PROVIDER`, `CLERK_JWKS_URL`.

## Deliverables
- Login page, logout action, username displayed when authenticated (frontend).
- Modular backend auth abstraction, mockable for local dev without a real Clerk instance.
- Authenticated `GET /api/v1/me` returning `{ id, email, username, full_name, image_url }`.

## Acceptance Criteria
- Unauthenticated users are redirected to sign-in (frontend middleware) and get `401` from `/api/v1/me` (backend).
- Authenticated users see their username and can sign out.
- Setting `AUTH_PROVIDER=mock` lets the backend run and be tested without any Clerk credentials.

## Definition of Done
- Frontend builds clean (`npm run build`).
- Backend `/health` and `/api/v1/me` verified locally in both `mock` and unconfigured `clerk` modes (the latter degrades to a clean `401`, not a crash).
- No Clerk secrets hardcoded or exposed to the client — only `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` reaches the browser bundle.

## Known Limitations / Follow-ups
- `ClerkAuthProvider` calls Clerk's Backend API on every request to resolve profile fields beyond the token's `sub` claim — fine for a hackathon, but should be cached or replaced with a custom Clerk JWT template for production.
- No automated tests yet (deferred to Phase 12 per the project plan).
- Real end-to-end verification requires a live Clerk test instance (publishable/secret keys + JWKS URL) — not exercised here since none was provided.

## Suggested Git Commit
`feat: integrate Clerk authentication`
