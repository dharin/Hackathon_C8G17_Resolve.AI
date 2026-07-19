import re

_LEVEL_WORDS = {"INFO", "WARN", "WARNING", "ERROR", "FATAL", "DEBUG", "CRITICAL", "TRACE"}

_KV_RE = re.compile(r"\b(?:service|svc|app|component)[=:]\s*([\w.-]+)", re.IGNORECASE)
_BRACKET_RE = re.compile(r"\[([\w.-]+)\]")
_PREFIX_RE = re.compile(r"^([a-zA-Z][\w-]{2,40}):\s")


def extract_service(line: str) -> str | None:
    """Best-effort extraction of a service/component name from a log line.

    Recognizes `service=`/`svc=`/`app=`/`component=` key-value pairs, a
    `[service-name]` bracket anywhere in the line, or a leading
    `service-name:` prefix. Returns None if nothing looks like a service
    identifier — this is a heuristic, not a guarantee.
    """
    match = _KV_RE.search(line)
    if match:
        return match.group(1)

    match = _BRACKET_RE.search(line)
    if match:
        return match.group(1)

    match = _PREFIX_RE.match(line.strip())
    if match:
        candidate = match.group(1)
        if candidate.upper() not in _LEVEL_WORDS:
            return candidate

    return None
