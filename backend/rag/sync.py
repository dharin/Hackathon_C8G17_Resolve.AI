import logging
from datetime import datetime, timezone
from typing import Any

from rag.chunker import chunk_document
from rag.embedder import Embedder
from rag.loaders.base import KnowledgeLoader
from rag.models import DocumentSyncState, SourceSyncSummary
from rag.store import ChunkStore
from rag.sync_state import SyncStateStore

logger = logging.getLogger(__name__)


class SyncCoordinator:
    """Ties a source loader to chunking, embedding, storage, and persisted
    sync state. One coordinator instance is reused across sources; only the
    loader passed to `sync_source` changes.
    """

    def __init__(
        self,
        store: ChunkStore,
        sync_state: SyncStateStore,
        embedder: Embedder,
        chunk_config: dict[str, Any] | None = None,
    ) -> None:
        self._store = store
        self._sync_state = sync_state
        self._embedder = embedder
        self._chunk_config = chunk_config or {}

    def sync_source(self, loader: KnowledgeLoader) -> SourceSyncSummary:
        source_type = loader.source_type
        summary = SourceSyncSummary(source_type=source_type)
        now = datetime.now(timezone.utc)

        documents = loader.discover()
        summary.documents_discovered = len(documents)
        discovered_ids: set[str] = set()

        for document in documents:
            discovered_ids.add(document.document_id)
            try:
                existing = self._sync_state.get(document.document_id)
                unchanged = (
                    existing is not None
                    and existing.status == "indexed"
                    and existing.content_hash == document.content_hash
                    and existing.version == document.version
                )
                if unchanged:
                    summary.documents_skipped_unchanged += 1
                    continue

                chunks = chunk_document(document, **self._chunk_config)
                vectors = self._embedder.embed_documents([chunk.content for chunk in chunks])
                self._store.replace_document_chunks(document.document_id, chunks, vectors)

                self._sync_state.upsert(
                    DocumentSyncState(
                        document_id=document.document_id,
                        source_type=source_type,
                        version=document.version,
                        source_uri=document.source_uri,
                        content_hash=document.content_hash,
                        last_discovered_at=now,
                        last_indexed_at=now,
                        status="indexed",
                        last_error=None,
                    )
                )
                summary.documents_indexed += 1
            except Exception as exc:  # noqa: BLE001 - isolate per-document failure
                logger.warning("Failed to sync document %s: %s", document.document_id, exc)
                summary.documents_failed += 1
                summary.errors.append(f"{document.document_id}: {exc}")
                self._sync_state.upsert(
                    DocumentSyncState(
                        document_id=document.document_id,
                        source_type=source_type,
                        version=document.version,
                        source_uri=document.source_uri,
                        content_hash=document.content_hash,
                        last_discovered_at=now,
                        last_indexed_at=None,
                        status="failed",
                        last_error=str(exc),
                    )
                )

        for previous in self._sync_state.all_for_source(source_type):
            if previous.document_id in discovered_ids or previous.status != "indexed":
                continue
            self._store.delete_document(previous.document_id)
            self._sync_state.mark_unavailable(previous.document_id)
            summary.documents_marked_unavailable += 1

        return summary
