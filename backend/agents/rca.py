import json
import re
from datetime import datetime, timezone

from config.settings import OPENROUTER_API_KEY, OPENROUTER_MODEL
from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.rca_report import AlternativeCause, RCAReport

# OpenRouter exposes an OpenAI-compatible Chat Completions API (see
# services/log_reader/llm_classifier.py for the same pattern).
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_SYSTEM_PROMPT = (
    "You perform root cause analysis for a single DevOps incident, given its "
    "category, severity, extracted fields, and raw log excerpt. Identify the "
    "most likely primary cause, quote the evidence (verbatim lines from the "
    "excerpt) that supports it, list plausible alternative causes each with "
    "their own confidence and evidence, and give an overall confidence "
    "between 0 and 1. Never suggest a fix, remediation, workaround, or next "
    "step of any kind — that is a separate agent's job. Only describe what "
    "happened and why, grounded strictly in the excerpt provided. "
    'Respond with strict JSON: {"primary_cause": str, "evidence": [str], '
    '"alternative_causes": [{"cause": str, "confidence": number, "evidence": [str]}], '
    '"confidence": number}.'
)

# Deterministic, offline-safe default per category. Also the fallback when
# an LLM is unavailable, ungrounded, or reads as a fix suggestion.
_CAUSE_TEMPLATES: dict[IssueCategory, tuple[str, list[str]]] = {
    IssueCategory.OOM_KILL: (
        "The process was terminated by the kernel's OOM killer after exceeding available memory.",
        [
            "Memory leak or unbounded growth in the killed process.",
            "Insufficient memory limit configured for the workload.",
        ],
    ),
    IssueCategory.DISK_SPACE_EXHAUSTION: (
        "The filesystem ran out of available space, blocking further writes.",
        [
            "Log or temp files accumulating without rotation.",
            "A runaway process writing excessive data to disk.",
        ],
    ),
    IssueCategory.AUTH_FAILURE: (
        "Authentication was rejected, repeatedly, against the target service.",
        [
            "Expired or rotated credentials not yet updated at the caller.",
            "A brute-force or credential-stuffing attempt.",
        ],
    ),
    IssueCategory.TIMEOUT: (
        "The operation did not complete within the configured timeout window.",
        [
            "A downstream dependency was degraded or overloaded.",
            "Network latency or packet loss on the request path.",
        ],
    ),
    IssueCategory.DATABASE_CONNECTION_ERROR: (
        "The application could not establish or maintain a connection to the database.",
        [
            "The database exhausted its connection pool or max-connections limit.",
            "A network partition or unplanned database process interruption occurred between app and database.",
        ],
    ),
    IssueCategory.HTTP_5XX_SPIKE: (
        "The service returned a burst of server-side errors to callers.",
        [
            "An unhandled exception in a recently deployed code path.",
            "A downstream dependency failure surfacing as a 5xx.",
        ],
    ),
    IssueCategory.UNKNOWN: (
        "The log excerpt shows an anomaly that doesn't clearly match a known incident category.",
        ["A new or rare failure mode not yet covered by detection rules."],
    ),
}

# A primary/alternative cause that reads like a fix suggestion is rejected
# outright, regardless of prompt compliance — this is the hard technical
# guarantee behind "RCA output never contains remediation/fix suggestions."
_FIX_SUGGESTION_RE = re.compile(
    r"\b(restart|rollback|patch|upgrade|downgrade|increase|decrease|reduce|scale|"
    r"recommend|should\s|must\s|fix|resolve|remediat|mitigat|workaround)\w*\b",
    re.IGNORECASE,
)


class RCAAgent:
    """Generates an explainable RCAReport for a single selected incident.

    Deterministic per-category templates are the offline-safe default,
    always available and always traceable to the incident's own log
    excerpt. An LLM, if configured, may produce a more specific report
    grounded in the incident's actual fields/excerpt — but its output is
    validated (evidence must literally appear in the excerpt, cause text
    must not read as a fix) before being trusted; otherwise this silently
    falls back to the heuristic report rather than erroring. Never
    recommends a fix — see project-spec.md "Root Cause Analysis".
    """

    def analyze(self, incident: LogIssue) -> RCAReport:
        if OPENROUTER_API_KEY:
            llm_report = self._analyze_with_llm(incident)
            if llm_report is not None:
                return llm_report
        return self._analyze_heuristically(incident)

    def _analyze_heuristically(self, incident: LogIssue) -> RCAReport:
        primary_cause, alt_templates = _CAUSE_TEMPLATES[incident.category]
        evidence = list(incident.raw_excerpt) or [incident.title]
        alternative_causes = [
            AlternativeCause(
                cause=cause,
                confidence=round(max(0.1, incident.confidence - 0.25 - 0.1 * index), 2),
                evidence=evidence,
            )
            for index, cause in enumerate(alt_templates)
        ]
        return RCAReport(
            incident_id=incident.id,
            primary_cause=primary_cause,
            evidence=evidence,
            alternative_causes=alternative_causes,
            confidence=incident.confidence,
            generated_at=datetime.now(timezone.utc),
            method="heuristic",
        )

    def _analyze_with_llm(self, incident: LogIssue) -> RCAReport | None:
        try:
            from openai import OpenAI
        except ImportError:
            return None

        user_payload = {
            "category": incident.category.value,
            "severity": incident.severity.value,
            "title": incident.title,
            "service": incident.service,
            "fields": incident.fields,
            "raw_excerpt": incident.raw_excerpt,
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

        primary_cause = str(payload.get("primary_cause") or "").strip()
        evidence = _grounded_evidence(payload.get("evidence"), incident.raw_excerpt)
        if not primary_cause or not evidence or _FIX_SUGGESTION_RE.search(primary_cause):
            return None  # ungrounded or reads like a fix — fall back to heuristic

        alternative_causes = []
        for alt in payload.get("alternative_causes") or []:
            cause = str(alt.get("cause", "")).strip()
            if not cause or _FIX_SUGGESTION_RE.search(cause):
                continue
            alt_evidence = _grounded_evidence(alt.get("evidence"), incident.raw_excerpt) or evidence
            try:
                confidence = max(0.0, min(1.0, float(alt.get("confidence", 0.3))))
            except (TypeError, ValueError):
                confidence = 0.3
            alternative_causes.append(AlternativeCause(cause=cause, confidence=confidence, evidence=alt_evidence))

        try:
            confidence = max(0.0, min(1.0, float(payload.get("confidence", incident.confidence))))
        except (TypeError, ValueError):
            confidence = incident.confidence

        return RCAReport(
            incident_id=incident.id,
            primary_cause=primary_cause,
            evidence=evidence,
            alternative_causes=alternative_causes,
            confidence=confidence,
            generated_at=datetime.now(timezone.utc),
            method="llm",
        )


def _grounded_evidence(raw_evidence: object, source_lines: list[str]) -> list[str]:
    """Keeps only evidence lines that literally appear in the incident's own
    raw log excerpt, so RCA evidence is always traceable to the source —
    never an LLM-invented quote.
    """
    if not isinstance(raw_evidence, list) or not source_lines:
        return []
    return [line for line in (str(item) for item in raw_evidence) if any(line in source for source in source_lines)]
