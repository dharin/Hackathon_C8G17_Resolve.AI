from datetime import datetime, timezone
from pathlib import Path

import pytest

from services import rag_sync_meta_store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(rag_sync_meta_store, "RAG_SYNC_META_DB_PATH", tmp_path / "rag_sync_meta.sqlite3")


def test_get_last_synced_at_returns_none_when_never_synced():
    assert rag_sync_meta_store.get_last_synced_at() is None


def test_set_and_get_round_trips():
    value = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rag_sync_meta_store.set_last_synced_at(value)
    assert rag_sync_meta_store.get_last_synced_at() == value


def test_set_without_argument_defaults_to_now():
    before = datetime.now(timezone.utc)
    returned = rag_sync_meta_store.set_last_synced_at()
    after = datetime.now(timezone.utc)
    assert before <= returned <= after
    assert rag_sync_meta_store.get_last_synced_at() == returned


def test_set_overwrites_previous_value():
    first = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second = datetime(2026, 2, 1, tzinfo=timezone.utc)
    rag_sync_meta_store.set_last_synced_at(first)
    rag_sync_meta_store.set_last_synced_at(second)
    assert rag_sync_meta_store.get_last_synced_at() == second
