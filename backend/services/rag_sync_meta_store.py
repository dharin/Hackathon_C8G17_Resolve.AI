import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config.settings import RAG_SYNC_META_DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS rag_sync_meta (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    last_synced_at TEXT NOT NULL
);
"""

# Single-row table: only ever tracks the last successful full sync
# completion time, nothing else. Kept separate from rag/sync_state.py's
# per-document incremental sync bookkeeping.


@contextmanager
def _connect():
    path: Path = RAG_SYNC_META_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_last_synced_at() -> datetime | None:
    with _connect() as conn:
        row = conn.execute("SELECT last_synced_at FROM rag_sync_meta WHERE id = 1").fetchone()
    return datetime.fromisoformat(row[0]) if row else None


def set_last_synced_at(value: datetime | None = None) -> datetime:
    value = value or datetime.now(timezone.utc)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO rag_sync_meta (id, last_synced_at) VALUES (1, ?) "
            "ON CONFLICT(id) DO UPDATE SET last_synced_at = excluded.last_synced_at",
            (value.isoformat(),),
        )
    return value
