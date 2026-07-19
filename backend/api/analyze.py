import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_current_user
from config.settings import UPLOAD_DIR
from models.log_issue import LogIssue
from models.upload_analysis import UploadAnalysisResult
from models.user import UserIdentity
from services.analysis_store import load_analysis, save_analysis
from services.log_reader.agent import LogReaderAgent

router = APIRouter(prefix="/api/v1", tags=["log-analysis"])

_agent = LogReaderAgent()


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
    incidents = _agent.analyze(text)

    result = UploadAnalysisResult(
        analysis_id=uuid.uuid4().hex,
        upload_id=upload_id,
        created_at=datetime.now(timezone.utc),
        total_lines=len(text.splitlines()),
        incidents=incidents,
    )
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
