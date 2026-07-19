from graph.orchestrator import get_detection_graph, get_incident_workflow_graph
from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.severity import Severity


def test_detection_graph_produces_incidents_from_log_text():
    graph = get_detection_graph()
    log_text = "2024-01-01T00:00:00Z ERROR OOMKilled process=java pid=4821 service=worker-jobs-1"

    final_state = graph.invoke({"log_text": log_text})

    assert "incidents" in final_state
    assert len(final_state["incidents"]) >= 1
    assert final_state["incidents"][0].category == IssueCategory.OOM_KILL


def test_detection_graph_handles_log_with_no_incidents():
    graph = get_detection_graph()
    final_state = graph.invoke({"log_text": "2024-01-01T00:00:00Z INFO service started cleanly"})
    assert final_state["incidents"] == []


def test_detection_graph_is_a_singleton():
    assert get_detection_graph() is get_detection_graph()


def test_incident_workflow_graph_populates_root_cause_via_rca_node():
    incident = LogIssue(
        id="incident-1",
        category=IssueCategory.OOM_KILL,
        severity=Severity.CRITICAL,
        title="Out-of-memory kill detected",
        confidence=0.9,
        raw_excerpt=["Out of memory: Killed process 4821 (java)"],
    )

    result = get_incident_workflow_graph().invoke({"selected_incident": incident})

    assert result["root_cause"] is not None
    assert result["root_cause"].incident_id == "incident-1"
    assert result["root_cause"].evidence


def test_incident_workflow_graph_runs_remediation_node_after_rca():
    # The test suite stubs retrieval to return no chunks (see conftest.py),
    # so recommendations legitimately comes back empty here — the point of
    # this test is that the "remediation" node runs at all, right after
    # "rca", without erroring.
    incident = LogIssue(
        id="incident-2",
        category=IssueCategory.DISK_SPACE_EXHAUSTION,
        severity=Severity.HIGH,
        title="Disk space exhaustion detected",
        confidence=0.85,
        raw_excerpt=["No space left on device"],
    )

    result = get_incident_workflow_graph().invoke({"selected_incident": incident})

    assert result["recommendations"] == []
    assert result["jira_payload"] is None


def test_incident_workflow_graph_runs_cookbook_node_after_remediation():
    incident = LogIssue(
        id="incident-3",
        category=IssueCategory.HTTP_5XX_SPIKE,
        severity=Severity.MEDIUM,
        title="HTTP 5xx spike detected",
        confidence=0.8,
        raw_excerpt=["503 Service Unavailable"],
    )

    result = get_incident_workflow_graph().invoke({"selected_incident": incident})

    assert result["cookbook"] is not None
    assert result["cookbook"].root_cause == result["root_cause"].primary_cause
    # No chunks retrieved (stubbed retriever) means no recommendations to
    # extract commands/validation/rollback from.
    assert result["cookbook"].commands == []
