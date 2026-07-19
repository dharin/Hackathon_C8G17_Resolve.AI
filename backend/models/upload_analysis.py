from datetime import datetime

from pydantic import BaseModel

from models.log_issue import LogIssue


class UploadAnalysisResult(BaseModel):
    analysis_id: str
    upload_id: str
    created_at: datetime
    total_lines: int
    incidents: list[LogIssue]
