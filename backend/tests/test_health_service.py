import httpx
import pytest

from services import health_service


@pytest.fixture(autouse=True)
def _clear_all_integration_config(monkeypatch):
    for key in [
        "CLERK_SECRET_KEY",
        "CLERK_JWKS_URL",
        "JIRA_URL",
        "JIRA_EMAIL",
        "JIRA_TOKEN",
        "JIRA_PROJECT_KEY",
        "SLACK_BOT_TOKEN",
        "SLACK_CHANNEL_ID",
        "CONFLUENCE_SITE_URL",
        "CONFLUENCE_EMAIL",
        "CONFLUENCE_API_TOKEN",
        "CONFLUENCE_CLOUD_ID",
    ]:
        monkeypatch.setenv(key, "")
    monkeypatch.setattr(health_service.settings, "JIRA_URL", "")
    monkeypatch.setattr(health_service.settings, "JIRA_EMAIL", "")
    monkeypatch.setattr(health_service.settings, "JIRA_TOKEN", "")
    monkeypatch.setattr(health_service.settings, "JIRA_PROJECT_KEY", "")
    monkeypatch.setattr(health_service.settings, "SLACK_BOT_TOKEN", "")
    monkeypatch.setattr(health_service.settings, "SLACK_CHANNEL_ID", "")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_SITE_URL", "")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_EMAIL", "")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_API_TOKEN", "")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_CLOUD_ID", "")
    monkeypatch.setattr(health_service.settings, "OPENROUTER_API_KEY", None)


def test_all_unconfigured_reports_every_integration_unhealthy():
    result = health_service.check_all()
    assert {i.key for i in result.integrations} == {"clerk", "llm", "jira", "confluence", "slack"}
    assert all(not i.healthy for i in result.integrations)
    assert all(i.status_text == "Unavailable" for i in result.integrations)


def test_llm_unconfigured_still_reports_configured_model_name(monkeypatch):
    monkeypatch.setattr(health_service.settings, "OPENROUTER_MODEL", "openai/gpt-4.1-mini")
    result = health_service.check_all()
    llm = next(i for i in result.integrations if i.key == "llm")
    assert llm.healthy is False
    assert llm.detail == "openai/gpt-4.1-mini"


def test_clerk_healthy_when_configured(monkeypatch):
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://example.clerk.accounts.dev/.well-known/jwks.json")
    result = health_service.check_all()
    clerk = next(i for i in result.integrations if i.key == "clerk")
    assert clerk.healthy is True
    assert clerk.status_text == "Connected"


def test_llm_healthy_when_key_configured_and_endpoint_reachable(monkeypatch):
    monkeypatch.setattr(health_service.settings, "OPENROUTER_API_KEY", "or-key")

    def fake_request(method, url, **kwargs):
        assert "openrouter.ai" in url
        return httpx.Response(200, json={"data": {}})

    monkeypatch.setattr(health_service, "_request", fake_request)
    result = health_service.check_all()
    llm = next(i for i in result.integrations if i.key == "llm")
    assert llm.healthy is True


def test_llm_unhealthy_when_key_configured_but_endpoint_rejects(monkeypatch):
    monkeypatch.setattr(health_service.settings, "OPENROUTER_API_KEY", "bad-key")
    monkeypatch.setattr(
        health_service, "_request", lambda method, url, **kwargs: httpx.Response(401)
    )
    result = health_service.check_all()
    llm = next(i for i in result.integrations if i.key == "llm")
    assert llm.healthy is False


def test_jira_healthy_when_configured_and_reachable(monkeypatch):
    monkeypatch.setattr(health_service.settings, "JIRA_URL", "https://example.atlassian.net")
    monkeypatch.setattr(health_service.settings, "JIRA_EMAIL", "bot@example.com")
    monkeypatch.setattr(health_service.settings, "JIRA_TOKEN", "token")
    monkeypatch.setattr(health_service.settings, "JIRA_PROJECT_KEY", "OPS")
    monkeypatch.setattr(
        health_service, "_request", lambda method, url, **kwargs: httpx.Response(200, json={})
    )
    result = health_service.check_all()
    jira = next(i for i in result.integrations if i.key == "jira")
    assert jira.healthy is True
    assert jira.status_text == "Connected"


def test_jira_unhealthy_on_network_error(monkeypatch):
    monkeypatch.setattr(health_service.settings, "JIRA_URL", "https://example.atlassian.net")
    monkeypatch.setattr(health_service.settings, "JIRA_EMAIL", "bot@example.com")
    monkeypatch.setattr(health_service.settings, "JIRA_TOKEN", "token")
    monkeypatch.setattr(health_service.settings, "JIRA_PROJECT_KEY", "OPS")

    def raise_timeout(method, url, **kwargs):
        raise httpx.ConnectTimeout("timed out")

    monkeypatch.setattr(health_service, "_request", raise_timeout)
    result = health_service.check_all()
    jira = next(i for i in result.integrations if i.key == "jira")
    assert jira.healthy is False


def test_confluence_healthy_when_configured_and_reachable(monkeypatch):
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_SITE_URL", "https://example.atlassian.net")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_EMAIL", "bot@example.com")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_API_TOKEN", "token")
    monkeypatch.setattr(health_service.settings, "CONFLUENCE_CLOUD_ID", "cloud-id")
    monkeypatch.setattr(
        health_service, "_request", lambda method, url, **kwargs: httpx.Response(200, json={"results": []})
    )
    result = health_service.check_all()
    confluence = next(i for i in result.integrations if i.key == "confluence")
    assert confluence.healthy is True


def test_slack_healthy_requires_ok_true_in_body_not_just_status_200(monkeypatch):
    # Slack's Web API returns HTTP 200 even for a bad token — "ok": false is
    # the only signal of failure, so a 200 with ok=false must be unhealthy.
    monkeypatch.setattr(health_service.settings, "SLACK_BOT_TOKEN", "xoxb-token")
    monkeypatch.setattr(health_service.settings, "SLACK_CHANNEL_ID", "C123")
    monkeypatch.setattr(
        health_service,
        "_request",
        lambda method, url, **kwargs: httpx.Response(200, json={"ok": False, "error": "invalid_auth"}),
    )
    result = health_service.check_all()
    slack = next(i for i in result.integrations if i.key == "slack")
    assert slack.healthy is False


def test_slack_healthy_when_ok_true(monkeypatch):
    monkeypatch.setattr(health_service.settings, "SLACK_BOT_TOKEN", "xoxb-token")
    monkeypatch.setattr(health_service.settings, "SLACK_CHANNEL_ID", "C123")
    monkeypatch.setattr(
        health_service, "_request", lambda method, url, **kwargs: httpx.Response(200, json={"ok": True})
    )
    result = health_service.check_all()
    slack = next(i for i in result.integrations if i.key == "slack")
    assert slack.healthy is True


def test_a_check_raising_unexpectedly_does_not_break_the_others(monkeypatch):
    def exploding_check():
        raise RuntimeError("boom")

    monkeypatch.setattr(health_service, "_check_jira", exploding_check)
    result = health_service.check_all()
    assert len(result.integrations) == 5
    assert all(not i.healthy for i in result.integrations)
