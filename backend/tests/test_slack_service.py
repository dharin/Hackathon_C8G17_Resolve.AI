from datetime import datetime, timezone
from pathlib import Path

import pytest

from integrations.slack import SlackError
from models.issue_category import IssueCategory
from models.jira_ticket import JiraTicketReference
from models.log_issue import LogIssue
from models.severity import Severity
from services import slack_notification_store, slack_service


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        slack_notification_store, "SLACK_NOTIFICATIONS_DB_PATH", tmp_path / "slack_notifications.sqlite3"
    )


def make_incident(**overrides) -> LogIssue:
    defaults = dict(
        id="incident-1",
        category=IssueCategory.DATABASE_CONNECTION_ERROR,
        severity=Severity.CRITICAL,
        title="Database connections exhausted",
        service="checkout-api",
        confidence=0.9,
    )
    defaults.update(overrides)
    return LogIssue(**defaults)


def make_jira_ticket(**overrides) -> JiraTicketReference:
    defaults = dict(
        key="OPS-1",
        url="https://example.atlassian.net/browse/OPS-1",
        created_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return JiraTicketReference(**defaults)


class _FakeConfiguredClient:
    def __init__(self):
        self.is_configured = True
        self.calls = 0

    def post_incident_notification(self, incident, jira_ticket):
        self.calls += 1
        return "C123", "1700000000.000100", "https://x.slack.com/archives/C123/p1"


class _FakeUnconfiguredClient:
    is_configured = False

    def post_incident_notification(self, incident, jira_ticket):
        raise AssertionError("should never be called when unconfigured")


class _FakeFailingClient:
    is_configured = True

    def post_incident_notification(self, incident, jira_ticket):
        raise SlackError("boom")


def test_ensure_notification_returns_none_for_non_critical_incident(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(slack_service, "SlackClient", lambda: fake)
    result = slack_service.ensure_notification("a1", make_incident(severity=Severity.HIGH), make_jira_ticket())
    assert result is None
    assert fake.calls == 0


def test_ensure_notification_returns_none_without_jira_ticket(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(slack_service, "SlackClient", lambda: fake)
    assert slack_service.ensure_notification("a1", make_incident(), None) is None
    assert fake.calls == 0


def test_ensure_notification_returns_none_when_unconfigured(monkeypatch):
    monkeypatch.setattr(slack_service, "SlackClient", lambda: _FakeUnconfiguredClient())
    assert slack_service.ensure_notification("a1", make_incident(), make_jira_ticket()) is None


def test_ensure_notification_sends_when_critical_and_configured(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(slack_service, "SlackClient", lambda: fake)

    result = slack_service.ensure_notification("a1", make_incident(), make_jira_ticket())

    assert result is not None
    assert result.channel_id == "C123"
    assert fake.calls == 1


def test_ensure_notification_is_idempotent(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(slack_service, "SlackClient", lambda: fake)

    first = slack_service.ensure_notification("a1", make_incident(), make_jira_ticket())
    second = slack_service.ensure_notification("a1", make_incident(), make_jira_ticket())

    assert first == second
    assert fake.calls == 1


def test_ensure_notification_swallows_slack_error(monkeypatch):
    monkeypatch.setattr(slack_service, "SlackClient", lambda: _FakeFailingClient())
    assert slack_service.ensure_notification("a1", make_incident(), make_jira_ticket()) is None


def test_notify_or_raise_raises_value_error_for_non_critical(monkeypatch):
    monkeypatch.setattr(slack_service, "SlackClient", lambda: _FakeConfiguredClient())
    with pytest.raises(ValueError):
        slack_service.notify_or_raise("a1", make_incident(severity=Severity.LOW), make_jira_ticket())


def test_notify_or_raise_raises_value_error_without_jira_ticket(monkeypatch):
    monkeypatch.setattr(slack_service, "SlackClient", lambda: _FakeConfiguredClient())
    with pytest.raises(ValueError):
        slack_service.notify_or_raise("a1", make_incident(), None)


def test_notify_or_raise_propagates_slack_error(monkeypatch):
    monkeypatch.setattr(slack_service, "SlackClient", lambda: _FakeFailingClient())
    with pytest.raises(SlackError):
        slack_service.notify_or_raise("a1", make_incident(), make_jira_ticket())


def test_notify_or_raise_is_idempotent(monkeypatch):
    fake = _FakeConfiguredClient()
    monkeypatch.setattr(slack_service, "SlackClient", lambda: fake)

    first = slack_service.notify_or_raise("a1", make_incident(), make_jira_ticket())
    second = slack_service.notify_or_raise("a1", make_incident(), make_jira_ticket())

    assert first == second
    assert fake.calls == 1
