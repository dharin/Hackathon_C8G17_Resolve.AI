import pytest
from fastapi.testclient import TestClient

from api import health as health_api
from main import app
from models.health import HealthCheckResult, IntegrationHealth

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_requires_auth(client: TestClient):
    response = client.get("/api/v1/health/integrations")
    assert response.status_code == 401


def test_returns_check_all_result(client: TestClient, monkeypatch):
    fake_result = HealthCheckResult(
        integrations=[
            IntegrationHealth(key="clerk", name="Clerk", healthy=True, status_text="Connected"),
            IntegrationHealth(key="llm", name="LLM", healthy=False, status_text="Unavailable", detail="model-x"),
        ]
    )
    monkeypatch.setattr(health_api.health_service, "check_all", lambda: fake_result)

    response = client.get("/api/v1/health/integrations", headers=AUTH_HEADERS)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["integrations"][0] == {
        "key": "clerk",
        "name": "Clerk",
        "healthy": True,
        "status_text": "Connected",
        "detail": None,
    }
    assert body["integrations"][1]["detail"] == "model-x"
