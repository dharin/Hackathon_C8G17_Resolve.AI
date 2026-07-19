from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

SourceType = Literal["confluence", "local_sop"]


class KnowledgeDocument(BaseModel):
    """Canonical, source-agnostic document shape produced by every loader
    before normalization/chunking — see project-spec.md "Canonical Document
    Model".
    """

    document_id: str
    source_type: SourceType
    title: str
    content: str
    source_uri: str
    version: str
    content_hash: str
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """One chunk of a KnowledgeDocument, ready for embedding and storage."""

    chunk_id: str
    document_id: str
    source_type: SourceType
    title: str
    source_uri: str
    section_path: list[str] = Field(default_factory=list)
    chunk_index: int
    version: str
    content_hash: str
    content: str
    token_count: int
    updated_at: datetime | None = None
    indexed_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedChunk(BaseModel):
    """A ranked, source-attributed retrieval result returned to the
    Remediation/Cookbook agents. Never fabricated — grounded only in what
    was actually indexed.
    """

    chunk_id: str
    content: str
    score: float
    source_type: SourceType
    title: str
    source_uri: str
    section_path: list[str] = Field(default_factory=list)
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


SyncStatus = Literal["indexed", "unavailable", "failed"]


class DocumentSyncState(BaseModel):
    """Persisted per-document sync bookkeeping used to decide whether a
    document needs re-fetching/re-embedding on the next sync run.
    """

    document_id: str
    source_type: SourceType
    version: str
    source_uri: str
    content_hash: str
    last_discovered_at: datetime
    last_indexed_at: datetime | None = None
    status: SyncStatus = "indexed"
    last_error: str | None = None


class SourceSyncSummary(BaseModel):
    """Outcome of a single sync run for one source, returned by the manual
    sync trigger and logged for observability.
    """

    source_type: SourceType
    documents_discovered: int = 0
    documents_indexed: int = 0
    documents_skipped_unchanged: int = 0
    documents_marked_unavailable: int = 0
    documents_failed: int = 0
    errors: list[str] = Field(default_factory=list)
