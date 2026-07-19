import random
import time

import httpx

from config.settings import SLACK_BOT_TOKEN, SLACK_CHANNEL_ID
from models.jira_ticket import JiraTicketReference
from models.log_issue import LogIssue

_API_BASE = "https://slack.com/api"
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 5
_REQUEST_TIMEOUT_SECONDS = 15.0


class SlackError(Exception):
    """Raised when Slack isn't configured or a notification call fails."""


class SlackClient:
    """Slack Web API client — posts one incident-notification message to
    the configured channel. Only ever called for critical incidents, and
    only after a Jira ticket already exists (see services/slack_service.py
    and project-spec.md "Notifications").
    """

    def __init__(self, bot_token: str | None = None, channel_id: str | None = None) -> None:
        self._token = bot_token if bot_token is not None else SLACK_BOT_TOKEN
        self.channel_id = channel_id if channel_id is not None else SLACK_CHANNEL_ID

        self._client: httpx.Client | None = None
        if self.is_configured:
            self._client = httpx.Client(
                headers={"Authorization": f"Bearer {self._token}"},
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )

    @property
    def is_configured(self) -> bool:
        return bool(self._token and self.channel_id)

    def post_incident_notification(
        self, incident: LogIssue, jira_ticket: JiraTicketReference
    ) -> tuple[str, str, str | None]:
        """Returns (channel_id, message_ts, permalink). Raises SlackError if
        unconfigured or the API call fails.
        """
        if self._client is None:
            raise SlackError("Slack is not configured — set SLACK_BOT_TOKEN and SLACK_CHANNEL_ID.")

        text = (
            f":rotating_light: *Critical incident:* {incident.title}\n"
            f"*Service:* {incident.service or 'unknown'}\n"
            f"*Category:* {incident.category.value}\n"
            f"*Jira ticket:* <{jira_ticket.url}|{jira_ticket.key}>"
        )
        response = self._request(
            "POST", f"{_API_BASE}/chat.postMessage", json={"channel": self.channel_id, "text": text}
        )
        data = response.json()
        if not data.get("ok"):
            raise SlackError(f"Slack chat.postMessage failed: {data.get('error')}")

        channel = data["channel"]
        message_ts = data["ts"]
        permalink = self._get_permalink(channel, message_ts)
        return channel, message_ts, permalink

    def _get_permalink(self, channel: str, message_ts: str) -> str | None:
        # Best-effort only — a missing permalink never blocks the
        # notification itself from counting as sent.
        try:
            response = self._request(
                "GET", f"{_API_BASE}/chat.getPermalink", params={"channel": channel, "message_ts": message_ts}
            )
            data = response.json()
            return data.get("permalink") if data.get("ok") else None
        except SlackError:
            return None

    def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        assert self._client is not None
        last_response: httpx.Response | None = None

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            response = self._client.request(method, url, **kwargs)
            last_response = response

            if response.status_code not in _RETRYABLE_STATUS_CODES:
                return response
            if attempt == _MAX_ATTEMPTS:
                raise SlackError(
                    f"Slack request to {url} failed with {response.status_code} after {_MAX_ATTEMPTS} attempts."
                )

            retry_after = response.headers.get("Retry-After")
            delay = float(retry_after) if retry_after else min(2**attempt, 30)
            delay += random.uniform(0, 0.5)
            time.sleep(delay)

        assert last_response is not None
        return last_response
