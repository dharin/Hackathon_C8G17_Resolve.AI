# Phase 4 — Log Upload

## Objective
Allow engineers to upload application logs for analysis.

## Scope
- Frontend upload component (drag/drop or file picker) accepting `.txt` and `.log`.
- Client-side file validation (type, size limit for hackathon).
- Backend `POST /upload-log` endpoint that accepts the file and returns an `uploadId`.
- Local storage of uploaded files (hackathon scope — no cloud storage).

## Dependencies
- Phase 1 (backend scaffold), Phase 3 (dashboard shell to host the upload UI).

## Implementation Tasks
- Frontend: `features/upload` component + `services/` API client calling `POST /upload-log`.
- Backend: `api/upload.py` route, `models/log_issue.py` Pydantic model, local filesystem storage under a git-ignored directory.
- Validate file extension and size on both client and server; return user-friendly errors otherwise.
- Return `{ uploadId }` on success per project-spec.md's API Contracts.

## Deliverables
- Working upload flow from UI to backend, returning an `uploadId`.

## Acceptance Criteria
- Uploading a valid `.log`/`.txt` file succeeds and returns an `uploadId`.
- Invalid file types/oversized files are rejected with a clear message.

## Definition of Done
- End-to-end upload verified locally; uploaded files persisted to local storage, not committed to git.

## Suggested Git Commit
`feat: implement log upload`
