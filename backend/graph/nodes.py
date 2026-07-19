from agents.rca import RCAAgent
from graph.state import DetectionState, IncidentWorkflowState
from services.log_reader.agent import LogReaderAgent

_log_reader_agent = LogReaderAgent()
_rca_agent = RCAAgent()


def log_reader_node(state: DetectionState) -> dict:
    return {"incidents": _log_reader_agent.analyze(state["log_text"])}


def rca_node(state: IncidentWorkflowState) -> dict:
    return {"root_cause": _rca_agent.analyze(state["selected_incident"])}
