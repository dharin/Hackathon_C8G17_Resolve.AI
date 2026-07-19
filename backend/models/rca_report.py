from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AlternativeCause(BaseModel):
    cause: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class RCAReport(BaseModel):
    incident_id: str
    primary_cause: str
    evidence: list[str]
    alternative_causes: list[AlternativeCause] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    generated_at: datetime
    method: Literal["llm", "heuristic"] = "heuristic"
