import httpx
import pytest

from integrations.jira import JiraClient, JiraError
from models.jira_payload import JiraPayload


def make_payload(**overrides) -> JiraPayload:
    defaults = dict(
        incident_id="incident-1",
        summary="Database connections exhausted",
        description="The database exhausted its connection pool.",
        priority="Highest",
        labels=["database_connection_error", "checkout-api"],
    )
    defaults.update(overrides)
    return JiraPayload(**defaults)


def make_client(handler, **overrides) -> JiraClient:
    client = JiraClient(
        base_url=overrides.get("base_url", "https://example.atlassian.net"),
        email=overrides.get("email", "bot@example.com"),
        api_token=overrides.get("api_token", "super-secret-token"),
        project_key=overrides.get("project_key", "OPS"),
    )
    client._client = httpx.Client(
        auth=httpx.BasicAuth("bot@example.com", "super-secret-token"),
        transport=httpx.MockTransport(handler),
    )
    return client


def test_clean_base_url_strips_browser_query_string():
    client = JiraClient(
        base_url="https://example.atlassian.net?continue=https%3A%2F%2Fexample.atlassian.net%2Fwelcome&atlOrigin=xyz",
        email="e",
        api_token="t",
        project_key="OPS",
    )
    assert client.base_url == "https://example.atlassian.net"


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(base_url="", email="e", api_token="t", project_key="OPS"),
        dict(base_url="https://x.atlassian.net", email="", api_token="t", project_key="OPS"),
        dict(base_url="https://x.atlassian.net", email="e", api_token="", project_key="OPS"),
        dict(base_url="https://x.atlassian.net", email="e", api_token="t", project_key=""),
    ],
)
def test_is_configured_false_when_any_field_missing(kwargs):
    assert JiraClient(**kwargs).is_configured is False


def test_create_issue_raises_when_not_configured():
    client = JiraClient(base_url="", email="", api_token="", project_key="")
    with pytest.raises(JiraError):
        client.create_issue(make_payload())


def test_create_issue_sends_expected_project_and_summary():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.read()
        return httpx.Response(201, json={"key": "OPS-42", "id": "10001"})

    client = make_client(handler)
    key, url = client.create_issue(make_payload())

    assert key == "OPS-42"
    assert url == "https://example.atlassian.net/browse/OPS-42"

    import json

    body = json.loads(captured["body"])
    assert body["fields"]["project"]["key"] == "OPS"
    assert body["fields"]["summary"] == "Database connections exhausted"
    assert body["fields"]["labels"] == ["database_connection_error", "checkout-api"]
    # Priority isn't sent as a structured field (see integrations/jira.py) —
    # it's folded into the description text instead.
    assert "priority" not in body["fields"]
    assert "Priority: Highest" in body["fields"]["description"]["content"][0]["content"][0]["text"]


def test_create_issue_retries_on_429_then_succeeds():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate limited"})
        return httpx.Response(201, json={"key": "OPS-1"})

    client = make_client(handler)
    key, _ = client.create_issue(make_payload())
    assert key == "OPS-1"
    assert calls["count"] == 2


def test_create_issue_does_not_retry_on_400():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(400, json={"errors": {"project": "invalid"}})

    client = make_client(handler)
    with pytest.raises(JiraError):
        client.create_issue(make_payload())
    assert calls["count"] == 1
