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
from models.jira_ticket import JiraTicketReference
from services import jira_service

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


def test_create_jira_requires_auth(client: TestClient):
    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/create-jira"
    )
    assert response.status_code == 401


def test_create_jira_unknown_analysis_returns_404(client: TestClient):
    response = client.post(
        "/api/v1/analyses/does-not-exist/incidents/whatever/create-jira",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


def test_create_jira_unknown_incident_returns_404(client: TestClient):
    analysis_id, _ = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/does-not-exist/create-jira",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 404


def test_create_jira_without_grounded_payload_returns_422(client: TestClient):
    # No Jira config and no retrieved chunks (stubbed retriever) means no
    # JiraPayload was built for this incident.
    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/create-jira",
        headers=AUTH_HEADERS,
    )
    assert response.status_code == 422


def test_create_jira_returns_ticket_reference_when_grounded(client: TestClient, monkeypatch):
    ticket = JiraTicketReference(
        key="OPS-99", url="https://example.atlassian.net/browse/OPS-99", created_at=datetime.now(timezone.utc)
    )
    monkeypatch.setattr(jira_service, "create_ticket_or_raise", lambda *a, **k: ticket)

    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/create-jira",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["key"] == "OPS-99"
    assert body["url"] == "https://example.atlassian.net/browse/OPS-99"


def test_create_jira_is_idempotent_across_calls(client: TestClient):
    from services import jira_ticket_store

    analysis_id, incident_id = upload_and_analyze(client, "oom_kill.log")
    jira_ticket_store.save_ticket(analysis_id, incident_id, "OPS-1", "https://x/browse/OPS-1")

    response = client.post(
        f"/api/v1/analyses/{analysis_id}/incidents/{incident_id}/create-jira",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200, response.text
    assert response.json()["key"] == "OPS-1"
