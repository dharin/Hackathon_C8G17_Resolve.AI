from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config.settings import (
    ANALYSES_DB_PATH,
    JIRA_TICKETS_DB_PATH,
    SLACK_NOTIFICATIONS_DB_PATH,
    UPLOAD_DIR,
)
from main import app
from models.slack_notification import SlackNotificationReference
from services import jira_ticket_store, slack_service

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_logs"
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client():
    created_uploads_before = set(UPLOAD_DIR.iterdir())
    ANALYSES_DB_PATH.unlink(missing_ok=True)
    JIRA_TICKETS_DB_PATH.unlink(missing_ok=True)
    SLACK_NOTIFICATIONS_DB_PATH.unlink(missing_ok=True)

    with TestClient(app) as test_client:
        yield test_client

    for path in set(UPLOAD_DIR.iterdir()) - created_uploads_before:
        path.unlink(missing_ok=True)
    ANALYSES_DB_PATH.unlink(missing_ok=True)
    JIRA_TICKETS_DB_PATH.unlink(missing_ok=True)
    SLACK_NOTIFICATIONS_DB_PATH.unlink(missing_ok=True)


def upload_and_analyze(client: TestClient, filename: str) -> tuple[str, str]:
    with (FIXTURES_DIR / filename).open("rb") as f:
        upload_response = client.post(
            "/api/v1/logs/upload",
            headers=AUTH_HEADERS,
            files={"file": (filename, f, "text/plain")},
        )
    upload_id = upload_response.json()["upload_id"]

    analyze_response = client.post(
        f"/api/v1/logs/{upload_id}/analyze", headers=AUTH_HEADERS
    )
    body = analyze_response.json()
    return body["analysis_id"], body["incidents"][0]["id"]


def test_notify_slack_requires_auth(client: TestClient):
    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/notify-slack"
    )
    assert response.status_code == 401


def test_notify_slack_unknown_analysis_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/analyses/does-not-exist/incidents/whatever/notify-slack",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


def test_notify_slack_unknown_incident_returns_404(client: TestClient):
    analysis_id, _ = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/does-not-exist/notify-slack",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


def test_notify_slack_without_jira_ticket_returns_422(client: TestClient):
    # oom_kill.log's incident is CRITICAL, but no Jira ticket exists (Jira
    # unconfigured in tests — see conftest.py), so there's nothing to
    # notify about yet.
    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/notify-slack",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 422


def test_notify_slack_returns_reference_when_ticket_exists(client: TestClient, monkeypatch):
    notification = SlackNotificationReference(
        channel_id="C123", message_ts="1700000000.000100", permalink="https://x.slack.com/archives/C123/p1",
        sent_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(slack_service, "notify_or_raise", lambda *a, **k: notification)

    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    jira_ticket_store.save_ticket(analysis_id, incident_id, "OPS-1", "https://x/browse/OPS-1")

    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/notify-slack",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["channel_id"] == "C123"
    assert body["message_ts"] == "1700000000.000100"


def test_notify_slack_is_idempotent_across_calls(client: TestClient):
    from services import slack_notification_store

    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    jira_ticket_store.save_ticket(analysis_id, incident_id, "OPS-1", "https://x/browse/OPS-1")
    slack_notification_store.save_notification(
        analysis_id, incident_id, "C123", "111.1", None
    )

    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/notify-slack",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    assert response.json()["message_ts"] == "111.1"
