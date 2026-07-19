import io

from docx import Document as DocxDocument
from docx.table import Table
from docx.text.paragraph import Paragraph


def parse_docx(raw: bytes) -> str:
    """Extracts paragraphs (as Markdown headings/bullets by style) and
    tables (as Markdown tables), in document order, so headings still work
    as chunk boundaries downstream.
    """
    document = DocxDocument(io.BytesIO(raw))
    parts: list[str] = []

    for block in _iter_block_items(document):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue
            style = (block.style.name or "").lower() if block.style else ""
            if style.startswith("heading"):
                level = "".join(ch for ch in style if ch.isdigit()) or "1"
                parts.append(f"{'#' * min(int(level), 6)} {text}")
            elif style == "list bullet" or style == "list paragraph":
                parts.append(f"- {text}")
            else:
                parts.append(text)
        elif isinstance(block, Table):
            parts.append(_table_to_markdown(block))

    return "\n\n".join(parts)


def _iter_block_items(document: DocxDocument):
    """Yields paragraphs and tables in the order they appear in the body —
    python-docx doesn't expose this directly.
    """
    parent_elm = document.element.body
    for child in parent_elm.iterchildren():
        if child.tag.endswith("}p"):
            yield Paragraph(child, document)
        elif child.tag.endswith("}tbl"):
            yield Table(child, document)


def _table_to_markdown(table: Table) -> str:
    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
    if not rows:
        return ""
    header, *body = rows
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in body)
    return "\n".join(lines)
