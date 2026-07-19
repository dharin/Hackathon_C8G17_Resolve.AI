import os

import pytest

# Force deterministic, offline test behavior regardless of the developer's
# local .env: mock auth (no real Clerk instance needed) and no LLM calls
# (no real OpenRouter key/network calls during the test suite). Must be set
# before anything imports config.settings, which loads .env with
# override=False — these pre-set values take precedence.
os.environ["AUTH_PROVIDER"] = "mock"
os.environ["OPENROUTER_API_KEY"] = ""


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
