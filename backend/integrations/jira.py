import random
import time
from urllib.parse import urlparse

import httpx

from config.settings import JIRA_EMAIL, JIRA_ISSUE_TYPE, JIRA_PROJECT_KEY, JIRA_TOKEN, JIRA_URL
from models.jira_payload import JiraPayload

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 5
_REQUEST_TIMEOUT_SECONDS = 15.0


class JiraError(Exception):
    """Raised when Jira isn't configured or a create-issue call fails after retries."""


def _clean_base_url(raw: str) -> str:
    """Keeps only scheme + host from whatever was pasted into JIRA_URL — a
    URL copied straight from a browser tab commonly carries a `?continue=`
    redirect query string and other cruft that isn't part of the actual
    Jira Cloud API base.
    """
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    return f"{parsed.scheme}://{parsed.netloc}"


class JiraClient:
    """Jira Cloud REST API v3 client — creates issues from a `JiraPayload`.
    Never used to read/list existing tickets; only to create the one this
    incident's remediation already grounded (see agents/remediation.py).
    """

    def __init__(
        self,
        base_url: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
        project_key: str | None = None,
    ) -> None:
        self.base_url = _clean_base_url(base_url if base_url is not None else JIRA_URL)
        self._email = email if email is not None else JIRA_EMAIL
        self._token = api_token if api_token is not None else JIRA_TOKEN
        self.project_key = project_key if project_key is not None else JIRA_PROJECT_KEY

        self._client: httpx.Client | None = None
        if self.is_configured:
            self._client = httpx.Client(
                auth=httpx.BasicAuth(self._email, self._token),
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self._email and self._token and self.project_key)

    def create_issue(self, payload: JiraPayload) -> tuple[str, str]:
        """Returns (issue_key, issue_url). Raises JiraError if unconfigured
        or the API call fails after retries.
        """
        if self._client is None:
            raise JiraError(
                "Jira is not configured — set JIRA_URL, JIRA_EMAIL, JIRA_TOKEN, "
                "and JIRA_PROJECT_KEY."
            )

        # `priority` isn't sent as a structured field — not every Jira
        # project's create screen has one configured, and a field the
        # screen doesn't expect can fail issue creation outright. It's
        # folded into the description text instead, which always works.
        description = f"Priority: {payload.priority}\n\n{payload.description}"
        body = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": payload.summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": description}],
                        }
                    ],
                },
                "issuetype": {"name": JIRA_ISSUE_TYPE},
                "labels": payload.labels,
            }
        }

        response = self._request("POST", f"{self.base_url}/rest/api/3/issue", json=body)
        data = response.json()
        key = data["key"]
        return key, f"{self.base_url}/browse/{key}"

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        assert self._client is not None
        last_response: httpx.Response | None = None

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            response = self._client.request(method, url, **kwargs)
            last_response = response

            if response.status_code < 400:
                return response
            if response.status_code not in _RETRYABLE_STATUS_CODES or attempt == _MAX_ATTEMPTS:
                raise JiraError(
                    f"Jira request to {url} failed with {response.status_code}: {response.text[:500]}"
                )

            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2**attempt, 30)
            delay += random.uniform(0, 0.5)
            time.sleep(delay)

        assert last_response is not None
        raise JiraError(f"Jira request to {url} failed after {_MAX_ATTEMPTS} attempts.")
