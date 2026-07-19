import re
from datetime import datetime, timezone

_ISO_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)
_SYSLOG_RE = re.compile(r"\b[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\b")


def parse_timestamp(line: str) -> datetime | None:
    """Extracts and parses the first recognizable timestamp in a log line.

    Supports ISO 8601 (with optional Z/offset/fractional seconds) and
    syslog-style "Mon DD HH:MM:SS" (year assumed to be the current year,
    since syslog format doesn't carry one). Returns None rather than raising
    when nothing recognizable is found — timestamps are best-effort.
    """
    match = _ISO_RE.search(line)
    if match:
        raw = match.group(0).replace("Z", "+00:00")
        if "T" not in raw:
            raw = raw.replace(" ", "T", 1)
        try:
            return datetime.fromisoformat(raw)
        except ValueError:
            pass

    match = _SYSLOG_RE.search(line)
    if match:
        year = datetime.now(timezone.utc).year
        try:
            parsed = datetime.strptime(f"{year} {match.group(0)}", "%Y %b %d %H:%M:%S")
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return None
