import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

import httpx

from rag.models import KnowledgeDocument
from rag.normalizer import normalize_content
from rag.parsers.confluence_storage import parse_confluence_storage

logger = logging.getLogger(__name__)

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 5
_REQUEST_TIMEOUT_SECONDS = 30.0


class ConfluenceLoader:
    """Loads Confluence Cloud pages through the REST API (never MCP — see
    project-spec.md RAG Design) using bounded concurrency, retries, and
    backoff. Confluence content is treated as untrusted evidence: page
    bodies are sanitized by parse_confluence_storage before ever reaching a
    prompt.
    """

    source_type = "confluence"

    def __init__(
        self,
        site_url: str,
        email: str,
        api_token: str,
        cloud_id: str,
        included_space_keys: list[str] | None = None,
        page_limit: int = 100,
        sync_concurrency: int = 3,
    ) -> None:
        self.site_url = site_url.rstrip("/")
        self.cloud_id = cloud_id
        self.included_space_keys = set(included_space_keys or [])
        self.page_limit = page_limit
        self.sync_concurrency = max(1, sync_concurrency)
        self._api_base = f"https://api.atlassian.com/ex/confluence/{cloud_id}"
        self._client = httpx.Client(
            auth=httpx.BasicAuth(email, api_token),
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )

    def discover(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        spaces = self._discover_spaces()

        page_summaries: list[tuple[dict[str, Any], dict[str, Any]]] = []
        for space in spaces:
            for page_summary in self._list_pages(space["id"]):
                page_summaries.append((page_summary, space))

        with ThreadPoolExecutor(max_workers=self.sync_concurrency) as executor:
            futures = [
                executor.submit(self._safe_load_page, page_summary, space)
                for page_summary, space in page_summaries
            ]
            for future in as_completed(futures):
                document = future.result()
                if document is not None:
                    documents.append(document)

        return documents

    def _discover_spaces(self) -> list[dict[str, Any]]:
        spaces: list[dict[str, Any]] = []
        url = f"{self._api_base}/wiki/api/v2/spaces?limit=100"
        while url:
            data = self._get(url).json()
            for space in data.get("results", []):
                if self.included_space_keys and space.get("key") not in self.included_space_keys:
                    continue
                spaces.append(space)
            url = self._next_url(data)
        return spaces

    def _list_pages(self, space_id: str):
        url = f"{self._api_base}/wiki/api/v2/pages?space-id={space_id}&status=current&limit={self.page_limit}"
        while url:
            data = self._get(url).json()
            yield from data.get("results", [])
            url = self._next_url(data)

    def _safe_load_page(self, page_summary: dict[str, Any], space: dict[str, Any]) -> KnowledgeDocument | None:
        page_id = page_summary.get("id", "unknown")
        try:
            return self._load_page(page_id, space)
        except Exception as exc:  # noqa: BLE001 - isolate per-page failure
            logger.warning("Failed to load Confluence page %s: %s", page_id, exc)
            return None

    def _load_page(self, page_id: str, space: dict[str, Any]) -> KnowledgeDocument:
        url = f"{self._api_base}/wiki/api/v2/pages/{page_id}?body-format=storage"
        page = self._get(url).json()

        storage_html = page.get("body", {}).get("storage", {}).get("value", "")
        content = normalize_content(parse_confluence_storage(storage_html))
        version = str(page.get("version", {}).get("number", 1))
        webui_path = page.get("_links", {}).get("webui", "")

        return KnowledgeDocument(
            document_id=f"confluence:{page_id}",
            source_type="confluence",
            title=page.get("title", "Untitled"),
            content=content,
            source_uri=f"{self.site_url}/wiki{webui_path}",
            version=version,
            content_hash=_content_hash(content),
            updated_at=_parse_timestamp(page.get("version", {}).get("createdAt")),
            metadata={
                "cloud_id": self.cloud_id,
                "site_url": self.site_url,
                "space_id": space.get("id"),
                "space_key": space.get("key"),
                "space_name": space.get("name"),
                "page_id": page_id,
                "page_version": version,
                "parent_id": page.get("parentId"),
                "labels": [],
                "web_url": f"{self.site_url}/wiki{webui_path}",
            },
        )

    def _get(self, url: str) -> httpx.Response:
        return self._request("GET", url)

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        last_response: httpx.Response | None = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            response = self._client.request(method, url, **kwargs)
            last_response = response

            if response.status_code < 400:
                return response

            if response.status_code not in _RETRYABLE_STATUS_CODES or attempt == _MAX_ATTEMPTS:
                response.raise_for_status()

            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2**attempt, 30)
            delay += random.uniform(0, 0.5)
            logger.info(
                "Confluence request to %s got %s, retrying in %.1fs (attempt %d/%d)",
                url,
                response.status_code,
                delay,
                attempt,
                _MAX_ATTEMPTS,
            )
            time.sleep(delay)

        assert last_response is not None
        last_response.raise_for_status()
        return last_response

    def _next_url(self, data: dict[str, Any]) -> str | None:
        # Pagination cursors/next URLs are opaque — never parsed or rebuilt.
        next_link = data.get("_links", {}).get("next")
        if not next_link:
            return None
        if next_link.startswith("http"):
            return next_link
        return f"{self._api_base}{next_link}"


def _content_hash(content: str) -> str:
    import hashlib

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
