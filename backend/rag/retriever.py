from rag.embedder import Embedder
from rag.models import RetrievedChunk
from rag.store import ChunkStore


class Retriever:
    """Backend retrieval service used by the Remediation/Cookbook agents.
    Returns only what was actually indexed — no supporting documentation
    means an empty list, never a fabricated recommendation.
    """

    def __init__(self, store: ChunkStore, embedder: Embedder) -> None:
        self._store = store
        self._embedder = embedder

    def retrieve(
        self,
        query: str,
        limit: int = 10,
        source_type: str | None = None,
        confluence_space_key: str | None = None,
        local_sop_path: str | None = None,
    ) -> list[RetrievedChunk]:
        query_vector = self._embedder.embed_query(query)
        return self._store.search(
            query_vector,
            limit=limit,
            source_type=source_type,
            confluence_space_key=confluence_space_key,
            local_sop_path=local_sop_path,
        )
