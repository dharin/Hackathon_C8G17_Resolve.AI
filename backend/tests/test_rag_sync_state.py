from datetime import datetime, timezone
from pathlib import Path

from rag.models import DocumentSyncState
from rag.sync_state import SyncStateStore


def make_state(**overrides) -> DocumentSyncState:
    defaults = dict(
        document_id="local-sop:a.md",
        source_type="local_sop",
        version="v1",
        source_uri="a.md",
        content_hash="hash1",
        last_discovered_at=datetime.now(timezone.utc),
        last_indexed_at=datetime.now(timezone.utc),
        status="indexed",
        last_error=None,
    )
    defaults.update(overrides)
    return DocumentSyncState(**defaults)


def test_upsert_and_get_round_trips(tmp_path: Path):
    store = SyncStateStore(tmp_path / "sync.sqlite3")
    state = make_state()
    store.upsert(state)

    loaded = store.get(state.document_id)
    assert loaded is not None
    assert loaded.content_hash == "hash1"
    assert loaded.status == "indexed"


def test_upsert_overwrites_existing_row(tmp_path: Path):
    store = SyncStateStore(tmp_path / "sync.sqlite3")
    store.upsert(make_state(content_hash="hash1"))
    store.upsert(make_state(content_hash="hash2"))

    loaded = store.get("local-sop:a.md")
    assert loaded.content_hash == "hash2"


def test_state_survives_reopening_the_store(tmp_path: Path):
    db_path = tmp_path / "sync.sqlite3"
    SyncStateStore(db_path).upsert(make_state())

    reopened = SyncStateStore(db_path)
    loaded = reopened.get("local-sop:a.md")
    assert loaded is not None
    assert loaded.content_hash == "hash1"


def test_mark_unavailable(tmp_path: Path):
    store = SyncStateStore(tmp_path / "sync.sqlite3")
    store.upsert(make_state())
    store.mark_unavailable("local-sop:a.md")

    loaded = store.get("local-sop:a.md")
    assert loaded.status == "unavailable"


def test_all_for_source_filters_by_source_type(tmp_path: Path):
    store = SyncStateStore(tmp_path / "sync.sqlite3")
    store.upsert(make_state(document_id="local-sop:a.md", source_type="local_sop"))
    store.upsert(make_state(document_id="confluence:1", source_type="confluence"))

    local_only = store.all_for_source("local_sop")
    assert [s.document_id for s in local_only] == ["local-sop:a.md"]


def test_get_missing_document_returns_none(tmp_path: Path):
    store = SyncStateStore(tmp_path / "sync.sqlite3")
    assert store.get("does-not-exist") is None
