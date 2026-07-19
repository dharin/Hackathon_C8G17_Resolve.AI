import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from config.settings import UPLOAD_DIR
from graph.orchestrator import get_detection_graph, get_incident_workflow_graph
from models.incident_detail import IncidentDetail
from models.log_issue import LogIssue
from models.severity import Severity
from models.upload_analysis import UploadAnalysisResult
from models.user import UserIdentity
from services import jira_service, jira_ticket_store, slack_notification_store, slack_service
from services.analysis_store import load_analysis, save_analysis

router = APIRouter(prefix="/api/v1", tags=["log-analysis"])


def _find_uploaded_file(upload_id: str) -> Path | None:
    matches = list(UPLOAD_DIR.glob(f"{upload_id}.*"))
    return matches[0] if matches else None


@router.post("/logs/{upload_id}/analyze", response_model=UploadAnalysisResult)
def analyze_log(
    upload_id: str,
    _user: UserIdentity = Depends(get_current_user),
) -> UploadAnalysisResult:
    file_path = _find_uploaded_file(upload_id)
    if file_path is None:
        raise HTTPException(
            status_code=404,
            detail=f"No uploaded log found for upload_id '{upload_id}'.",
        )

    # Read only, never executed or interpreted as code — the Log Reader
    # Agent classifies text patterns, nothing more.
    text = file_path.read_text(encoding="utf-8", errors="replace")
    final_state = get_detection_graph().invoke({"log_text": text})
    incidents = final_state["incidents"]

    result = UploadAnalysisResult(
        analysis_id=uuid.uuid4().hex,
        upload_id=upload_id,
        created_at=datetime.now(timezone.utc),
        total_lines=len(text.splitlines()),
        incidents=incidents,
    )
    # Persisted right after the Log Reader Agent runs; both GET endpoints
    # below read only from this store, never from re-parsing the log.
    save_analysis(result)
    return result


@router.get("/analyses/{analysis_id}/incidents", response_model=list[LogIssue])
def get_analysis_incidents(
    analysis_id: str,
    _user: UserIdentity = Depends(get_current_user),
) -> list[LogIssue]:
    result = load_analysis(analysis_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for analysis_id '{analysis_id}'.",
        )
    return result.incidents


@router.get(
    "/analyses/{analysis_id}/incidents/{incident_id}",
    response_model=IncidentDetail,
)
def get_incident_detail(
    analysis_id: str,
    incident_id: str,
    _user: UserIdentity = Depends(get_current_user),
) -> IncidentDetail:
    """Single-incident detail endpoint. This is the endpoint Phases 7-9
    extend with `rca`, `recommendations`, and `cookbook` — it replaces the
    original `GET /incidents/{id}` contract from project-spec.md, which
    Phase 5 diverged from (see tasks/phase-05-log-reader-agent.md).
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

    # Critical incidents get a Jira ticket automatically, without the user
    # clicking anything (project-spec.md "Notifications" — "Critical
    # only... Automatic"). Idempotent: repeated views of the same incident
    # never create a second ticket (see services/jira_ticket_store.py).
    # Non-critical incidents only ever get a ticket via the manual
    # POST .../create-jira endpoint — this just reflects one if it exists.
    if incident.severity == Severity.CRITICAL:
        jira_ticket = jira_service.ensure_ticket(analysis_id, incident_id, jira_payload)
        # Slack always fires after Jira, never before or independently
        # (project-spec.md "Notifications") — `ensure_notification` itself
        # also gates on severity/jira_ticket, this check just avoids the
        # call entirely when there's nothing yet to notify about.
        slack_notification = (
            slack_service.ensure_notification(analysis_id, incident, jira_ticket)
            if jira_ticket is not None
            else None
        )
    else:
        jira_ticket = jira_ticket_store.get_ticket(analysis_id, incident_id)
        slack_notification = slack_notification_store.get_notification(analysis_id, incident_id)

    return IncidentDetail(
        incident=incident,
        rca=workflow_state.get("root_cause"),
        recommendations=workflow_state.get("recommendations"),
        cookbook=workflow_state.get("cookbook"),
        jira_ticket=jira_ticket,
        slack_notification=slack_notification,
    )
