import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from rag.models import DocumentSyncState

_SCHEMA = """
CREATE TABLE IF NOT EXISTS document_sync_state (
    document_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    version TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    last_discovered_at TEXT NOT NULL,
    last_indexed_at TEXT,
    status TEXT NOT NULL,
    last_error TEXT
);
"""


class SyncStateStore:
    """Persists per-document sync bookkeeping in SQLite so incremental sync
    survives a backend restart (project-spec.md "Incremental
    Synchronization" / "Sync state").
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def get(self, document_id: str) -> DocumentSyncState | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM document_sync_state WHERE document_id = ?", (document_id,)
            ).fetchone()
        return _row_to_state(row) if row else None

    def all_for_source(self, source_type: str) -> list[DocumentSyncState]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM document_sync_state WHERE source_type = ?", (source_type,)
            ).fetchall()
        return [_row_to_state(row) for row in rows]

    def upsert(self, state: DocumentSyncState) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO document_sync_state (
                    document_id, source_type, version, source_uri, content_hash,
                    last_discovered_at, last_indexed_at, status, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    source_type=excluded.source_type,
                    version=excluded.version,
                    source_uri=excluded.source_uri,
                    content_hash=excluded.content_hash,
                    last_discovered_at=excluded.last_discovered_at,
                    last_indexed_at=excluded.last_indexed_at,
                    status=excluded.status,
                    last_error=excluded.last_error
                """,
                (
                    state.document_id,
                    state.source_type,
                    state.version,
                    state.source_uri,
                    state.content_hash,
                    state.last_discovered_at.isoformat(),
                    state.last_indexed_at.isoformat() if state.last_indexed_at else None,
                    state.status,
                    state.last_error,
                ),
            )

    def mark_unavailable(self, document_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE document_sync_state SET status = 'unavailable' WHERE document_id = ?",
                (document_id,),
            )

    def delete(self, document_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM document_sync_state WHERE document_id = ?", (document_id,))


def _row_to_state(row: sqlite3.Row) -> DocumentSyncState:
    return DocumentSyncState(
        document_id=row["document_id"],
        source_type=row["source_type"],
        version=row["version"],
        source_uri=row["source_uri"],
        content_hash=row["content_hash"],
        last_discovered_at=datetime.fromisoformat(row["last_discovered_at"]),
        last_indexed_at=datetime.fromisoformat(row["last_indexed_at"]) if row["last_indexed_at"] else None,
        status=row["status"],
        last_error=row["last_error"],
    )
