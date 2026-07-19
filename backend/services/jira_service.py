import logging

from integrations.jira import JiraClient, JiraError
from models.jira_payload import JiraPayload
from models.jira_ticket import JiraTicketReference
from services import jira_ticket_store

logger = logging.getLogger(__name__)


def ensure_ticket(
    analysis_id: str, incident_id: str, jira_payload: JiraPayload | None
) -> JiraTicketReference | None:
    """Idempotent, best-effort creation for the automatic (critical-incident)
    path: returns the existing ticket if one was already created for this
    incident, otherwise creates one from `jira_payload`. Returns None
    (never raises) when there's nothing to do — no payload, Jira not
    configured, or the API call failed — so this is safe to call
    opportunistically without failing the whole incident-detail request.
    """
    existing = jira_ticket_store.get_ticket(analysis_id, incident_id)
    if existing is not None:
        return existing

    if jira_payload is None:
        return None

    client = JiraClient()
    if not client.is_configured:
        return None

    try:
        key, url = client.create_issue(jira_payload)
    except JiraError as exc:
        logger.warning("Automatic Jira ticket creation failed for incident %s: %s", incident_id, exc)
        return None

    return jira_ticket_store.save_ticket(analysis_id, incident_id, key, url)


def create_ticket_or_raise(
    analysis_id: str, incident_id: str, jira_payload: JiraPayload | None
) -> JiraTicketReference:
    """Same idempotency as `ensure_ticket`, but raises instead of swallowing
    failures — for the manual `POST /create-jira` endpoint, where the user
    clicking the button should see a real error. Raises `ValueError` when
    there's no grounded payload to build a ticket from (a client-fixable
    422, not a Jira-side failure) and `JiraError` for everything else
    (unconfigured Jira, or the API call itself failing).
    """
    existing = jira_ticket_store.get_ticket(analysis_id, incident_id)
    if existing is not None:
        return existing

    if jira_payload is None:
        raise ValueError("No grounded remediation available to build a Jira ticket from.")

    client = JiraClient()
    key, url = client.create_issue(jira_payload)
    return jira_ticket_store.save_ticket(analysis_id, incident_id, key, url)
