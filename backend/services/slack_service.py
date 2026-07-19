import logging

from integrations.slack import SlackClient, SlackError
from models.jira_ticket import JiraTicketReference
from models.log_issue import LogIssue
from models.severity import Severity
from models.slack_notification import SlackNotificationReference
from services import slack_notification_store

logger = logging.getLogger(__name__)


def ensure_notification(
    analysis_id: str,
    incident: LogIssue,
    jira_ticket: JiraTicketReference | None,
) -> SlackNotificationReference | None:
    """Idempotent, best-effort Slack notification for the automatic path:
    returns the existing notification if one was already sent for this
    incident, otherwise sends one — but only for a CRITICAL incident that
    already has a Jira ticket (see project-spec.md "Notifications" — Slack
    always fires after Jira, never before or independently). Returns None
    (never raises) whenever there's nothing to do, so this is safe to call
    opportunistically without failing the whole incident-detail request.
    """
    if incident.severity != Severity.CRITICAL or jira_ticket is None:
        return None

    existing = slack_notification_store.get_notification(analysis_id, incident.id)
    if existing is not None:
        return existing

    client = SlackClient()
    if not client.is_configured:
        return None

    try:
        channel, message_ts, permalink = client.post_incident_notification(incident, jira_ticket)
    except SlackError as exc:
        logger.warning("Slack notification failed for incident %s: %s", incident.id, exc)
        return None

    return slack_notification_store.save_notification(analysis_id, incident.id, channel, message_ts, permalink)


def notify_or_raise(
    analysis_id: str,
    incident: LogIssue,
    jira_ticket: JiraTicketReference | None,
) -> SlackNotificationReference:
    """Same idempotency and critical-only/after-Jira gating as
    `ensure_notification`, but raises instead of swallowing failures — for
    a direct `POST /notify-slack` call, where the caller should see a real
    error rather than silence.
    """
    if incident.severity != Severity.CRITICAL:
        raise ValueError("Slack notifications are only sent for critical incidents.")
    if jira_ticket is None:
        raise ValueError("A Jira ticket must exist before a Slack notification can be sent.")

    existing = slack_notification_store.get_notification(analysis_id, incident.id)
    if existing is not None:
        return existing

    client = SlackClient()
    channel, message_ts, permalink = client.post_incident_notification(incident, jira_ticket)
    return slack_notification_store.save_notification(analysis_id, incident.id, channel, message_ts, permalink)
