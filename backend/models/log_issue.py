from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from models.issue_category import IssueCategory
from models.severity import Severity


class LogIssue(BaseModel):
    id: str
    category: IssueCategory
    severity: Severity
    title: str
    service: str | None = None
    timestamp: datetime | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    fields: dict[str, Any] = Field(default_factory=dict)
    raw_excerpt: list[str] = Field(default_factory=list)
    detection_method: Literal["rule", "llm", "unclassified"] = "rule"
