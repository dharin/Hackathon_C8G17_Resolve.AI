from pathlib import Path

import pytest

from services import slack_notification_store


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(
        slack_notification_store, "SLACK_NOTIFICATIONS_DB_PATH", tmp_path / "slack_notifications.sqlite3"
    )


def test_get_missing_notification_returns_none():
    assert slack_notification_store.get_notification("analysis-1", "incident-1") is None


def test_save_and_get_notification_round_trips():
    saved = slack_notification_store.save_notification(
        "analysis-1", "incident-1", "C123", "1700000000.000100", "https://x.slack.com/archives/C123/p1"
    )
    loaded = slack_notification_store.get_notification("analysis-1", "incident-1")

    assert loaded is not None
    assert loaded.channel_id == "C123"
    assert loaded.message_ts == "1700000000.000100"
    assert loaded.permalink == "https://x.slack.com/archives/C123/p1"
    assert loaded.sent_at == saved.sent_at


def test_save_notification_upserts_rather_than_duplicating():
    slack_notification_store.save_notification("analysis-1", "incident-1", "C123", "111.1", None)
    slack_notification_store.save_notification("analysis-1", "incident-1", "C123", "222.2", None)

    loaded = slack_notification_store.get_notification("analysis-1", "incident-1")
    assert loaded.message_ts == "222.2"


def test_notifications_are_scoped_per_analysis_and_incident():
    slack_notification_store.save_notification("analysis-1", "incident-1", "C123", "111.1", None)
    assert slack_notification_store.get_notification("analysis-2", "incident-1") is None
    assert slack_notification_store.get_notification("analysis-1", "incident-2") is None


def test_permalink_can_be_none():
    saved = slack_notification_store.save_notification("analysis-1", "incident-1", "C123", "111.1", None)
    assert saved.permalink is None
    assert slack_notification_store.get_notification("analysis-1", "incident-1").permalink is None
