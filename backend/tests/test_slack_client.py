from datetime import datetime, timezone

import httpx
import pytest

from integrations.slack import SlackClient, SlackError
from models.jira_ticket import JiraTicketReference
from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.severity import Severity


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


def make_client(handler) -> SlackClient:
    client = SlackClient(bot_token="xoxb-fake-token", channel_id="C123")
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    return client


def test_is_configured_false_when_token_or_channel_missing():
    assert SlackClient(bot_token="", channel_id="C123").is_configured is False
    assert SlackClient(bot_token="xoxb-fake", channel_id="").is_configured is False


def test_post_incident_notification_raises_when_not_configured():
    client = SlackClient(bot_token="", channel_id="")
    with pytest.raises(SlackError):
        client.post_incident_notification(make_incident(), make_jira_ticket())


def test_post_incident_notification_sends_expected_message_and_returns_ts():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if "chat.postMessage" in str(request.url):
            captured["body"] = request.read()
            return httpx.Response(200, json={"ok": True, "channel": "C123", "ts": "1700000000.000100"})
        if "chat.getPermalink" in str(request.url):
            return httpx.Response(
                200, json={"ok": True, "permalink": "https://x.slack.com/archives/C123/p1700000000000100"}
            )
        return httpx.Response(404)

    client = make_client(handler)
    channel, ts, permalink = client.post_incident_notification(make_incident(), make_jira_ticket())

    assert channel == "C123"
    assert ts == "1700000000.000100"
    assert permalink == "https://x.slack.com/archives/C123/p1700000000000100"

    import json

    body = json.loads(captured["body"])
    assert body["channel"] == "C123"
    assert "Database connections exhausted" in body["text"]
    assert "OPS-1" in body["text"]


def test_post_incident_notification_raises_on_slack_level_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": False, "error": "channel_not_found"})

    client = make_client(handler)
    with pytest.raises(SlackError):
        client.post_incident_notification(make_incident(), make_jira_ticket())


def test_missing_permalink_does_not_block_notification():
    def handler(request: httpx.Request) -> httpx.Response:
        if "chat.postMessage" in str(request.url):
            return httpx.Response(200, json={"ok": True, "channel": "C123", "ts": "1700000000.000100"})
        return httpx.Response(200, json={"ok": False, "error": "invalid_auth"})

    client = make_client(handler)
    _, _, permalink = client.post_incident_notification(make_incident(), make_jira_ticket())
    assert permalink is None


def test_retries_on_429_then_succeeds():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if "chat.postMessage" in str(request.url):
            calls["count"] += 1
            if calls["count"] == 1:
                return httpx.Response(429, headers={"Retry-After": "0"}, json={"ok": False, "error": "rate_limited"})
            return httpx.Response(200, json={"ok": True, "channel": "C123", "ts": "1700000000.000100"})
        return httpx.Response(200, json={"ok": False, "error": "missing_scope"})

    client = make_client(handler)
    channel, ts, _ = client.post_incident_notification(make_incident(), make_jira_ticket())
    assert channel == "C123"
    assert calls["count"] == 2
