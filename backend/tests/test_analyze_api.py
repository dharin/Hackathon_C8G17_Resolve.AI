from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from config.settings import ANALYSES_DIR, UPLOAD_DIR
from main import app

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_logs"
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client():
    created_uploads_before = set(UPLOAD_DIR.iterdir())
    created_analyses_before = set(ANALYSES_DIR.iterdir())

    with TestClient(app) as test_client:
        yield test_client

    # Clean up whatever this test run wrote to the (real, git-ignored)
    # uploads/analyses directories, so repeated local test runs don't
    # accumulate files.
    for path in set(UPLOAD_DIR.iterdir()) - created_uploads_before:
        path.unlink(missing_ok=True)
    for path in set(ANALYSES_DIR.iterdir()) - created_analyses_before:
        path.unlink(missing_ok=True)


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
    # RCA is populated as of Phase 7; recommendations/cookbook wait for
    # Phases 8-9.
    assert body["rca"] is not None
    assert body["rca"]["incident_id"] == incident_id
    assert body["rca"]["primary_cause"]
    assert body["rca"]["evidence"]
    assert body["recommendations"] is None
    assert body["cookbook"] is None


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


def test_analyze_never_creates_jira_or_slack_side_effects(client: TestClient):
    # No Jira/Slack integration is even wired into the app yet in this
    # phase — asserting no such route exists confirms analysis can't have
    # triggered either.
    route_paths = {
        route.path for route in app.routes if hasattr(route, "path")
    }
    assert not any("jira" in path.lower() for path in route_paths)
    assert not any("slack" in path.lower() for path in route_paths)
