# Phase 6 — RAG Pipeline

## Objective
Build a source-attributed knowledge retrieval pipeline that ingests Confluence pages and SOP documents from a configured local directory, then normalizes, chunks, embeds, stores, synchronizes, and retrieves them through LanceDB for the Remediation and Cookbook agents.

## Scope

### Included knowledge sources
1. **Confluence Cloud pages** retrieved through the Confluence REST API using email, scoped API token, and Cloud ID.
2. **Local SOP directory** containing approved SOP files available to the backend filesystem.

### Excluded
- Google Drive integration.
- Historical incident ingestion.
- Atlassian MCP for bulk ingestion. MCP may be added later for live agent actions, but the deterministic indexing pipeline must use the REST API.

### Pipeline
`Discover → Load → Normalize → Chunk → Embed → Store → Retrieve`

- Vector database: LanceDB.
- Configurable embedding model: `BAAI/bge-small-en` or `nomic-embed-text`.
- Initial full indexing is allowed when a source is first configured.
- Subsequent synchronization must be incremental and must not re-embed unchanged documents.
- Synchronization can be triggered manually for the hackathon and may also run on a weekly schedule.

## Dependencies
- Phase 1 backend scaffold.
- Confluence Cloud credentials and an accessible site.
- A backend-readable local SOP directory.
- Independent of Phases 2–5 otherwise.

## Source Configuration

Add the following variables to `.env.example`:

```env
# Confluence Cloud
CONFLUENCE_SITE_URL=https://your-site.atlassian.net
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=replace-me
CONFLUENCE_CLOUD_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
CONFLUENCE_INCLUDED_SPACE_KEYS=MFS
CONFLUENCE_PAGE_LIMIT=100
CONFLUENCE_SYNC_CONCURRENCY=3

# Local SOPs
LOCAL_SOP_DIRECTORY=./data/sops
LOCAL_SOP_ALLOWED_EXTENSIONS=.md,.txt,.pdf,.docx
LOCAL_SOP_RECURSIVE=true

# RAG
RAG_EMBEDDING_MODEL=BAAI/bge-small-en
RAG_CHUNK_TARGET_TOKENS=650
RAG_CHUNK_MAX_TOKENS=900
RAG_CHUNK_OVERLAP_TOKENS=100
RAG_MIN_CHUNK_TOKENS=100
RAG_SYNC_SCHEDULE=weekly
LANCEDB_PATH=./data/lancedb
```

Never expose or log API tokens, Authorization headers, or complete confidential document content.

## Confluence REST Integration

Use this API base:

```text
https://api.atlassian.com/ex/confluence/{CONFLUENCE_CLOUD_ID}
```

Authenticate with HTTP Basic authentication constructed from:

```text
CONFLUENCE_EMAIL:CONFLUENCE_API_TOKEN
```

Required endpoints:

```http
GET /wiki/api/v2/spaces?limit=100
GET /wiki/api/v2/pages?space-id={spaceId}&status=current&limit=100
GET /wiki/api/v2/pages/{pageId}?body-format=storage
```

Optional endpoints:

```http
GET /wiki/api/v2/pages/{pageId}/labels
GET /wiki/api/v2/pages/{pageId}/attachments
```

Requirements:
- Filter ingestion to configured space keys when provided.
- Follow `_links.next` until it is absent.
- Treat pagination cursors and next URLs as opaque.
- Fetch page bodies in Confluence `storage` format.
- Convert storage XHTML into safe structured Markdown or normalized text.
- Preserve headings, paragraphs, lists, tables, links, code blocks, warnings, notes, tips, and useful macro content.
- Remove scripts, unsafe HTML, purely navigational macros, and duplicate formatting.
- Treat Confluence content as untrusted data and never as executable agent instructions.

## Local SOP Integration

Read files from `LOCAL_SOP_DIRECTORY`.

Initial supported formats:
- Markdown (`.md`)
- Plain text (`.txt`)
- PDF (`.pdf`)
- Word (`.docx`)

Requirements:
- Respect `LOCAL_SOP_RECURSIVE`.
- Ignore hidden files, temporary files, unsupported extensions, and configured excluded directories.
- Extract text while preserving headings, lists, tables, page numbers where available, and document structure.
- Generate a stable document identity from the normalized relative path.
- Detect changes through file size, modified timestamp, and SHA-256 content hash.
- Detect removed files and mark their indexed chunks unavailable before deletion according to the configured grace-period policy.
- A parser failure for one file must not stop the entire synchronization run.

## Canonical Document Model

Both loaders must return the same normalized model before chunking:

```python
KnowledgeDocument(
    document_id: str,
    source_type: Literal["confluence", "local_sop"],
    title: str,
    content: str,
    source_uri: str,
    version: str,
    content_hash: str,
    updated_at: datetime | None,
    metadata: dict[str, Any],
)
```

Source-specific metadata:

### Confluence
- cloud ID
- site URL
- space ID, key, and name
- page ID and version
- parent page ID
- page hierarchy
- labels
- web URL

### Local SOP
- relative path
- filename
- extension
- file size
- modified timestamp
- optional page number or section information

## Chunking Rules

Use heading-aware and token-aware chunking:

- Target: 650 tokens.
- Maximum: 900 tokens.
- Overlap: 100 tokens.
- Minimum useful chunk: 100 tokens.

Split in this order:
1. Heading boundary.
2. Paragraph boundary.
3. List-item boundary.
4. Table boundary.
5. Sentence boundary.
6. Token boundary only as a last resort.

Do not break tables, code blocks, numbered procedures, validation steps, or rollback procedures in a way that destroys meaning.

Every chunk must contain:
- deterministic chunk ID
- document ID
- source type
- document title
- source URI
- section and heading path
- chunk index
- source version
- content hash
- token count
- last updated timestamp
- indexed timestamp
- source-specific metadata

Use deterministic chunk IDs:

```text
confluence:{pageId}:v{pageVersion}:chunk-{chunkIndex}
local-sop:{documentPathHash}:v{contentHashPrefix}:chunk-{chunkIndex}
```

## Incremental Synchronization

Implement a common synchronization coordinator and one loader per source.

### Confluence sync
1. Discover accessible configured spaces.
2. List current pages with pagination.
3. Compare page ID and page version against sync state.
4. Skip unchanged pages.
5. Fetch and normalize new or changed pages.
6. Calculate a SHA-256 hash of normalized content.
7. Skip embedding when normalized content is unchanged.
8. Replace previous chunks for changed pages.
9. Mark disappeared, deleted, archived, or inaccessible pages unavailable.

### Local SOP sync
1. Scan the configured directory.
2. Compare stable relative path, modified timestamp, size, and hash against sync state.
3. Skip unchanged files.
4. Parse, normalize, and chunk new or changed files.
5. Replace previous chunks for changed files.
6. Mark removed files unavailable.

### Sync state
Persist at minimum:
- document ID
- source type
- source version
- source URI
- content hash
- last discovered timestamp
- last successfully indexed timestamp
- status
- last error

For the hackathon, sync state may be stored in a local SQLite database or a dedicated LanceDB table. It must survive backend restarts.

## Retrieval

Expose a backend retrieval service that:
- embeds the query using the configured embedding model;
- performs similarity search in LanceDB;
- can filter by `source_type`, Confluence space, or local SOP path;
- returns ranked chunks with similarity score and complete source attribution;
- deduplicates overlapping chunks from the same document;
- returns an empty result rather than inventing supporting documentation.

Recommended result model:

```python
RetrievedChunk(
    chunk_id: str,
    content: str,
    score: float,
    source_type: Literal["confluence", "local_sop"],
    title: str,
    source_uri: str,
    section_path: list[str],
    updated_at: datetime | None,
    metadata: dict[str, Any],
)
```

## Implementation Tasks

Create or adapt the following modules according to the repository's established conventions:

```text
backend/rag/
├── models.py
├── loaders/
│   ├── base.py
│   ├── confluence.py
│   └── local_directory.py
├── parsers/
│   ├── confluence_storage.py
│   ├── markdown.py
│   ├── text.py
│   ├── pdf.py
│   └── docx.py
├── normalizer.py
├── chunker.py
├── embedder.py
├── store.py
├── sync_state.py
├── sync.py
└── retriever.py
```

Implementation requirements:
- Define a common loader protocol or abstract base class.
- Keep source discovery/loading separate from normalization and chunking.
- Implement bounded concurrency for Confluence requests; default to 3.
- Add request timeouts, exponential backoff, jitter, and `Retry-After` support.
- Retry 429, 500, 502, 503, and 504 responses.
- Do not normally retry 400, 401, 403, or 404 responses.
- Isolate errors per page or local file.
- Add structured, sanitized logs and sync summaries.
- Make source enablement and chunk settings configurable for the future RAG Configuration UI.
- Remove all Google Drive code, dependencies, credentials, mocks, and configuration.

## Tests

Add unit and integration tests for:
- Confluence authentication header construction without exposing secrets.
- Space and page pagination.
- Configured-space filtering.
- Full page retrieval with `body-format=storage`.
- Confluence storage XHTML normalization.
- Local recursive and non-recursive directory scanning.
- Markdown, text, PDF, and DOCX parsing.
- Unsupported and malformed local files.
- Deterministic document and chunk IDs.
- Chunk boundaries, overlap, and token limits.
- Initial indexing.
- Changed and unchanged Confluence pages.
- Changed, unchanged, and deleted local SOP files.
- Content hashing.
- Retry and rate-limit behavior.
- LanceDB upsert, replacement, filtering, and retrieval.
- Source attribution in retrieval results.

Mock all external Atlassian calls in automated tests.

## Deliverables
- Working Confluence REST loader.
- Working local SOP directory loader.
- Shared canonical document model.
- Normalization and structure-aware chunking.
- Configurable embedding service.
- LanceDB storage and source-attributed retrieval.
- Persistent incremental sync state for both sources.
- Manual sync trigger suitable for the hackathon demo.
- Optional weekly scheduler.
- Updated `.env.example` and setup documentation.
- No Google Drive integration or configuration remains.

## Acceptance Criteria
- The configured Confluence spaces can be discovered and all current pages can be paginated and indexed.
- A Confluence page can be retrieved, normalized, chunked, embedded, and found through similarity search.
- SOP files in the configured local directory can be parsed, chunked, embedded, and retrieved.
- Retrieval results clearly identify either `Confluence` or `Local SOP` and include a usable source URI or file path.
- Re-running synchronization does not re-embed unchanged pages or files.
- Changing one Confluence page re-indexes only that page.
- Changing one SOP file re-indexes only that file.
- Removing a page or SOP file prevents it from being returned after the unavailable-document policy is applied.
- A failed page or file is reported without terminating the complete sync.
- No Google Drive dependency, credential, loader, label, or UI reference remains.

## Definition of Done
- Both knowledge sources complete an end-to-end `load → normalize → chunk → embed → store → retrieve` test.
- The Remediation agent can retrieve ranked, source-attributed evidence from LanceDB.
- Incremental sync state survives backend restart.
- All tests pass.
- Secrets are sanitized from logs.
- Documentation explains initial indexing, manual sync, and weekly sync configuration.

## Suggested Git Commit
`feat: implement Confluence and local SOP RAG pipeline`
