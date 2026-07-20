import os
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import httpx

from config import settings
from models.health import HealthCheckResult, IntegrationHealth

_TIMEOUT_SECONDS = 5.0


def check_all() -> HealthCheckResult:
    """Runs every integration's health check concurrently — each is an
    independent network call with its own timeout, and running them
    sequentially would make the popup wait for the sum of all five instead
    of the slowest one.
    """
    checks: list[Callable[[], IntegrationHealth]] = [
        _check_clerk,
        _check_llm,
        _check_jira,
        _check_confluence,
        _check_slack,
    ]
    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        integrations = list(executor.map(_run_safely, checks))
    return HealthCheckResult(integrations=integrations)


def _run_safely(check: Callable[[], IntegrationHealth]) -> IntegrationHealth:
    # A health check must never itself break the endpoint — any unexpected
    # error just reports that one integration as unavailable.
    try:
        return check()
    except Exception:  # noqa: BLE001
        return IntegrationHealth(
            key=check.__name__, name=check.__name__, healthy=False, status_text="Unavailable"
        )


def _request(method: str, url: str, **kwargs) -> httpx.Response:
    kwargs.setdefault("timeout", _TIMEOUT_SECONDS)
    return httpx.request(method, url, **kwargs)


def _reachable(method: str, url: str, **kwargs) -> bool:
    try:
        response = _request(method, url, **kwargs)
        return response.status_code < 400
    except httpx.HTTPError:
        return False


def _check_clerk() -> IntegrationHealth:
    # Every request reaching this endpoint already passed Clerk auth (see
    # api/deps.py::get_current_user) when AUTH_PROVIDER=clerk — but that's
    # also true under the mock provider used in tests/local dev, where no
    # real Clerk call happens at all. Checking configuration directly is
    # honest in both cases instead of just trusting "we got here".
    configured = bool(os.environ.get("CLERK_SECRET_KEY")) and bool(os.environ.get("CLERK_JWKS_URL"))
    return IntegrationHealth(
        key="clerk",
        name="Clerk",
        healthy=configured,
        status_text="Connected" if configured else "Unavailable",
    )


def _check_llm() -> IntegrationHealth:
    if not settings.OPENROUTER_API_KEY:
        return IntegrationHealth(
            key="llm",
            name="LLM",
            healthy=False,
            status_text="Unavailable",
            detail=settings.OPENROUTER_MODEL,
        )
    healthy = _reachable(
        "GET",
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
    )
    return IntegrationHealth(
        key="llm",
        name="LLM",
        healthy=healthy,
        status_text="Connected" if healthy else "Unavailable",
        detail=settings.OPENROUTER_MODEL,
    )


def _check_jira() -> IntegrationHealth:
    configured = bool(
        settings.JIRA_URL and settings.JIRA_EMAIL and settings.JIRA_TOKEN and settings.JIRA_PROJECT_KEY
    )
    if not configured:
        return IntegrationHealth(key="jira", name="Jira", healthy=False, status_text="Unavailable")

    healthy = _reachable(
        "GET",
        f"{settings.JIRA_URL.rstrip('/')}/rest/api/3/myself",
        auth=httpx.BasicAuth(settings.JIRA_EMAIL, settings.JIRA_TOKEN),
    )
    return IntegrationHealth(
        key="jira", name="Jira", healthy=healthy, status_text="Connected" if healthy else "Unavailable"
    )


def _check_confluence() -> IntegrationHealth:
    configured = bool(
        settings.CONFLUENCE_SITE_URL
        and settings.CONFLUENCE_EMAIL
        and settings.CONFLUENCE_API_TOKEN
        and settings.CONFLUENCE_CLOUD_ID
    )
    if not configured:
        return IntegrationHealth(key="confluence", name="Confluence", healthy=False, status_text="Unavailable")

    healthy = _reachable(
        "GET",
        f"https://api.atlassian.com/ex/confluence/{settings.CONFLUENCE_CLOUD_ID}/wiki/api/v2/spaces?limit=1",
        auth=httpx.BasicAuth(settings.CONFLUENCE_EMAIL, settings.CONFLUENCE_API_TOKEN),
    )
    return IntegrationHealth(
        key="confluence",
        name="Confluence",
        healthy=healthy,
        status_text="Connected" if healthy else "Unavailable",
    )


def _check_slack() -> IntegrationHealth:
    configured = bool(settings.SLACK_BOT_TOKEN and settings.SLACK_CHANNEL_ID)
    if not configured:
        return IntegrationHealth(key="slack", name="Slack", healthy=False, status_text="Unavailable")

    try:
        # Slack's Web API returns HTTP 200 even for a bad token — failure is
        # only visible in the JSON body's "ok" field.
        response = _request(
            "POST",
            "https://slack.com/api/auth.test",
            headers={"Authorization": f"Bearer {settings.SLACK_BOT_TOKEN}"},
        )
        healthy = response.status_code < 400 and response.json().get("ok") is True
    except httpx.HTTPError:
        healthy = False

    return IntegrationHealth(
        key="slack", name="Slack", healthy=healthy, status_text="Connected" if healthy else "Unavailable"
    )
