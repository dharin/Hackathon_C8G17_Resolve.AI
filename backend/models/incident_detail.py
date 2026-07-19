from pydantic import BaseModel

from models.cookbook import Cookbook
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.recommendation import Recommendation


class IncidentDetail(BaseModel):
    """Response shape for `GET /analyses/{analysis_id}/incidents/{incident_id}`.

    This is the endpoint later phases extend instead of the original
    `project-spec.md` `GET /incidents/{id}` contract, which Phase 5 diverged
    from (see tasks/phase-05-log-reader-agent.md "API deviation").
    """

    incident: LogIssue
    rca: RCAReport | None = None
    recommendations: list[Recommendation] | None = None
    cookbook: Cookbook | None = None
