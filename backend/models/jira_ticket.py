from datetime import datetime

from pydantic import BaseModel


class JiraTicketReference(BaseModel):
    """The result of a Jira ticket creation call — what the UI links to."""

    key: str
    url: str
    created_at: datetime
