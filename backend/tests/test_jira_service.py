from pathlib import Path

import pytest

from integrations.jira import JiraError
from models.jira_payload import JiraPayload
from services import jira_service, jira_ticket_store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(jira_ticket_store, "JIRA_TICKETS_DB_PATH", tmp_path / "jira_tickets.sqlite3")


def make_payload(**overrides) -> JiraPayload:
    defaults = dict(
        incident_id="incident-1",
        summary="Database connections exhausted",
        description="The database exhausted its connection pool.",
        priority="Highest",
        labels=["database_connection_error"],
    )
    defaults.update(overrides)
    return JiraPayload(**defaults)


class _FakeConfiguredClient:
    def __init__(self, key="OPS-1", url="https://x/browse/OPS-1"):
        self.is_configured = True
        self._key = key
        self._url = url
        self.calls = 0

    def create_issue(self, payload):
        self.calls += 1
        return self._key, self._url


class _FakeUnconfiguredClient:
    is_configured = False

    def create_issue(self, payload):
        raise AssertionError("should never be called when unconfigured")


class _FakeFailingClient:
    is_configured = True

    def create_issue(self, payload):
        raise JiraError("boom")


def test_ensure_ticket_returns_none_without_payload_or_config(monkeypatch):
    monkeypatch.setattr(jira_service, "JiraClient", lambda: _FakeUnconfiguredClient())
    assert jira_service.ensure_ticket("a1", "i1", None) is None
    assert jira_service.ensure_ticket("a1", "i1", make_payload()) is None


def test_ensure_ticket_creates_when_configured_and_payload_present(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(jira_service, "JiraClient", lambda: fake)

    ticket = jira_service.ensure_ticket("a1", "i1", make_payload())

    assert ticket is not None
    assert ticket.key == "OPS-1"
    assert fake.calls == 1


def test_ensure_ticket_is_idempotent(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(jira_service, "JiraClient", lambda: fake)

    first = jira_service.ensure_ticket("a1", "i1", make_payload())
    second = jira_service.ensure_ticket("a1", "i1", make_payload())

    assert first == second
    assert fake.calls == 1  # second call found the existing ticket, never hit Jira again


def test_ensure_ticket_swallows_jira_error(monkeypatch):
    monkeypatch.setattr(jira_service, "JiraClient", lambda: _FakeFailingClient())
    assert jira_service.ensure_ticket("a1", "i1", make_payload()) is None


def test_create_ticket_or_raise_raises_value_error_without_payload(monkeypatch):
    monkeypatch.setattr(jira_service, "JiraClient", lambda: _FakeConfiguredClient())
    with pytest.raises(ValueError):
        jira_service.create_ticket_or_raise("a1", "i1", None)


def test_create_ticket_or_raise_propagates_jira_error(monkeypatch):
    monkeypatch.setattr(jira_service, "JiraClient", lambda: _FakeFailingClient())
    with pytest.raises(JiraError):
        jira_service.create_ticket_or_raise("a1", "i1", make_payload())


def test_create_ticket_or_raise_is_idempotent(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(jira_service, "JiraClient", lambda: fake)

    first = jira_service.create_ticket_or_raise("a1", "i1", make_payload())
    second = jira_service.create_ticket_or_raise("a1", "i1", make_payload())

    assert first == second
    assert fake.calls == 1
