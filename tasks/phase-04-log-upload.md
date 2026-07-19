# Phase 4 — Log Upload

## Objective
Allow engineers to upload application logs for analysis.

## Scope
- Frontend upload component (drag/drop + file browser) accepting `.txt` and `.log`.
- Client-side validation (extension, configurable size limit), progress, duplicate-submission prevention, result display.
- Backend `POST /api/v1/logs/upload` endpoint that validates, stores, and returns upload metadata.
- Local storage of uploaded files (hackathon scope — no cloud storage).

## Dependencies
- Phase 1 (backend scaffold), Phase 2 (auth — the endpoint requires a valid bearer token), Phase 3 (dashboard shell to host the upload UI).

## API deviation from project-spec.md / original task file (explicitly instructed this turn)
The original spec listed `POST /upload-log` returning `{ uploadId }`. This phase was implemented against a revised, more explicit contract given directly this turn:

- **Route**: `POST /api/v1/logs/upload` (not `/upload-log`), consistent with the `/api/v1` prefix already used by `/api/v1/me`.
- **Response**: `{ upload_id, file_name, size_bytes, status }` (snake_case, richer metadata) instead of `{ uploadId }`.

## Implementation Tasks
- Backend: `config/settings.py` — added `UPLOAD_DIR` (`backend/uploads/`, git-ignored), `ALLOWED_LOG_EXTENSIONS`, `MAX_UPLOAD_SIZE_BYTES` (from `MAX_UPLOAD_SIZE_MB` env var, default 10 MB).
- Backend: `models/log_upload.py` — `LogUploadResult`.
- Backend: `services/upload_service.py` — `save_log_upload()`: validates extension, streams the file to disk in 1 MB chunks enforcing the size limit *while reading* (doesn't trust the client-sent `Content-Length`), rejects empty files, deletes any partial file on rejection. Storage path is built entirely from a server-generated UUID + an allowlisted extension — the original file name is never used to construct a path, so there's no path-traversal surface. Content is only ever written as raw bytes, never parsed/executed/interpreted.
- Backend: `api/upload.py` — `POST /api/v1/logs/upload`, requires auth via the existing `get_current_user` dependency (Phase 2), translates `UploadValidationError` into the right HTTP status (400/413/415).
- Backend: `requirements.txt` — added `python-multipart` (required by FastAPI for `UploadFile`/form parsing).
- Frontend: `lib/upload-config.ts` — shared constants (allowed extensions, max size from `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB`, API base URL from `NEXT_PUBLIC_API_BASE_URL`), `formatBytes`.
- Frontend: `services/upload-service.ts` — `uploadLogFile()` using `XMLHttpRequest` (needed for real upload-progress events, which `fetch` doesn't expose), returns `{ promise, abort }`.
- Frontend: `features/upload/upload-panel.tsx` — drag/drop zone + click-to-browse, client-side validation mirroring the backend, progress bar, disables the drop zone entirely while `status === "uploading"` (prevents duplicate submissions from double-drop/double-click), success state requires an explicit "Upload another file" click before a new file can be selected, error state shows the server's `detail` message with a "Try again" action. Auth token obtained via Clerk's `useAuth().getToken()`.
- Frontend: `app/(dashboard)/upload-logs/page.tsx` — wires `UploadPanel` into the sidebar's existing "Upload Logs" nav entry (previously a dead link).
- `.env.example` — added `NEXT_PUBLIC_API_BASE_URL`, `MAX_UPLOAD_SIZE_MB`, `NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB`.

## Deliverables
- Working upload flow from UI to backend, returning `{ upload_id, file_name, size_bytes, status }`.

## Acceptance Criteria
- Uploading a valid `.log`/`.txt` file succeeds and returns upload metadata. Verified via `curl -F` against the backend directly (200, correct JSON).
- Invalid file types rejected with a clear message (415). Verified.
- Oversized files rejected (413) with no partial file left on disk. Verified (tested with a 1 MB limit against a 2 MB file).
- Empty files rejected (400). Verified.
- Missing/invalid auth rejected (401). Verified.

## Definition of Done
- Backend behaviors verified end-to-end via `curl` (valid upload, bad extension, oversized, empty, unauthenticated).
- Frontend `npm run build` passes clean (typecheck + lint), including the new `/upload-logs` route.
- Uploaded files persist to `backend/uploads/`, which is git-ignored.

## Known Limitations / Follow-ups
- No in-browser interaction test (drag/drop, progress bar animation, duplicate-click prevention) was performed — no headless-browser driver was available in this environment. Verified by code review + backend-level `curl` testing instead. Recommend a manual click-through before the demo.
- No agent analysis is triggered on upload, as instructed — the result is purely storage + metadata. Phase 5 (Log Reader Agent) consumes `upload_id` next.
- The 401 path (missing/invalid Clerk token from the browser) hasn't been tested against a real signed-in session — only via `curl` with a mock-mode token.

## Suggested Git Commit
`feat: implement log upload`
