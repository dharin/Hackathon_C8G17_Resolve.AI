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
