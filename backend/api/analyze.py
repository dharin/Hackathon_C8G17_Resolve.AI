import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from config.settings import UPLOAD_DIR
from graph.orchestrator import get_detection_graph, get_incident_workflow_graph
from models.incident_detail import IncidentDetail
from models.log_issue import LogIssue
from models.upload_analysis import UploadAnalysisResult
from models.user import UserIdentity
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
    return IncidentDetail(
        incident=incident,
        rca=workflow_state.get("root_cause"),
        recommendations=workflow_state.get("recommendations"),
        cookbook=workflow_state.get("cookbook"),
    )
