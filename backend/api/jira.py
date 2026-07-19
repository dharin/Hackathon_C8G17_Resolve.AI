from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from graph.orchestrator import get_incident_workflow_graph
from integrations.jira import JiraError
from models.jira_ticket import JiraTicketReference
from models.user import UserIdentity
from services import jira_service
from services.analysis_store import load_analysis

router = APIRouter(prefix="/api/v1", tags=["jira"])


@router.post(
    "/analyses/{analysis_id}/incidents/{incident_id}/create-jira",
    response_model=JiraTicketReference,
)
def create_jira_ticket(
    analysis_id: str,
    incident_id: str,
    _user: UserIdentity = Depends(get_current_user),
) -> JiraTicketReference:
    """Manual Jira ticket creation, primarily for non-critical incidents
    (critical incidents are ticketed automatically — see
    api/analyze.py::get_incident_detail). Idempotent: calling this again
    for an incident that already has a ticket just returns the existing
    reference rather than creating a duplicate.
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

    workflow_state = get_incident_workflow_graph().invoke({"selected_incident": incident})
    jira_payload = workflow_state.get("jira_payload")

    try:
        return jira_service.create_ticket_or_raise(analysis_id, incident_id, jira_payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except JiraError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
