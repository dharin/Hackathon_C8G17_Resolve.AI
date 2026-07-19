# Phase 6 — RAG Pipeline

## Objective
Build the knowledge retrieval pipeline that later agents (Remediation) ground their answers in.

## Scope
- Ingestion from Confluence and Google Drive SOPs (use mock/local sample documents if live credentials are unavailable during the hackathon).
- Chunk → Embed → Store → Retrieve pipeline backed by LanceDB.
- Embedding via `BAAI/bge-small-en` or `nomic-embed-text` (configurable).
- Weekly incremental sync: check modified pages, re-chunk only those, update LanceDB — never a full re-index.

## Dependencies
- Phase 1 (backend scaffold). Independent of Phases 2–5 otherwise.

## Implementation Tasks
- `backend/rag/loaders.py`: Confluence + Google Drive loaders (mockable behind an interface so missing credentials degrade gracefully to sample docs).
- `backend/rag/chunker.py`, `backend/rag/embedder.py`, `backend/rag/store.py` (LanceDB).
- `backend/rag/sync.py`: incremental weekly sync job (modified-since check).
- `backend/config/`: RAG configuration (embedding model choice, chunk size, sources) exposed for the future "RAG Configuration" UI page.
- Add `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN`, `GOOGLE_DRIVE_CREDENTIALS` to `.env.example`.

## Deliverables
- Working ingest → embed → store → retrieve pipeline queryable from backend code.
- Incremental sync mechanism (can be triggered manually for demo purposes).

## Acceptance Criteria
- A sample SOP document can be ingested, embedded, and retrieved via similarity search.
- Re-running sync does not re-embed unmodified documents.

## Definition of Done
- Retrieval returns ranked, source-attributed chunks for a test query.

## Suggested Git Commit
`feat: implement RAG pipeline`
