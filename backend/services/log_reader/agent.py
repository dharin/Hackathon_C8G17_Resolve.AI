import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from models.issue_category import IssueCategory
from models.log_issue import LogIssue
from models.severity import Severity
from services.log_reader import patterns
from services.log_reader.llm_classifier import classify_with_llm
from services.log_reader.service_extractor import extract_service
from services.log_reader.timestamp_parser import parse_timestamp

MAX_EXCERPT_LINES = 5
GROUP_LINE_WINDOW = 5  # merge same category+service matches within this many lines
_SEVERITY_ORDER = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


@dataclass
class _RawMatch:
    line_no: int
    line: str
    category: IssueCategory
    severity: Severity
    title: str
    fields: dict[str, Any]
    confidence: float
    service: str | None
    timestamp: datetime | None
    detection_method: str = "rule"


class LogReaderAgent:
    """Parses an uploaded log's text and detects every incident in it.

    Deterministic regex rules (services.log_reader.patterns) run first. Only
    lines that carry an evident problem signal (ERROR/FATAL/WARN/exception-
    like) but match no known rule are handed to the LLM classifier, and only
    if one is configured — see llm_classifier.classify_with_llm.

    This agent only reads and classifies. It never creates Jira tickets,
    never sends Slack notifications, and returns every detected incident
    regardless of severity — filtering/notification is out of scope here.
    """

    def analyze(self, text: str) -> list[LogIssue]:
        raw_matches = self._scan(text)
        groups = self._group(raw_matches)
        return [self._to_log_issue(group) for group in groups]

    def _scan(self, text: str) -> list[_RawMatch]:
        raw_matches: list[_RawMatch] = []

        for line_no, line in enumerate(text.splitlines()):
            if not line.strip():
                continue

            match = patterns.detect(line)
            if match is not None:
                raw_matches.append(
                    _RawMatch(
                        line_no=line_no,
                        line=line,
                        category=match.category,
                        severity=match.severity,
                        title=match.title,
                        fields=match.fields,
                        confidence=match.confidence,
                        service=extract_service(line),
                        timestamp=parse_timestamp(line),
                    )
                )
                continue

            if not patterns.has_problem_signal(line):
                continue

            llm_result = classify_with_llm(line)
            if llm_result is not None:
                raw_matches.append(
                    _RawMatch(
                        line_no=line_no,
                        line=line,
                        category=llm_result.category,
                        severity=llm_result.severity,
                        title=llm_result.title,
                        fields=llm_result.fields,
                        confidence=llm_result.confidence,
                        service=extract_service(line),
                        timestamp=parse_timestamp(line),
                        detection_method="llm",
                    )
                )
            else:
                # No deterministic rule matched and no LLM was able to (or
                # was configured to) classify it — this is a genuine unknown,
                # never forced into a known category.
                raw_matches.append(
                    _RawMatch(
                        line_no=line_no,
                        line=line,
                        category=IssueCategory.UNKNOWN,
                        severity=Severity.LOW,
                        title="Unclassified anomaly",
                        fields={},
                        confidence=0.35,
                        service=extract_service(line),
                        timestamp=parse_timestamp(line),
                        detection_method="unclassified",
                    )
                )

        return raw_matches

    def _group(self, matches: list[_RawMatch]) -> list[list[_RawMatch]]:
        """Merges nearby same-category/same-service matches into one incident
        so a burst of related lines (e.g. 5 connection-refused lines in a
        row) becomes one incident with multiple occurrences, not five.
        """
        groups: list[list[_RawMatch]] = []
        for current in matches:
            for group in groups:
                last = group[-1]
                if (
                    last.category == current.category
                    and last.service == current.service
                    and (current.line_no - last.line_no) <= GROUP_LINE_WINDOW
                ):
                    group.append(current)
                    break
            else:
                groups.append([current])
        return groups

    def _to_log_issue(self, group: list[_RawMatch]) -> LogIssue:
        primary = group[0]
        occurrences = len(group)
        severity = self._escalate(primary.severity, occurrences)
        confidence = round(min(0.98, primary.confidence + 0.02 * (occurrences - 1)), 2)

        # Merge fields across the whole group, not just the first match — a
        # value extracted from a later line (e.g. a disk-usage percentage
        # that only appears once the second related line is parsed) must
        # still surface on the incident.
        fields: dict[str, Any] = {}
        for match in group:
            fields.update(match.fields)

        if primary.category == IssueCategory.HTTP_5XX_SPIKE:
            codes = sorted({m.fields.get("status_code") for m in group if m.fields.get("status_code")})
            if codes:
                fields["status_codes"] = codes
                fields.pop("status_code", None)
        fields["occurrences"] = occurrences

        return LogIssue(
            id=uuid.uuid4().hex,
            category=primary.category,
            severity=severity,
            title=primary.title,
            service=primary.service,
            timestamp=primary.timestamp,
            confidence=confidence,
            fields=fields,
            raw_excerpt=[m.line for m in group[:MAX_EXCERPT_LINES]],
            detection_method=primary.detection_method,
        )

    @staticmethod
    def _escalate(severity: Severity, occurrences: int) -> Severity:
        """Repeated occurrences of the same issue bump severity up one tier
        (capped at critical) — a single auth failure is routine, five in a
        row within a few lines is a plausible brute-force attempt.
        """
        if occurrences >= 5:
            steps = 2
        elif occurrences >= 3:
            steps = 1
        else:
            return severity

        index = min(_SEVERITY_ORDER.index(severity) + steps, len(_SEVERITY_ORDER) - 1)
        return _SEVERITY_ORDER[index]
