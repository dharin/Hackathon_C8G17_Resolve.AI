import re

_BLANK_RUN = re.compile(r"\n{3,}")
_TRAILING_WS = re.compile(r"[ \t]+\n")


def normalize_content(content: str) -> str:
    """Light, source-agnostic cleanup applied after parsing and before
    chunking: normalize line endings, strip trailing whitespace, and
    collapse runs of blank lines so chunk boundaries aren't skewed by
    incidental formatting differences between sources.
    """
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_WS.sub("\n", text)
    text = _BLANK_RUN.sub("\n\n", text)
    return text.strip()
