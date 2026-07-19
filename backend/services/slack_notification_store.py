import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config.settings import SLACK_NOTIFICATIONS_DB_PATH
from models.slack_notification import SlackNotificationReference

_SCHEMA = """
CREATE TABLE IF NOT EXISTS slack_notifications (
    analysis_id TEXT NOT NULL,
    incident_id TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    message_ts TEXT NOT NULL,
    permalink TEXT,
    sent_at TEXT NOT NULL,
    PRIMARY KEY (analysis_id, incident_id)
);
"""

# Exists for exactly one reason: a Slack notification is an external side
# effect that must never fire twice for the same incident. Not a general
# workflow-state tracker — see services/jira_ticket_store.py for the same
# pattern and rationale.


@contextmanager
def _connect():
    path: Path = SLACK_NOTIFICATIONS_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_notification(analysis_id: str, incident_id: str) -> SlackNotificationReference | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT channel_id, message_ts, permalink, sent_at FROM slack_notifications "
            "WHERE analysis_id = ? AND incident_id = ?",
            (analysis_id, incident_id),
        ).fetchone()
    if row is None:
        return None
    return SlackNotificationReference(
        channel_id=row["channel_id"],
        message_ts=row["message_ts"],
        permalink=row["permalink"],
        sent_at=datetime.fromisoformat(row["sent_at"]),
    )


def save_notification(
    analysis_id: str, incident_id: str, channel_id: str, message_ts: str, permalink: str | None
) -> SlackNotificationReference:
    notification = SlackNotificationReference(
        channel_id=channel_id, message_ts=message_ts, permalink=permalink, sent_at=datetime.now(timezone.utc)
    )
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO slack_notifications "
            "(analysis_id, incident_id, channel_id, message_ts, permalink, sent_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                analysis_id,
                incident_id,
                notification.channel_id,
                notification.message_ts,
                notification.permalink,
                notification.sent_at.isoformat(),
            ),
        )
    return notification
