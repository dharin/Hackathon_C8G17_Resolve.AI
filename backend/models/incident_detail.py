from pydantic import BaseModel

from models.cookbook import Cookbook
from models.jira_ticket import JiraTicketReference
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.recommendation import Recommendation
from models.slack_notification import SlackNotificationReference


class IncidentDetail(BaseModel):
    """Response shape for `GET /analyses/{analysis_id}/incidents/{incident_id}`.

    This is the endpoint later phases extend instead of the original
    `project-spec.md` `GET /incidents/{id}` contract, which Phase 5 diverged
    from (see tasks/phase-05-log-reader-agent.md "API deviation").

    `jira_ticket` is populated automatically for critical incidents (see
    api/analyze.py) and reflects a manually-created ticket (via
    `POST .../create-jira`) for non-critical ones — `None` means no ticket
    exists yet. `slack_notification` is populated automatically, only for
    critical incidents, and only once `jira_ticket` exists — never before
    or independently of it.
    """

    incident: LogIssue
    rca: RCAReport | None = None
    recommendations: list[Recommendation] | None = None
    cookbook: Cookbook | None = None
    jira_ticket: JiraTicketReference | None = None
    slack_notification: SlackNotificationReference | None = None
