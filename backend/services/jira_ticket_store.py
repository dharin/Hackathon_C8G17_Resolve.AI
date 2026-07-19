import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config.settings import JIRA_TICKETS_DB_PATH
from models.jira_ticket import JiraTicketReference

_SCHEMA = """
CREATE TABLE IF NOT EXISTS jira_tickets (
    analysis_id TEXT NOT NULL,
    incident_id TEXT NOT NULL,
    ticket_key TEXT NOT NULL,
    ticket_url TEXT NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (analysis_id, incident_id)
);
"""

# This store exists for exactly one reason: Jira ticket creation is an
# external side effect that must never happen twice for the same incident.
# It is not a general workflow-state tracker — see the RCA/Remediation/
# Cookbook agents, which are recomputed on request rather than persisted.


@contextmanager
def _connect():
    path: Path = JIRA_TICKETS_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def get_ticket(analysis_id: str, incident_id: str) -> JiraTicketReference | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT ticket_key, ticket_url, created_at FROM jira_tickets "
            "WHERE analysis_id = ? AND incident_id = ?",
            (analysis_id, incident_id),
        ).fetchone()
    if row is None:
        return None
    return JiraTicketReference(
        key=row["ticket_key"], url=row["ticket_url"], created_at=datetime.fromisoformat(row["created_at"])
    )


def save_ticket(analysis_id: str, incident_id: str, key: str, url: str) -> JiraTicketReference:
    ticket = JiraTicketReference(key=key, url=url, created_at=datetime.now(timezone.utc))
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO jira_tickets (analysis_id, incident_id, ticket_key, ticket_url, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (analysis_id, incident_id, ticket.key, ticket.url, ticket.created_at.isoformat()),
        )
    return ticket
