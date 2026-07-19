from pathlib import Path

import pytest

from services import jira_ticket_store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(jira_ticket_store, "JIRA_TICKETS_DB_PATH", tmp_path / "jira_tickets.sqlite3")


def test_get_missing_ticket_returns_none():
    assert jira_ticket_store.get_ticket("analysis-1", "incident-1") is None


def test_save_and_get_ticket_round_trips():
    saved = jira_ticket_store.save_ticket("analysis-1", "incident-1", "OPS-1", "https://x/browse/OPS-1")
    loaded = jira_ticket_store.get_ticket("analysis-1", "incident-1")

    assert loaded is not None
    assert loaded.key == "OPS-1"
    assert loaded.url == "https://x/browse/OPS-1"
    assert loaded.created_at == saved.created_at


def test_save_ticket_upserts_rather_than_duplicating():
    jira_ticket_store.save_ticket("analysis-1", "incident-1", "OPS-1", "https://x/browse/OPS-1")
    jira_ticket_store.save_ticket("analysis-1", "incident-1", "OPS-2", "https://x/browse/OPS-2")

    loaded = jira_ticket_store.get_ticket("analysis-1", "incident-1")
    assert loaded.key == "OPS-2"


def test_tickets_are_scoped_per_analysis_and_incident():
    jira_ticket_store.save_ticket("analysis-1", "incident-1", "OPS-1", "https://x/browse/OPS-1")
    assert jira_ticket_store.get_ticket("analysis-2", "incident-1") is None
    assert jira_ticket_store.get_ticket("analysis-1", "incident-2") is None
