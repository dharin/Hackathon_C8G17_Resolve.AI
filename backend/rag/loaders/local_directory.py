import hashlib
import logging
from datetime import datetime, timezone
from pathlib import Path

from rag.models import KnowledgeDocument
from rag.normalizer import normalize_content
from rag.parsers.docx import parse_docx
from rag.parsers.markdown import parse_markdown
from rag.parsers.pdf import parse_pdf
from rag.parsers.text import parse_text

logger = logging.getLogger(__name__)

_PARSERS = {
    ".md": parse_markdown,
    ".txt": parse_text,
    ".pdf": parse_pdf,
    ".docx": parse_docx,
}

_EXCLUDED_DIR_NAMES = {".git", "__pycache__", ".DS_Store", "node_modules"}


class LocalSopLoader:
    """Loads SOP documents from a backend-readable local directory. A
    parser failure for one file is caught and logged here so it never
    aborts the rest of the sync (see project-spec.md "Local SOP
    Integration").
    """

    source_type = "local_sop"

    def __init__(
        self,
        directory: Path,
        allowed_extensions: set[str],
        recursive: bool = True,
    ) -> None:
        self.directory = directory
        self.allowed_extensions = {ext.lower() for ext in allowed_extensions}
        self.recursive = recursive

    def discover(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        for path in self._iter_files():
            try:
                document = self._load_file(path)
            except Exception as exc:  # noqa: BLE001 - isolate per-file failure
                logger.warning("Failed to parse local SOP file %s: %s", path, exc)
                continue
            if document is not None:
                documents.append(document)
        return documents

    def _iter_files(self):
        if not self.directory.exists():
            return
        pattern = "**/*" if self.recursive else "*"
        for path in sorted(self.directory.glob(pattern)):
            if not path.is_file():
                continue
            if path.name.startswith(".") or path.name.endswith(("~", ".tmp", ".swp")):
                continue
            if any(part in _EXCLUDED_DIR_NAMES for part in path.relative_to(self.directory).parts[:-1]):
                continue
            if path.suffix.lower() not in self.allowed_extensions or path.suffix.lower() not in _PARSERS:
                continue
            yield path

    def _load_file(self, path: Path) -> KnowledgeDocument | None:
        parser = _PARSERS[path.suffix.lower()]
        raw = path.read_bytes()
        content = normalize_content(parser(raw))
        if not content.strip():
            return None

        relative_path = path.relative_to(self.directory).as_posix()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        stat = path.stat()

        return KnowledgeDocument(
            document_id=f"local-sop:{relative_path}",
            source_type="local_sop",
            title=path.stem,
            content=content,
            source_uri=relative_path,
            version=content_hash[:12],
            content_hash=content_hash,
            updated_at=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
            metadata={
                "relative_path": relative_path,
                "filename": path.name,
                "extension": path.suffix.lower(),
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            },
        )
