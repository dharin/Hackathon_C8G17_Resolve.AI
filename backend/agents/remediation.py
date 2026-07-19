import json

from config.settings import OPENROUTER_API_KEY, OPENROUTER_MODEL
from models.jira_payload import JiraPayload
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.recommendation import Recommendation
from models.severity import Severity
from rag.models import RetrievedChunk
from rag.pipeline import get_retriever
from rag.retriever import Retriever

# OpenRouter exposes an OpenAI-compatible Chat Completions API (see
# services/log_reader/llm_classifier.py and agents/rca.py for the same
# pattern).
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
_RETRIEVAL_LIMIT = 3
_SNIPPET_MAX_CHARS = 120

_PRIORITY_BY_SEVERITY: dict[Severity, str] = {
    Severity.CRITICAL: "Highest",
    Severity.HIGH: "High",
    Severity.MEDIUM: "Medium",
    Severity.LOW: "Low",
}

_SYSTEM_PROMPT = (
    "You write a single short, actionable remediation recommendation grounded "
    "strictly in one retrieved document excerpt. Given a root cause and the "
    "excerpt, respond with a concise imperative title (e.g. 'Restart the "
    "connection pool') and a one-sentence rationale explaining why this "
    "excerpt supports it. Never invent information not present in the "
    "excerpt and never reference any source other than the one given. "
    'Respond with strict JSON: {"title": str, "rationale": str}.'
)


class RemediationAgent:
    """Recommends grounded remediations for a selected incident's RCA,
    retrieved from Confluence/local SOPs via the Phase 6 RAG pipeline.

    Never hallucinates: every recommendation is built from an actually
    retrieved chunk (enforced by `Recommendation.sources` requiring at
    least one entry), and an empty retrieval result yields an empty
    recommendation list — see project-spec.md "Remediation" ("No
    supporting documentation found."). An LLM, if configured, may draft
    more natural title/rationale text, but only from the same retrieved
    excerpt; it never introduces a new source.
    """

    def __init__(self, retriever: Retriever | None = None) -> None:
        self._retriever = retriever

    def recommend(
        self, incident: LogIssue, rca: RCAReport | None
    ) -> tuple[list[Recommendation], JiraPayload | None]:
        query = rca.primary_cause if rca else incident.title
        retriever = self._retriever or get_retriever()
        chunks = retriever.retrieve(query, limit=_RETRIEVAL_LIMIT)

        if not chunks:
            return [], None

        recommendations = [self._build_recommendation(chunk) for chunk in chunks]
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        jira_payload = self._build_jira_payload(incident, rca, recommendations[0])
        return recommendations, jira_payload

    def _build_recommendation(self, chunk: RetrievedChunk) -> Recommendation:
        drafted = self._draft_with_llm(chunk) if OPENROUTER_API_KEY else None
        title, rationale = drafted or self._draft_heuristically(chunk)
        return Recommendation(
            title=title,
            confidence=chunk.score,
            rationale=rationale,
            sources=[chunk],
        )

    def _draft_heuristically(self, chunk: RetrievedChunk) -> tuple[str, str]:
        snippet = " ".join(chunk.content.split())
        if len(snippet) > _SNIPPET_MAX_CHARS:
            snippet = snippet[:_SNIPPET_MAX_CHARS].rsplit(" ", 1)[0] + "…"
        title = f'Follow guidance in "{chunk.title}"'
        rationale = snippet or f"Relevant {chunk.source_type} documentation found for this incident."
        return title, rationale

    def _draft_with_llm(self, chunk: RetrievedChunk) -> tuple[str, str] | None:
        try:
            from openai import OpenAI
        except ImportError:
            return None

        user_payload = {
            "document_title": chunk.title,
            "document_excerpt": chunk.content[:2000],
        }

        try:
            client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=_OPENROUTER_BASE_URL)
            response = client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(user_payload)},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                timeout=15,
            )
            payload = json.loads(response.choices[0].message.content)
        except Exception:
            return None

        title = str(payload.get("title") or "").strip()
        rationale = str(payload.get("rationale") or "").strip()
        if not title or not rationale:
            return None
        return title, rationale

    def _build_jira_payload(
        self, incident: LogIssue, rca: RCAReport | None, top: Recommendation
    ) -> JiraPayload:
        source = top.sources[0]
        description_lines = [f"Incident: {incident.title}"]
        if rca:
            description_lines.append(f"Root cause: {rca.primary_cause}")
        description_lines.append(f"Recommended action: {top.title} — {top.rationale}")
        description_lines.append(
            f"Source: {source.title} ({source.source_type}) — {source.source_uri}"
        )

        labels = [incident.category.value]
        if incident.service:
            labels.append(incident.service)

        return JiraPayload(
            incident_id=incident.id,
            summary=f"[{incident.severity.value.upper()}] {incident.title}",
            description="\n".join(description_lines),
            priority=_PRIORITY_BY_SEVERITY.get(incident.severity, "Medium"),
            labels=labels,
        )
