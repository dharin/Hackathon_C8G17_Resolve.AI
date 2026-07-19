from datetime import datetime, timezone

from agents.cookbook import CookbookAgent
from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.recommendation import Recommendation
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
        content="Restart the pool.",
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


def make_recommendation(chunk: RetrievedChunk, **overrides) -> Recommendation:
    defaults = dict(
        title=f'Follow guidance in "{chunk.title}"',
        confidence=chunk.score,
        rationale="Some rationale.",
        sources=[chunk],
    )
    defaults.update(overrides)
    return Recommendation(**defaults)


def test_root_cause_comes_from_rca():
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [])
    assert cookbook.root_cause == "The database exhausted its connection pool."


def test_root_cause_falls_back_to_incident_title_without_rca():
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), None, [])
    assert cookbook.root_cause == "Database connections exhausted"


def test_steps_map_one_to_one_with_recommendation_titles():
    chunk = make_chunk()
    rec = make_recommendation(chunk, title="Restart the pgbouncer pool")
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [rec])
    assert cookbook.steps == ["Restart the pgbouncer pool"]


def test_commands_extracted_only_from_fenced_code_blocks():
    chunk = make_chunk(
        content=(
            "Restart the pool using the following steps.\n"
            "```bash\n"
            "systemctl restart pgbouncer\n"
            "kubectl rollout status deployment/checkout-api\n"
            "```\n"
            "This should resolve the issue."
        )
    )
    rec = make_recommendation(chunk)
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [rec])
    assert cookbook.commands == [
        "systemctl restart pgbouncer",
        "kubectl rollout status deployment/checkout-api",
    ]


def test_no_commands_invented_when_source_has_no_code_block():
    chunk = make_chunk(content="Just restart the service manually, no script provided.")
    rec = make_recommendation(chunk)
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [rec])
    assert cookbook.commands == []


def test_validation_sentences_extracted_by_keyword():
    chunk = make_chunk(
        content=(
            "Restart the pool. Verify the connection count drops below 80. "
            "Confirm checkout-api error rate returns to baseline."
        )
    )
    rec = make_recommendation(chunk)
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [rec])
    assert any("Verify the connection count" in v for v in cookbook.validation)
    assert any("Confirm checkout-api error rate" in v for v in cookbook.validation)


def test_rollback_sentences_extracted_by_keyword():
    chunk = make_chunk(
        content="Apply the config change. If it fails, roll back to the previous revision immediately."
    )
    rec = make_recommendation(chunk)
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [rec])
    assert any("roll back to the previous revision" in r for r in cookbook.rollback)


def test_empty_recommendations_produce_empty_but_non_null_cookbook():
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), [])
    assert cookbook.steps == []
    assert cookbook.commands == []
    assert cookbook.validation == []
    assert cookbook.rollback == []
    assert cookbook.root_cause


def test_duplicate_commands_across_sources_are_deduped():
    chunk_a = make_chunk(chunk_id="a", content="```\nsystemctl restart pgbouncer\n```")
    chunk_b = make_chunk(chunk_id="b", content="```\nsystemctl restart pgbouncer\n```")
    recs = [make_recommendation(chunk_a), make_recommendation(chunk_b)]
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), recs)
    assert cookbook.commands == ["systemctl restart pgbouncer"]


def test_duplicate_recommendation_titles_are_deduped_in_steps():
    # Two chunks from the same source document commonly produce identical
    # heuristic titles (see agents/remediation.py) — steps must not repeat
    # the same instruction twice, and every title must stay unique so the
    # UI can key each rendered step safely.
    chunk_a = make_chunk(chunk_id="a", title="Database Runbook")
    chunk_b = make_chunk(chunk_id="b", title="Database Runbook")
    recs = [
        make_recommendation(chunk_a, title='Follow guidance in "Database Runbook"'),
        make_recommendation(chunk_b, title='Follow guidance in "Database Runbook"'),
    ]
    agent = CookbookAgent()
    cookbook = agent.build(make_incident(), make_rca(), recs)
    assert cookbook.steps == ['Follow guidance in "Database Runbook"']
