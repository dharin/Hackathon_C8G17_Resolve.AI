import io

from pypdf import PdfReader


def parse_pdf(raw: bytes) -> str:
    """Extracts text page by page, keeping a `## Page N` heading per page so
    the chunker can preserve page boundaries as section context and callers
    can cite a page number.
    """
    reader = PdfReader(io.BytesIO(raw))
    parts: list[str] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            continue
        parts.append(f"## Page {page_number}\n\n{text}")
    return "\n\n".join(parts)
