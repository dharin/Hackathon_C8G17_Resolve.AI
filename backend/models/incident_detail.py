from typing import Any

from pydantic import BaseModel

from models.log_issue import LogIssue
from models.rca_report import RCAReport


class IncidentDetail(BaseModel):
    """Response shape for `GET /analyses/{analysis_id}/incidents/{incident_id}`.

    This is the endpoint later phases extend instead of the original
    `project-spec.md` `GET /incidents/{id}` contract, which Phase 5 diverged
    from (see tasks/phase-05-log-reader-agent.md "API deviation"):
    - Phase 8 populates `recommendations` (replace `dict` with
      `Recommendation` once that model exists).
    - Phase 9 populates `cookbook` (replace `dict` with `Cookbook` once that
      model exists).
    """

    incident: LogIssue
    rca: RCAReport | None = None
    recommendations: list[dict[str, Any]] | None = None
    cookbook: dict[str, Any] | None = None
