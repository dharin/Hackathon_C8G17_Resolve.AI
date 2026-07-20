from bs4 import BeautifulSoup, NavigableString, Tag

# Confluence storage-format macros that only add navigation/UI chrome, not
# content worth indexing (table of contents, page trees, related-content
# widgets, etc).
_NAVIGATIONAL_MACROS = {
    "toc",
    "children",
    "pagetree",
    "recently-updated",
    "contentbylabel",
    "related-labels",
    "navmap",
    "livesearch",
}

_ADMONITION_MACROS = {"info": "Info", "note": "Note", "warning": "Warning", "tip": "Tip"}


def parse_confluence_storage(storage_html: str) -> str:
    """Converts Confluence `storage`-format XHTML into sanitized Markdown.

    Confluence content is untrusted evidence, never executable instructions:
    scripts and inline event handlers are stripped outright, and only a
    known-safe set of structural elements is converted.

    Parsed as XML ("lxml-xml"), not HTML ("lxml") — storage format wraps
    macro bodies (e.g. a code macro's plain-text-body) in CDATA sections,
    which are an XML-only construct. BeautifulSoup's HTML parser has no
    concept of CDATA and silently drops that content, so a code macro would
    parse as an empty fenced block no matter what it actually contained.
    XML mode also strips the (here, undeclared) `ac:`/`ri:` namespace
    prefixes from tag and attribute names — every lookup below matches on
    the unprefixed name for that reason.

    The page body is a *fragment* — typically many sibling top-level
    elements (paragraph after paragraph, headings, tables) — but XML
    requires exactly one root element. Wrapped in a synthetic `<root>`
    before parsing so nothing after the first top-level element gets
    silently dropped by the parser.
    """
    soup = BeautifulSoup(f"<root>{storage_html}</root>", "lxml-xml")
    root = soup.find("root")

    for script in root.find_all(["script", "style"]):
        script.decompose()

    for macro in root.find_all("structured-macro"):
        name = macro.get("name", "")
        if name in _NAVIGATIONAL_MACROS:
            macro.decompose()
            continue
        if name == "code":
            _replace_code_macro(macro)
        elif name in _ADMONITION_MACROS:
            _replace_admonition_macro(macro, _ADMONITION_MACROS[name])

    markdown = _node_to_markdown(root)
    # Collapse runs of blank lines left behind by decomposed/converted nodes.
    lines = [line.rstrip() for line in markdown.splitlines()]
    collapsed: list[str] = []
    for line in lines:
        if line == "" and collapsed and collapsed[-1] == "":
            continue
        collapsed.append(line)
    return "\n".join(collapsed).strip()


def _replace_code_macro(macro: Tag) -> None:
    body = macro.find("plain-text-body")
    code_text = body.get_text() if body else ""
    macro.replace_with(NavigableString(f"\n```\n{code_text}\n```\n"))


def _replace_admonition_macro(macro: Tag, label: str) -> None:
    body = macro.find("rich-text-body")
    text = body.get_text(" ", strip=True) if body else ""
    macro.replace_with(NavigableString(f"\n> **{label}:** {text}\n"))


def _node_to_markdown(node) -> str:
    if isinstance(node, NavigableString):
        return str(node)

    parts: list[str] = []
    for child in node.children:
        parts.append(_element_to_markdown(child))
    return "".join(parts)


def _element_to_markdown(node) -> str:
    if isinstance(node, NavigableString):
        return str(node)
    if not isinstance(node, Tag):
        return ""

    name = node.name.lower() if node.name else ""

    if name in {"h1", "h2", "h3", "h4", "h5", "h6"}:
        level = int(name[1])
        return f"\n{'#' * level} {node.get_text(' ', strip=True)}\n"
    if name == "p":
        return f"\n{_node_to_markdown(node)}\n"
    if name in {"strong", "b"}:
        return f"**{node.get_text(' ', strip=True)}**"
    if name in {"em", "i"}:
        return f"*{node.get_text(' ', strip=True)}*"
    if name == "a":
        href = node.get("href", "")
        text = node.get_text(" ", strip=True)
        return f"[{text}]({href})" if href else text
    if name == "br":
        return "\n"
    if name == "li":
        return f"- {node.get_text(' ', strip=True)}\n"
    if name in {"ul", "ol"}:
        return "\n" + "".join(_element_to_markdown(li) for li in node.find_all("li", recursive=False)) + "\n"
    if name == "table":
        return _table_to_markdown(node)
    if name in {"code", "pre"}:
        return f"`{node.get_text()}`"
    if name in {"script", "style"}:
        return ""

    return _node_to_markdown(node)


def _table_to_markdown(table: Tag) -> str:
    rows = table.find_all("tr")
    if not rows:
        return ""

    grid = [[cell.get_text(" ", strip=True) for cell in row.find_all(["th", "td"])] for row in rows]
    grid = [row for row in grid if row]
    if not grid:
        return ""

    header, *body = grid
    lines = [
        "\n| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines) + "\n"
