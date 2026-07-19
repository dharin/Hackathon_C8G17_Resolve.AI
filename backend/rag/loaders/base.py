from typing import Protocol

from rag.models import KnowledgeDocument


class KnowledgeLoader(Protocol):
    """Common contract for every RAG source loader. A loader only discovers
    and loads raw documents into the canonical KnowledgeDocument shape — it
    never normalizes or chunks (that's normalizer.py/chunker.py), so sources
    stay swappable and testable in isolation.
    """

    source_type: str

    def discover(self) -> list[KnowledgeDocument]:
        """Return every currently-accessible document from this source.

        Implementations must isolate errors per document/page: one bad file
        or page must not raise out of discover() and abort the whole sync.
        """
        ...
