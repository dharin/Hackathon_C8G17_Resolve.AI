from pathlib import Path

import pytest

from models.issue_category import IssueCategory
from models.severity import Severity
from services.log_reader.agent import LogReaderAgent

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_logs"


def load_fixture(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def only(issues, category: IssueCategory):
    matches = [i for i in issues if i.category == category]
    assert len(matches) == 1, f"expected exactly one {category} incident, got {len(matches)}"
    return matches[0]


@pytest.fixture
def agent() -> LogReaderAgent:
    return LogReaderAgent()


def test_oom_kill_detected(agent):
    issues = agent.analyze(load_fixture("oom_kill.log"))
    issue = only(issues, IssueCategory.OOM_KILL)
    assert issue.severity == Severity.CRITICAL
    assert issue.service == "worker-jobs-1"
    assert issue.fields.get("process") == "java"
    assert issue.fields.get("pid") == "4821"
    assert issue.timestamp is not None
    assert issue.raw_excerpt
    assert 0.0 <= issue.confidence <= 1.0


def test_disk_space_exhaustion_detected(agent):
    issues = agent.analyze(load_fixture("disk_space_exhaustion.log"))
    issue = only(issues, IssueCategory.DISK_SPACE_EXHAUSTION)
    assert issue.severity == Severity.CRITICAL
    assert issue.service == "worker-jobs-2"
    # two related lines (no-space + 96% full) within the group window merge
    assert issue.fields.get("occurrences") == 2
    assert issue.fields.get("used_percent") == 96


def test_auth_failure_detected_and_escalated(agent):
    issues = agent.analyze(load_fixture("auth_failure.log"))
    issue = only(issues, IssueCategory.AUTH_FAILURE)
    assert issue.service == "auth-service"
    assert issue.fields.get("user") == "jdoe"
    # base severity is medium; 3 repeated occurrences escalate one tier
    assert issue.severity == Severity.HIGH
    assert issue.fields.get("occurrences") == 3


def test_timeout_detected(agent):
    issues = agent.analyze(load_fixture("timeout.log"))
    issue = only(issues, IssueCategory.TIMEOUT)
    assert issue.severity == Severity.MEDIUM
    assert issue.service == "notification-service"
    assert issue.fields.get("duration_ms") == 5000.0


def test_database_connection_error_detected(agent):
    issues = agent.analyze(load_fixture("database_connection_error.log"))
    issue = only(issues, IssueCategory.DATABASE_CONNECTION_ERROR)
    assert issue.severity == Severity.CRITICAL
    assert issue.service == "checkout-api"
    assert issue.fields.get("occurrences") == 2


def test_http_5xx_spike_detected_and_escalated(agent):
    issues = agent.analyze(load_fixture("http_5xx_spike.log"))
    issue = only(issues, IssueCategory.HTTP_5XX_SPIKE)
    assert issue.service == "checkout-api"
    assert issue.fields.get("occurrences") == 4
    assert issue.fields.get("status_codes") == ["500", "503"]
    # base severity is high; 4 occurrences escalate one tier to critical
    assert issue.severity == Severity.CRITICAL


def test_unknown_pattern_not_forced_into_known_category(agent):
    issues = agent.analyze(load_fixture("unknown.log"))
    assert len(issues) == 1
    issue = issues[0]
    assert issue.category == IssueCategory.UNKNOWN
    assert issue.detection_method == "unclassified"
    assert issue.severity == Severity.LOW
    assert issue.service == "payments-webhook"
    # no OPENROUTER_API_KEY in the test environment (see conftest.py), so this
    # must be the low-confidence deterministic fallback, not a fabricated
    # high-confidence guess.
    assert issue.confidence < 0.5


def test_mixed_log_detects_all_incidents_regardless_of_severity(agent):
    issues = agent.analyze(load_fixture("mixed.log"))
    categories = {issue.category for issue in issues}

    assert IssueCategory.DATABASE_CONNECTION_ERROR in categories
    assert IssueCategory.AUTH_FAILURE in categories
    assert IssueCategory.OOM_KILL in categories
    assert IssueCategory.UNKNOWN in categories

    severities = {issue.severity for issue in issues}
    # both low-severity (unknown) and critical incidents must be present —
    # nothing gets filtered out by severity.
    assert Severity.CRITICAL in severities
    assert Severity.LOW in severities

    # the purely informational "queue depth" line has no problem signal and
    # must not become an incident.
    assert not any("queue depth" in "".join(issue.raw_excerpt) for issue in issues)


def test_agent_never_touches_jira_or_slack(agent):
    # Static guarantee: none of the log-reader modules import anything from
    # an integrations package, so they structurally cannot create Jira
    # tickets or send Slack notifications. Checked via imports (not a raw
    # text search) since the code's own docstrings mention "Jira"/"Slack"
    # precisely to document that they're *not* touched.
    import ast

    package_dir = Path(__file__).parent.parent / "services" / "log_reader"
    for py_file in package_dir.glob("*.py"):
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                assert "jira" not in name.lower(), f"{py_file.name} imports {name}"
                assert "slack" not in name.lower(), f"{py_file.name} imports {name}"
                assert "integrations" not in name.lower(), f"{py_file.name} imports {name}"
