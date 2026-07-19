def parse_markdown(raw: bytes) -> str:
    # Markdown is already the chunker's native structure language, so no
    # conversion is needed beyond decoding.
    return raw.decode("utf-8", errors="replace")
