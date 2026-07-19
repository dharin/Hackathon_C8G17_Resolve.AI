import pytest

from agents.remediation import RemediationAgent
from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.severity import Severity
from rag.models import RetrievedChunk


def make_incident(**overrides) -> LogIssue:
    defaults = dict(
        id="incident-1",
        category=IssueCategory.DATABASE_CONNECTION_ERROR,
        severity=Severity.CRITICAL,
        title="Database connections exhausted",
        service="checkout-api",
        confidence=0.9,
        raw_excerpt=["FATAL connection pool exhausted for db-primary"],
    )
    defaults.update(overrides)
    return LogIssue(**defaults)


def make_rca(**overrides) -> RCAReport:
    from datetime import datetime, timezone

    defaults = dict(
        incident_id="incident-1",
        primary_cause="The database exhausted its connection pool.",
        evidence=["FATAL connection pool exhausted for db-primary"],
        alternative_causes=[],
        confidence=0.9,
        generated_at=datetime.now(timezone.utc),
        method="heuristic",
    )
    defaults.update(overrides)
    return RCAReport(**defaults)


def make_chunk(**overrides) -> RetrievedChunk:
    defaults = dict(
        chunk_id="local-sop:db-runbook.md:v1:chunk-0",
        content="Restart the pgbouncer pool and verify max_connections is not exceeded.",
        score=0.87,
        source_type="local_sop",
        title="Database Connection Pool Runbook",
        source_uri="runbooks/db-pool.md",
        section_path=["Troubleshooting"],
        updated_at=None,
        metadata={},
    )
    defaults.update(overrides)
    return RetrievedChunk(**defaults)


class FakeRetriever:
    def __init__(self, chunks: list[RetrievedChunk]):
        self._chunks = chunks
        self.last_query = None

    def retrieve(self, query, limit=10, **kwargs):
        self.last_query = query
        return self._chunks[:limit]


@pytest.fixture
def agent_with_chunks():
    retriever = FakeRetriever([make_chunk()])
    return RemediationAgent(retriever=retriever), retriever


def test_no_chunks_returns_no_recommendations_and_no_jira_payload():
    agent = RemediationAgent(retriever=FakeRetriever([]))
    recommendations, jira_payload = agent.recommend(make_incident(), make_rca())
    assert recommendations == []
    assert jira_payload is None


def test_recommendation_is_grounded_in_retrieved_chunk(agent_with_chunks):
    agent, retriever = agent_with_chunks
    recommendations, _ = agent.recommend(make_incident(), make_rca())

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert rec.sources == [make_chunk()]
    assert 0.0 <= rec.confidence <= 1.0
    assert rec.title
    assert rec.rationale
    assert retriever.last_query == "The database exhausted its connection pool."


def test_query_falls_back_to_incident_title_when_no_rca():
    retriever = FakeRetriever([make_chunk()])
    agent = RemediationAgent(retriever=retriever)
    agent.recommend(make_incident(), None)
    assert retriever.last_query == "Database connections exhausted"


def test_every_recommendation_has_at_least_one_source(agent_with_chunks):
    agent, _ = agent_with_chunks
    recommendations, _ = agent.recommend(make_incident(), make_rca())
    for rec in recommendations:
        assert len(rec.sources) >= 1


def test_recommendations_ranked_by_confidence_descending():
    chunks = [
        make_chunk(chunk_id="a", score=0.5, title="Doc A"),
        make_chunk(chunk_id="b", score=0.9, title="Doc B"),
        make_chunk(chunk_id="c", score=0.7, title="Doc C"),
    ]
    agent = RemediationAgent(retriever=FakeRetriever(chunks))
    recommendations, _ = agent.recommend(make_incident(), make_rca())
    confidences = [r.confidence for r in recommendations]
    assert confidences == sorted(confidences, reverse=True)


def test_jira_payload_built_from_top_recommendation(agent_with_chunks):
    agent, _ = agent_with_chunks
    recommendations, jira_payload = agent.recommend(make_incident(), make_rca())

    assert jira_payload is not None
    assert jira_payload.incident_id == "incident-1"
    assert jira_payload.priority == "Highest"  # CRITICAL severity
    assert "checkout-api" in jira_payload.labels
    assert recommendations[0].title in jira_payload.description


def test_priority_maps_from_severity():
    agent = RemediationAgent(retriever=FakeRetriever([make_chunk()]))
    _, jira_payload = agent.recommend(make_incident(severity=Severity.LOW), make_rca())
    assert jira_payload.priority == "Low"


def test_heuristic_rationale_never_exceeds_reasonable_length(agent_with_chunks):
    agent, _ = agent_with_chunks
    long_content = "word " * 500
    retriever = FakeRetriever([make_chunk(content=long_content)])
    agent = RemediationAgent(retriever=retriever)
    recommendations, _ = agent.recommend(make_incident(), make_rca())
    assert len(recommendations[0].rationale) < 300
