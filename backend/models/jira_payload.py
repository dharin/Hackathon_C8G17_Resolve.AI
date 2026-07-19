from pydantic import BaseModel, Field


class JiraPayload(BaseModel):
    """Draft Jira ticket payload built by the Remediation Agent. Ticket
    creation itself is Phase 10's job — this only prepares the content.
    """

    incident_id: str
    summary: str
    description: str
    priority: str
    issue_type: str = "Incident"
    labels: list[str] = Field(default_factory=list)
