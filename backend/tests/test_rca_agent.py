import pytest

from agents.rca import RCAAgent
from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.severity import Severity


def make_incident(category: IssueCategory, **overrides) -> LogIssue:
    defaults = dict(
        id="incident-1",
        category=category,
        severity=Severity.CRITICAL,
        title="Something broke",
        service="worker-1",
        confidence=0.9,
        fields={},
        raw_excerpt=["ERROR something happened on worker-1"],
        detection_method="rule",
    )
    defaults.update(overrides)
    return LogIssue(**defaults)


@pytest.fixture
def agent() -> RCAAgent:
    return RCAAgent()


def test_heuristic_report_is_returned_when_no_llm_key_configured(agent):
    # conftest.py blanks OPENROUTER_API_KEY for the whole suite.
    incident = make_incident(IssueCategory.OOM_KILL)
    report = agent.analyze(incident)

    assert report.method == "heuristic"
    assert report.incident_id == "incident-1"
    assert report.primary_cause
    assert report.confidence == incident.confidence


def test_evidence_is_traceable_to_the_incidents_raw_excerpt(agent):
    incident = make_incident(
        IssueCategory.DATABASE_CONNECTION_ERROR,
        raw_excerpt=["FATAL connection pool exhausted for db-primary"],
    )
    report = agent.analyze(incident)

    assert report.evidence
    assert all(line in incident.raw_excerpt for line in report.evidence)
    for alt in report.alternative_causes:
        assert all(line in incident.raw_excerpt for line in alt.evidence)


def test_every_known_category_has_a_grounded_report(agent):
    for category in IssueCategory:
        incident = make_incident(category)
        report = agent.analyze(incident)
        assert report.primary_cause
        assert report.evidence
        assert 0.0 <= report.confidence <= 1.0


def test_report_never_contains_a_fix_suggestion(agent):
    fix_keywords = (
        "restart",
        "rollback",
        "patch",
        "upgrade",
        "increase",
        "recommend",
        "fix",
        "resolve",
        "remediat",
        "mitigat",
        "workaround",
    )
    for category in IssueCategory:
        report = agent.analyze(make_incident(category))
        combined_text = report.primary_cause + " " + " ".join(a.cause for a in report.alternative_causes)
        lowered = combined_text.lower()
        assert not any(keyword in lowered for keyword in fix_keywords), (
            f"{category}: RCA text reads like a fix suggestion: {combined_text!r}"
        )


def test_alternative_causes_have_lower_confidence_than_primary(agent):
    incident = make_incident(IssueCategory.HTTP_5XX_SPIKE, confidence=0.9)
    report = agent.analyze(incident)
    for alt in report.alternative_causes:
        assert alt.confidence < report.confidence


def test_missing_raw_excerpt_falls_back_to_title_as_evidence(agent):
    incident = make_incident(IssueCategory.TIMEOUT, raw_excerpt=[])
    report = agent.analyze(incident)
    assert report.evidence == [incident.title]
