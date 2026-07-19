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

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_logs"
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client():
    created_uploads_before = set(UPLOAD_DIR.iterdir())
    # Analyses/tickets/notifications now live in single SQLite files (see
    # services/analysis_store.py, services/jira_ticket_store.py,
    # services/slack_notification_store.py) rather than one file per
    # analysis, so it's simplest to reset them entirely around each test
    # rather than diff their contents.
    ANALYSES_DB_PATH.unlink(missing_ok=True)
    JIRA_TICKETS_DB_PATH.unlink(missing_ok=True)
    SLACK_NOTIFICATIONS_DB_PATH.unlink(missing_ok=True)

    with TestClient(app) as test_client:
        yield test_client

    # Clean up whatever this test run wrote to the (real, git-ignored)
    # uploads directory, so repeated local test runs don't accumulate files.
    for path in set(UPLOAD_DIR.iterdir()) - created_uploads_before:
        path.unlink(missing_ok=True)
    ANALYSES_DB_PATH.unlink(missing_ok=True)
    JIRA_TICKETS_DB_PATH.unlink(missing_ok=True)
    SLACK_NOTIFICATIONS_DB_PATH.unlink(missing_ok=True)


def upload_sample(client: TestClient, filename: str) -> str:
    with (FIXTURES_DIR / filename).open("rb") as f:
        response = client.post(
            "/api/v1/logs/upload",
            headers=AUTH_HEADERS,
            files={"file": (filename, f, "text/plain")},
        )
    assert response.status_code == 200, response.text
    return response.json()["upload_id"]


def test_analyze_end_to_end(client: TestClient):
    upload_id = upload_sample(client, "mixed.log")

    analyze_response = client.post(
        f"/api/v1/logs/{upload_id}/analyze", headers=AUTH_HEADERS
    )
    assert analyze_response.status_code == 200, analyze_response.text
    body = analyze_response.json()
    assert body["upload_id"] == upload_id
    analysis_id = body["analysis_id"]
    assert len(body["incidents"]) >= 4

    categories = {issue["category"] for issue in body["incidents"]}
    assert "database_connection_error" in categories
    assert "oom_kill" in categories
    assert "auth_failure" in categories

    incidents_response = client.get(
        f"/api/v1/analyses/{analysis_id}/incidents", headers=AUTH_HEADERS
    )
    assert incidents_response.status_code == 200
    incidents = incidents_response.json()
    assert incidents == body["incidents"]


def test_analyze_unknown_upload_id_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/logs/does-not-exist/analyze", headers=AUTH_HEADERS
    )
    assert response.status_code == 404


def test_incidents_unknown_analysis_id_returns_404(client: TestClient):
    response = client.get(
        "/api/v1/analyses/does-not-exist/incidents", headers=AUTH_HEADERS
    )
    assert response.status_code == 404


def test_incident_detail_returns_the_matching_incident(client: TestClient):
    upload_id = upload_sample(client, "mixed.log")
    analyze_response = client.post(
        f"/api/v1/logs/{upload_id}/analyze", headers=AUTH_HEADERS
    )
    analysis_id = analyze_response.json()["analysis_id"]
    incident_id = analyze_response.json()["incidents"][0]["id"]

    response = client.get(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["incident"]["id"] == incident_id
    # RCA (Phase 7), recommendations (Phase 8), and cookbook (Phase 9) are
    # all populated now. Recommendations/commands are empty because the
    # test suite stubs retrieval to return no chunks (see conftest.py) —
    # a real, legitimate "no supporting documentation found" state, not a
    # missing feature.
    assert body["rca"] is not None
    assert body["rca"]["incident_id"] == incident_id
    assert body["rca"]["primary_cause"]
    assert body["rca"]["evidence"]
    assert body["recommendations"] == []
    assert body["cookbook"] is not None
    assert body["cookbook"]["root_cause"] == body["rca"]["primary_cause"]
    assert body["cookbook"]["commands"] == []
    # Jira/Slack are unconfigured in tests (see conftest.py) — even for a
    # CRITICAL-severity incident, auto-creation/notification is a no-op
    # rather than an error (see services/jira_service.py::ensure_ticket,
    # services/slack_service.py::ensure_notification).
    assert body["jira_ticket"] is None
    assert body["slack_notification"] is None


def test_incident_detail_unknown_analysis_id_returns_404(client: TestClient):
    response = client.get(
        "/api/v1/analyses/does-not-exist/incidents/whatever", headers=AUTH_HEADERS
    )
    assert response.status_code == 404


def test_incident_detail_unknown_incident_id_returns_404(client: TestClient):
    upload_id = upload_sample(client, "oom_kill.log")
    analyze_response = client.post(
        f"/api/v1/logs/{upload_id}/analyze", headers=AUTH_HEADERS
    )
    analysis_id = analyze_response.json()["analysis_id"]

    response = client.get(
        f"/api/v1/analyses/{analysis_id}/incidents/does-not-exist",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


def test_analyze_requires_auth(client: TestClient):
    upload_id = upload_sample(client, "oom_kill.log")
    response = client.post(f"/api/v1/logs/{upload_id}/analyze")
    assert response.status_code == 401


def test_analyze_alone_never_creates_jira_or_slack_side_effects(client: TestClient):
    # Analyzing a log only runs the Log Reader Agent (see
    # graph/orchestrator.py::get_detection_graph) — RCA/Remediation/
    # Cookbook, and any Jira/Slack side effects, only ever happen once an
    # incident's detail is actually fetched (api/analyze.py::get_incident_detail).
    from services import jira_ticket_store, slack_notification_store

    upload_id = upload_sample(client, "oom_kill.log")
    analyze_response = client.post(
        f"/api/v1/logs/{upload_id}/analyze", headers=AUTH_HEADERS
    )
    analysis_id = analyze_response.json()["analysis_id"]
    incident_id = analyze_response.json()["incidents"][0]["id"]

    assert jira_ticket_store.get_ticket(analysis_id, incident_id) is None
    assert slack_notification_store.get_notification(analysis_id, incident_id) is None


def test_critical_incident_auto_creates_jira_then_notifies_slack(client: TestClient, monkeypatch):
    from datetime import datetime, timezone

    from models.jira_ticket import JiraTicketReference
    from models.slack_notification import SlackNotificationReference
    from services import jira_service, slack_service

    ticket = JiraTicketReference(
        key="OPS-1", url="https://example.atlassian.net/browse/OPS-1", created_at=datetime.now(timezone.utc)
    )
    notification = SlackNotificationReference(
        channel_id="C123", message_ts="111.1", permalink=None, sent_at=datetime.now(timezone.utc)
    )
    calls: list[str] = []

    def fake_ensure_ticket(analysis_id, incident_id, jira_payload):
        calls.append("jira")
        return ticket

    def fake_ensure_notification(analysis_id, incident, jira_ticket):
        calls.append("slack")
        assert jira_ticket == ticket  # Slack only ever receives an already-created ticket
        return notification

    monkeypatch.setattr(jira_service, "ensure_ticket", fake_ensure_ticket)
    monkeypatch.setattr(slack_service, "ensure_notification", fake_ensure_notification)

    upload_id = upload_sample(client, "oom_kill.log")  # CRITICAL severity
    analyze_response = client.post(
        f"/api/v1/logs/{upload_id}/analyze", headers=AUTH_HEADERS
    )
    analysis_id = analyze_response.json()["analysis_id"]
    incident_id = analyze_response.json()["incidents"][0]["id"]

    response = client.get(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["jira_ticket"]["key"] == "OPS-1"
    assert body["slack_notification"]["channel_id"] == "C123"
    assert calls == ["jira", "slack"]  # Jira strictly before Slack
