import base64

import httpx
import pytest

from rag.loaders.confluence import ConfluenceLoader

CLOUD_ID = "test-cloud-id"
API_BASE = f"https://api.atlassian.com/ex/confluence/{CLOUD_ID}"


def make_loader(handler, **kwargs) -> ConfluenceLoader:
    loader = ConfluenceLoader(
        site_url="https://example.atlassian.net",
        email="bot@example.com",
        api_token="super-secret-token",
        cloud_id=CLOUD_ID,
        **kwargs,
    )
    loader._client = httpx.Client(
        auth=httpx.BasicAuth("bot@example.com", "super-secret-token"),
        transport=httpx.MockTransport(handler),
    )
    return loader


def test_auth_header_is_basic_and_does_not_expose_token_in_repr():
    def handler(request: httpx.Request) -> httpx.Response:
        auth_header = request.headers["Authorization"]
        assert auth_header.startswith("Basic ")
        decoded = base64.b64decode(auth_header.removeprefix("Basic ")).decode()
        assert decoded == "bot@example.com:super-secret-token"
        return httpx.Response(200, json={"results": [], "_links": {}})

    loader = make_loader(handler)
    assert "super-secret-token" not in repr(loader.__dict__.get("_client"))
    loader._discover_spaces()


def test_space_pagination_follows_next_link():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith(f"{API_BASE}/wiki/api/v2/spaces"):
            calls["count"] += 1
            if calls["count"] == 1:
                return httpx.Response(
                    200,
                    json={
                        "results": [{"id": "1", "key": "AAA", "name": "Space A"}],
                        "_links": {"next": "/wiki/api/v2/spaces?cursor=page2"},
                    },
                )
            return httpx.Response(
                200,
                json={"results": [{"id": "2", "key": "BBB", "name": "Space B"}], "_links": {}},
            )
        return httpx.Response(200, json={"results": [], "_links": {}})

    loader = make_loader(handler)
    spaces = loader._discover_spaces()
    assert [s["key"] for s in spaces] == ["AAA", "BBB"]
    assert calls["count"] == 2


def test_configured_space_filtering():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"id": "1", "key": "KEEP", "name": "Keep"},
                    {"id": "2", "key": "SKIP", "name": "Skip"},
                ],
                "_links": {},
            },
        )

    loader = make_loader(handler, included_space_keys=["KEEP"])
    spaces = loader._discover_spaces()
    assert [s["key"] for s in spaces] == ["KEEP"]


def test_page_retrieval_and_storage_normalization():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/pages/123" in url:
            return httpx.Response(
                200,
                json={
                    "id": "123",
                    "title": "Disk Cleanup Runbook",
                    "spaceId": "1",
                    "parentId": None,
                    "version": {"number": 2, "createdAt": "2024-01-01T00:00:00Z"},
                    "body": {"storage": {"value": "<h1>Runbook</h1><p>Clean the disk.</p>"}},
                    "_links": {"webui": "/spaces/AAA/pages/123/Disk-Cleanup"},
                },
            )
        return httpx.Response(200, json={"results": [], "_links": {}})

    loader = make_loader(handler)
    document = loader._load_page("123", {"id": "1", "key": "AAA", "name": "Space A"})

    assert document.source_type == "confluence"
    assert document.title == "Disk Cleanup Runbook"
    assert "# Runbook" in document.content
    assert "Clean the disk." in document.content
    assert document.version == "2"
    assert document.source_uri.endswith("/spaces/AAA/pages/123/Disk-Cleanup")
    assert document.metadata["space_key"] == "AAA"
    assert document.metadata["page_id"] == "123"


def test_retries_on_429_then_succeeds():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            return httpx.Response(429, headers={"Retry-After": "0"}, json={"error": "rate limited"})
        return httpx.Response(200, json={"results": [], "_links": {}})

    loader = make_loader(handler)
    response = loader._get(f"{API_BASE}/wiki/api/v2/spaces?limit=100")
    assert response.status_code == 200
    assert calls["count"] == 2


def test_does_not_retry_on_404():
    calls = {"count": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        return httpx.Response(404, json={"error": "not found"})

    loader = make_loader(handler)
    with pytest.raises(httpx.HTTPStatusError):
        loader._get(f"{API_BASE}/wiki/api/v2/pages/999")
    assert calls["count"] == 1


def test_failed_page_does_not_abort_full_discover():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "/spaces" in url:
            return httpx.Response(200, json={"results": [{"id": "1", "key": "AAA", "name": "A"}], "_links": {}})
        if "/pages?" in url:
            return httpx.Response(
                200,
                json={
                    "results": [{"id": "good"}, {"id": "bad"}],
                    "_links": {},
                },
            )
        if "/pages/bad" in url:
            return httpx.Response(404, json={"error": "gone"})
        if "/pages/good" in url:
            return httpx.Response(
                200,
                json={
                    "id": "good",
                    "title": "Good Page",
                    "version": {"number": 1},
                    "body": {"storage": {"value": "<p>ok</p>"}},
                    "_links": {"webui": "/pages/good"},
                },
            )
        return httpx.Response(200, json={"results": [], "_links": {}})

    loader = make_loader(handler, sync_concurrency=1)
    documents = loader.discover()

    assert len(documents) == 1
    assert documents[0].document_id == "confluence:good"
