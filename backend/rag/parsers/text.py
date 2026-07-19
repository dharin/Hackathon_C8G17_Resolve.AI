def parse_text(raw: bytes) -> str:
    return raw.decode("utf-8", errors="replace")
