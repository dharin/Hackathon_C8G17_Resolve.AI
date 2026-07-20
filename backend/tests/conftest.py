import os

import pytest

# Force deterministic, offline test behavior regardless of the developer's
# local .env: mock auth (no real Clerk instance needed) and no LLM calls
# (no real OpenRouter key/network calls during the test suite). Must be set
# before anything imports config.settings, which loads .env with
# override=False — these pre-set values take precedence.
os.environ["AUTH_PROVIDER"] = "mock"
os.environ["OPENROUTER_API_KEY"] = ""
# Blank real Jira credentials too — otherwise a CRITICAL-severity test
# incident would trigger a real ticket creation against whatever live
# Jira project is configured in the developer's .env (see
# api/analyze.py::get_incident_detail's auto-create-for-critical path).
os.environ["JIRA_URL"] = ""
os.environ["JIRA_EMAIL"] = ""
os.environ["JIRA_TOKEN"] = ""
os.environ["JIRA_PROJECT_KEY"] = ""
# Same reasoning for Slack — a CRITICAL incident with a (test-created)
# Jira ticket would otherwise post a real message to whatever live channel
# is configured (see services/slack_service.py's auto-notify path).
os.environ["SLACK_BOT_TOKEN"] = ""
os.environ["SLACK_CHANNEL_ID"] = ""
# services/health_service.py reads these directly (not via config.settings),
# so they need the same treatment: without this, the health-check tests'
# result would depend on whether the developer's local .env happens to have
# real Clerk credentials.
os.environ["CLERK_SECRET_KEY"] = ""
os.environ["CLERK_JWKS_URL"] = ""
os.environ["CONFLUENCE_SITE_URL"] = ""
os.environ["CONFLUENCE_EMAIL"] = ""
os.environ["CONFLUENCE_API_TOKEN"] = ""
os.environ["CONFLUENCE_CLOUD_ID"] = ""


class _EmptyRetriever:
    """Default stand-in for the real RAG retriever (which would otherwise
    download an embedding model / open LanceDB on first use). Individual
    tests that need real chunk data monkeypatch `agents.remediation.get_retriever`
    themselves, overriding this default within their own scope.
    """

    def retrieve(self, *args, **kwargs):
        return []


@pytest.fixture(autouse=True)
def _stub_remediation_retriever(monkeypatch):
    monkeypatch.setattr("agents.remediation.get_retriever", lambda: _EmptyRetriever())
