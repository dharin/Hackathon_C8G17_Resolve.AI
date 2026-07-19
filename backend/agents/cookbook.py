import re

from models.cookbook import Cookbook
from models.log_issue import LogIssue
from models.rca_report import RCAReport
from models.recommendation import Recommendation

_CODE_BLOCK_RE = re.compile(r"```(?:\w+)?\n?(.*?)```", re.DOTALL)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")

_VALIDATION_KEYWORDS = ("verify", "confirm", "check", "ensure", "validate")
_ROLLBACK_KEYWORDS = ("rollback", "roll back", "revert", "undo", "restore", "fail over", "failover")


class CookbookAgent:
    """Transforms the RCA and remediation recommendations into a structured
    runbook. Deliberately extractive rather than generative: every command,
    validation step, and rollback step is pulled verbatim from a
    recommendation's own retrieved source content, never written from
    scratch — this is what guarantees "every command traces back to a
    remediation recommendation" (see project-spec.md "Cookbook") with zero
    risk of an invented step, at the cost of sometimes finding nothing to
    extract (in which case that section is left empty, not fabricated).
    """

    def build(
        self,
        incident: LogIssue,
        rca: RCAReport | None,
        recommendations: list[Recommendation],
    ) -> Cookbook:
        root_cause = rca.primary_cause if rca else incident.title
        # Deduped: multiple recommendations can share an identical heuristic
        # title when several chunks from the same source document each
        # became their own recommendation (see agents/remediation.py).
        steps = _dedupe([rec.title for rec in recommendations])

        commands: list[str] = []
        validation: list[str] = []
        rollback: list[str] = []
        for rec in recommendations:
            for source in rec.sources:
                commands.extend(_extract_commands(source.content))
                validation.extend(_extract_sentences(source.content, _VALIDATION_KEYWORDS))
                rollback.extend(_extract_sentences(source.content, _ROLLBACK_KEYWORDS))

        return Cookbook(
            root_cause=root_cause,
            steps=steps,
            commands=_dedupe(commands),
            validation=_dedupe(validation),
            rollback=_dedupe(rollback),
        )


def _extract_commands(content: str) -> list[str]:
    commands = []
    for block in _CODE_BLOCK_RE.findall(content):
        for line in block.splitlines():
            stripped = line.strip()
            if stripped:
                commands.append(stripped)
    return commands


def _extract_sentences(content: str, keywords: tuple[str, ...]) -> list[str]:
    # Strip fenced code blocks first so a command line isn't double-counted
    # as a validation/rollback sentence.
    prose = _CODE_BLOCK_RE.sub(" ", content)
    sentences = _SENTENCE_SPLIT_RE.split(prose)
    lowered_keywords = keywords
    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip() and any(keyword in sentence.lower() for keyword in lowered_keywords)
    ]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
