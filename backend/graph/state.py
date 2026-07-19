from typing import Any, TypedDict

from models.log_issue import LogIssue
from models.rca_report import RCAReport


class DetectionState(TypedDict, total=False):
    """State for the Upload -> Incidents portion of the pipeline (see
    project-spec.md "LangGraph State"). One run per uploaded log.
    """

    log_text: str
    incidents: list[LogIssue]


class IncidentWorkflowState(TypedDict, total=False):
    """State for the Selected Incident -> RCA -> Remediation -> Cookbook ->
    Notification portion of the pipeline. One run per selected incident.

    `recommendations`, `cookbook`, and `jira_payload` are still typed
    loosely (`dict`) because their Pydantic models don't exist yet — Phase 8
    introduces `Recommendation`/`JiraPayload` and Phase 9 introduces
    `Cookbook`; each should replace its `dict` placeholder here accordingly.
    """

    selected_incident: LogIssue
    root_cause: RCAReport | None
    recommendations: list[dict[str, Any]] | None
    cookbook: dict[str, Any] | None
    jira_payload: dict[str, Any] | None
