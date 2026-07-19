from agents.cookbook import CookbookAgent
from agents.rca import RCAAgent
from agents.remediation import RemediationAgent
from graph.state import DetectionState, IncidentWorkflowState
from services.log_reader.agent import LogReaderAgent

_log_reader_agent = LogReaderAgent()
_rca_agent = RCAAgent()
_remediation_agent = RemediationAgent()
_cookbook_agent = CookbookAgent()


def log_reader_node(state: DetectionState) -> dict:
    return {"incidents": _log_reader_agent.analyze(state["log_text"])}


def rca_node(state: IncidentWorkflowState) -> dict:
    return {"root_cause": _rca_agent.analyze(state["selected_incident"])}


def remediation_node(state: IncidentWorkflowState) -> dict:
    recommendations, jira_payload = _remediation_agent.recommend(
        state["selected_incident"], state.get("root_cause")
    )
    return {"recommendations": recommendations, "jira_payload": jira_payload}


def cookbook_node(state: IncidentWorkflowState) -> dict:
    cookbook = _cookbook_agent.build(
        state["selected_incident"],
        state.get("root_cause"),
        state.get("recommendations") or [],
    )
    return {"cookbook": cookbook}
