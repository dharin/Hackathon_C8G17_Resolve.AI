from datetime import datetime

from pydantic import BaseModel, Field

from rag.models import SourceSyncSummary


class RagSyncStatus(BaseModel):
    """Response for `GET /api/v1/rag/status` — read on page load so the
    "Update Knowledgebase" button can show the last successful sync date
    without requiring a sync to have run in the current session.
    """

    last_synced_at: datetime | None = None


class RagSyncResult(BaseModel):
    """Response for `POST /api/v1/rag/sync`. `last_synced_at` reflects the
    persisted timestamp after this run — if any source failed outright,
    that timestamp is left at its previous value (see api/rag.py), so the
    UI can "roll back" to it rather than display a stale success.
    """

    summaries: list[SourceSyncSummary]
    last_synced_at: datetime | None = None
    errors: list[str] = Field(default_factory=list)
