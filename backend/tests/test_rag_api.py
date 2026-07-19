from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import rag as rag_api
from main import app
from rag.models import SourceSyncSummary
from services import rag_sync_meta_store

AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def _isolated_meta_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(rag_sync_meta_store, "RAG_SYNC_META_DB_PATH", tmp_path / "rag_sync_meta.sqlite3")


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


class _FakeCoordinator:
    def __init__(self, results: dict[str, object]):
        self._results = results

    def sync_source(self, loader):
        result = self._results[loader]
        if isinstance(result, Exception):
            raise result
        return result


def _confluence_summary(**overrides) -> SourceSyncSummary:
    defaults = dict(
        source_type="confluence",
        documents_discovered=3,
        documents_indexed=3,
        documents_skipped_unchanged=0,
        documents_marked_unavailable=0,
        documents_failed=0,
    )
    defaults.update(overrides)
    return SourceSyncSummary(**defaults)


def _local_sop_summary(**overrides) -> SourceSyncSummary:
    defaults = dict(
        source_type="local_sop",
        documents_discovered=2,
        documents_indexed=2,
        documents_skipped_unchanged=0,
        documents_marked_unavailable=0,
        documents_failed=0,
    )
    defaults.update(overrides)
    return SourceSyncSummary(**defaults)


def test_status_requires_auth(client: TestClient):
    response = client.get("/api/v1/rag/status")
    assert response.status_code == 401


def test_status_returns_none_when_never_synced(client: TestClient):
    response = client.get("/api/v1/rag/status", headers=AUTH_HEADERS)
    assert response.status_code == 200
    assert response.json()["last_synced_at"] is None


def test_sync_requires_auth(client: TestClient):
    response = client.post("/api/v1/rag/sync")
    assert response.status_code == 401


def test_sync_success_advances_last_synced_at(client: TestClient, monkeypatch):
    monkeypatch.setattr(rag_api, "build_confluence_loader", lambda: "confluence-loader")
    monkeypatch.setattr(rag_api, "build_local_sop_loader", lambda: "local-loader")
    monkeypatch.setattr(
        rag_api,
        "get_sync_coordinator",
        lambda: _FakeCoordinator(
            {"confluence-loader": _confluence_summary(), "local-loader": _local_sop_summary()}
        ),
    )

    response = client.post("/api/v1/rag/sync", headers=AUTH_HEADERS)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["errors"] == []
    assert body["last_synced_at"] is not None
    assert {s["source_type"] for s in body["summaries"]} == {"confluence", "local_sop"}

    status_response = client.get("/api/v1/rag/status", headers=AUTH_HEADERS)
    assert status_response.json()["last_synced_at"] == body["last_synced_at"]


def test_sync_skips_confluence_when_unconfigured(client: TestClient, monkeypatch):
    monkeypatch.setattr(rag_api, "build_confluence_loader", lambda: None)
    monkeypatch.setattr(rag_api, "build_local_sop_loader", lambda: "local-loader")
    monkeypatch.setattr(
        rag_api, "get_sync_coordinator", lambda: _FakeCoordinator({"local-loader": _local_sop_summary()})
    )

    response = client.post("/api/v1/rag/sync", headers=AUTH_HEADERS)

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["errors"] == []
    assert {s["source_type"] for s in body["summaries"]} == {"local_sop"}


def test_sync_failure_does_not_advance_last_synced_at(client: TestClient, monkeypatch):
    monkeypatch.setattr(rag_api, "build_confluence_loader", lambda: "confluence-loader")
    monkeypatch.setattr(rag_api, "build_local_sop_loader", lambda: "local-loader")
    monkeypatch.setattr(
        rag_api,
        "get_sync_coordinator",
        lambda: _FakeCoordinator(
            {"confluence-loader": RuntimeError("auth failed"), "local-loader": _local_sop_summary()}
        ),
    )

    response = client.post("/api/v1/rag/sync", headers=AUTH_HEADERS)

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body["errors"]) == 1
    assert "confluence" in body["errors"][0]
    assert body["last_synced_at"] is None  # never synced before, and this run failed
    # The one source that did succeed is still reported.
    assert {s["source_type"] for s in body["summaries"]} == {"local_sop"}


def test_sync_failure_rolls_back_to_previous_last_synced_at(client: TestClient, monkeypatch):
    previous = rag_sync_meta_store.set_last_synced_at()

    monkeypatch.setattr(rag_api, "build_confluence_loader", lambda: "confluence-loader")
    monkeypatch.setattr(rag_api, "build_local_sop_loader", lambda: "local-loader")
    monkeypatch.setattr(
        rag_api,
        "get_sync_coordinator",
        lambda: _FakeCoordinator(
            {"confluence-loader": RuntimeError("boom"), "local-loader": _local_sop_summary()}
        ),
    )

    response = client.post("/api/v1/rag/sync", headers=AUTH_HEADERS)

    assert response.status_code == 200, response.text
    returned = datetime.fromisoformat(response.json()["last_synced_at"].replace("Z", "+00:00"))
    assert returned == previous
