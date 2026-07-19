from datetime import datetime

from pydantic import BaseModel


class SlackNotificationReference(BaseModel):
    """The result of a Slack notification send — what the UI reports as
    "notified" and links back to.
    """

    channel_id: str
    message_ts: str
    permalink: str | None = None
    sent_at: datetime
