from typing import TypedDict

from models.cookbook import Cookbook
from models.jira_payload import JiraPayload
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.recommendation import Recommendation


class DetectionState(TypedDict, total=False):
    """State for the Upload -> Incidents portion of the pipeline (see
    project-spec.md "LangGraph State"). One run per uploaded log.
    """

    log_text: str
    incidents: list[LogIssue]


class IncidentWorkflowState(TypedDict, total=False):
    """State for the Selected Incident -> RCA -> Remediation -> Cookbook ->
    Notification portion of the pipeline. One run per selected incident.
    """

    selected_incident: LogIssue
    root_cause: RCAReport | None
    recommendations: list[Recommendation] | None
    cookbook: Cookbook | None
    jira_payload: JiraPayload | None
