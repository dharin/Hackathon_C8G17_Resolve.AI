from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from graph.nodes import cookbook_node, log_reader_node, rca_node, remediation_node
from graph.state import DetectionState, IncidentWorkflowState


@lru_cache(maxsize=1)
def get_detection_graph() -> CompiledStateGraph:
    """Upload -> Incidents. Invoked once per uploaded log by
    `POST /api/v1/logs/{upload_id}/analyze`.
    """
    graph = StateGraph(DetectionState)
    graph.add_node("log_reader", log_reader_node)
    graph.add_edge(START, "log_reader")
    graph.add_edge("log_reader", END)
    return graph.compile()


@lru_cache(maxsize=1)
def get_incident_workflow_graph() -> CompiledStateGraph:
    """Selected Incident -> RCA -> Remediation -> Cookbook -> Notification.

    Phase 7 added "rca". Phase 8 added "remediation". Phase 9 adds
    "cookbook" between "remediation" and END. Notification (Phase 11)
    is the only remaining stage.
    """
    graph = StateGraph(IncidentWorkflowState)
    graph.add_node("rca", rca_node)
    graph.add_node("remediation", remediation_node)
    graph.add_node("cookbook", cookbook_node)
    graph.add_edge(START, "rca")
    graph.add_edge("rca", "remediation")
    graph.add_edge("remediation", "cookbook")
    graph.add_edge("cookbook", END)
    return graph.compile()
