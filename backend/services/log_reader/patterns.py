import re
from dataclasses import dataclass, field
from typing import Any, Callable

from models.issue_category import IssueCategory
from models.severity import Severity

_PROBLEM_SIGNAL_RE = re.compile(
    r"\b(ERROR|FATAL|CRITICAL|EXCEPTION|TRACEBACK|FAILED?|WARN(?:ING)?)\b", re.IGNORECASE
)


@dataclass
class CategoryMatch:
    category: IssueCategory
    severity: Severity
    title: str
    confidence: float
    fields: dict[str, Any] = field(default_factory=dict)


# --- OOM kill -----------------------------------------------------------

_OOM_RE = re.compile(
    r"\b(oom[-_ ]?kill(?:er)?|out of memory|oomkilled)\b", re.IGNORECASE
)
_OOM_PROC_RE = re.compile(r"killed process (\d+)\s*\(([^)]+)\)", re.IGNORECASE)


def _detect_oom(line: str) -> CategoryMatch | None:
    if not _OOM_RE.search(line):
        return None
    fields: dict[str, Any] = {}
    match = _OOM_PROC_RE.search(line)
    if match:
        fields["pid"] = match.group(1)
        fields["process"] = match.group(2)
    return CategoryMatch(
        category=IssueCategory.OOM_KILL,
        severity=Severity.CRITICAL,
        title="Out-of-memory kill detected",
        confidence=0.92,
        fields=fields,
    )


# --- Disk-space exhaustion ------------------------------------------------

_DISK_RE = re.compile(
    r"\b(no space left on device|enospc|disk\s+(?:full|usage))\b", re.IGNORECASE
)
_DISK_PCT_RE = re.compile(r"(\d{1,3})\s*%\s*(?:full|used|usage|of\s+maxmemory)", re.IGNORECASE)


def _detect_disk(line: str) -> CategoryMatch | None:
    if not _DISK_RE.search(line):
        return None
    fields: dict[str, Any] = {}
    pct_match = _DISK_PCT_RE.search(line)
    severity = Severity.CRITICAL
    if pct_match:
        pct = int(pct_match.group(1))
        fields["used_percent"] = pct
        if pct >= 90:
            severity = Severity.CRITICAL
        elif pct >= 75:
            severity = Severity.HIGH
        else:
            severity = Severity.MEDIUM
    return CategoryMatch(
        category=IssueCategory.DISK_SPACE_EXHAUSTION,
        severity=severity,
        title="Disk space exhaustion detected",
        confidence=0.9,
        fields=fields,
    )


# --- Database connection error -------------------------------------------

_DB_KEYWORDS_RE = re.compile(r"\b(postgres|postgresql|mysql|database|pg_stat_activity)\b", re.IGNORECASE)
_DB_CONN_RE = re.compile(
    r"\b(connection pool|connection (?:refused|reset|timeout|exhausted)|"
    r"could not connect|connection to .* failed|pool exhausted)\b",
    re.IGNORECASE,
)


def _detect_database(line: str) -> CategoryMatch | None:
    if not (_DB_KEYWORDS_RE.search(line) and _DB_CONN_RE.search(line)):
        return None
    return CategoryMatch(
        category=IssueCategory.DATABASE_CONNECTION_ERROR,
        severity=Severity.CRITICAL,
        title="Database connection error detected",
        confidence=0.88,
    )


# --- Authentication failure ------------------------------------------------

_AUTH_RE = re.compile(
    r"\b(authentication failed|auth failed|invalid credentials|login failed|"
    r"failed password|unauthorized|permission denied|refresh token not found)\b",
    re.IGNORECASE,
)
_AUTH_USER_KV_RE = re.compile(r"user(?:name)?[=:]\s*([\w.@-]+)", re.IGNORECASE)
_AUTH_USER_FOR_RE = re.compile(r"\bfor\s+([\w.@-]+)", re.IGNORECASE)


def _detect_auth(line: str) -> CategoryMatch | None:
    if not _AUTH_RE.search(line):
        return None
    fields: dict[str, Any] = {}
    # Try the unambiguous "user=" / "username:" form first — a bare "for" is
    # too generic and can precede unrelated words ("failed for the request").
    match = _AUTH_USER_KV_RE.search(line) or _AUTH_USER_FOR_RE.search(line)
    if match:
        fields["user"] = match.group(1)
    return CategoryMatch(
        category=IssueCategory.AUTH_FAILURE,
        severity=Severity.MEDIUM,
        title="Authentication failure detected",
        confidence=0.85,
        fields=fields,
    )


# --- HTTP 5xx spike ---------------------------------------------------------

_HTTP_5XX_RE = re.compile(
    r'"\s*(5\d{2})\b|status(?:_code)?[=:]\s*(5\d{2})\b|\b(5\d{2})\s+'
    r"(?:service unavailable|internal server error|bad gateway|gateway timeout)",
    re.IGNORECASE,
)


def _detect_http_5xx(line: str) -> CategoryMatch | None:
    match = _HTTP_5XX_RE.search(line)
    if not match:
        return None
    code = next(g for g in match.groups() if g)
    return CategoryMatch(
        category=IssueCategory.HTTP_5XX_SPIKE,
        severity=Severity.HIGH,
        title="HTTP 5xx errors detected",
        confidence=0.87,
        fields={"status_code": code},
    )


# --- Timeout (generic fallback; checked after DB, since a DB-specific ------
# --- timeout should be categorized as a database connection error) --------

_TIMEOUT_RE = re.compile(r"\b(timed out|timeout|deadline exceeded)\b", re.IGNORECASE)
_DURATION_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(ms|s|sec|seconds)\b", re.IGNORECASE)


def _detect_timeout(line: str) -> CategoryMatch | None:
    if not _TIMEOUT_RE.search(line):
        return None
    fields: dict[str, Any] = {}
    match = _DURATION_RE.search(line)
    if match:
        value = float(match.group(1))
        unit = match.group(2).lower()
        fields["duration_ms"] = value if unit == "ms" else value * 1000
    return CategoryMatch(
        category=IssueCategory.TIMEOUT,
        severity=Severity.MEDIUM,
        title="Timeout detected",
        confidence=0.8,
        fields=fields,
    )


# Order matters: more specific categories are checked before generic ones
# (e.g. a database-flavored timeout must resolve to DATABASE_CONNECTION_ERROR,
# not the generic TIMEOUT bucket).
_DETECTORS: list[Callable[[str], CategoryMatch | None]] = [
    _detect_oom,
    _detect_disk,
    _detect_database,
    _detect_auth,
    _detect_http_5xx,
    _detect_timeout,
]


def detect(line: str) -> CategoryMatch | None:
    for detector in _DETECTORS:
        match = detector(line)
        if match is not None:
            return match
    return None


def has_problem_signal(line: str) -> bool:
    """True if a line looks like it carries an anomaly, even though no
    deterministic category matched — the signal that makes it eligible for
    LLM classification instead of being silently dropped.
    """
    return bool(_PROBLEM_SIGNAL_RE.search(line))
