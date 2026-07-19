import json
from dataclasses import dataclass
from typing import Any

from config.settings import OPENROUTER_API_KEY, OPENROUTER_MODEL
from models.issue_category import IssueCategory
from models.severity import Severity

# OpenRouter exposes an OpenAI-compatible Chat Completions API, so the
# official `openai` SDK is reused here — just pointed at OpenRouter's base
# URL with an OpenRouter key instead of an OpenAI one.
_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_ALLOWED_CATEGORIES = [c.value for c in IssueCategory]

_SYSTEM_PROMPT = (
    "You classify a single DevOps log line into one of these categories: "
    f"{', '.join(_ALLOWED_CATEGORIES)}. Only pick a category other than "
    "'unknown' if you are confident it genuinely applies — never force a "
    "fit for an anomaly that doesn't clearly match. Respond with strict "
    'JSON: {"category": str, "severity": "critical"|"high"|"medium"|"low", '
    '"title": str, "confidence": number between 0 and 1}.'
)


@dataclass
class LLMClassification:
    category: IssueCategory
    severity: Severity
    title: str
    confidence: float
    fields: dict[str, Any]


def classify_with_llm(line: str) -> LLMClassification | None:
    """Best-effort LLM classification for a line that carries a problem
    signal but matched no deterministic rule.

    Returns None — never raises — if no API key is configured, the SDK
    isn't installed, or the call fails for any reason. Callers must treat
    None as "fall back to an unknown-category incident", never as an error.
    """
    if not OPENROUTER_API_KEY:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    try:
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=_OPENROUTER_BASE_URL)
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": line},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            timeout=10,
        )
        payload = json.loads(response.choices[0].message.content)
        category = IssueCategory(payload.get("category", "unknown"))
        severity = Severity(payload.get("severity", "low"))
        confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.5))))
        title = str(payload.get("title") or "Unclassified anomaly")
    except Exception:
        return None

    return LLMClassification(
        category=category,
        severity=severity,
        title=title,
        confidence=confidence,
        fields={},
    )
