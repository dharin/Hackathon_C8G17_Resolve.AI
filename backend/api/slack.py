from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from integrations.slack import SlackError
from models.slack_notification import SlackNotificationReference
from models.user import UserIdentity
from services import jira_ticket_store, slack_service
from services.analysis_store import load_analysis

router = APIRouter(prefix="/api/v1", tags=["slack"])


@router.post(
    "/analyses/{analysis_id}/incidents/{incident_id}/notify-slack",
    response_model=SlackNotificationReference,
)
def notify_slack(
    analysis_id: str,
    incident_id: str,
    _user: UserIdentity = Depends(get_current_user),
) -> SlackNotificationReference:
    """Direct Slack notification trigger. Critical incidents are notified
    automatically once a Jira ticket exists (see
    api/analyze.py::get_incident_detail) — this endpoint exists mainly to
    retry a notification that failed automatically. Requires a Jira ticket
    to already exist for this incident (never creates one itself) and only
    ever applies to critical incidents. Idempotent: calling this again for
    an incident already notified just returns the existing reference.
    """
    result = load_analysis(analysis_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for analysis_id '{analysis_id}'.",
        )

    incident = next((issue for issue in result.incidents if issue.id == incident_id), None)
    if incident is None:
        raise HTTPException(
            status_code=404,
            detail=f"No incident '{incident_id}' found in analysis '{analysis_id}'.",
        )

    jira_ticket = jira_ticket_store.get_ticket(analysis_id, incident_id)

    try:
        return slack_service.notify_or_raise(analysis_id, incident, jira_ticket)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except SlackError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
