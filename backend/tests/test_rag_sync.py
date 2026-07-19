import hashlib
from datetime import datetime, timezone
from pathlib import Path

from rag.models import KnowledgeDocument
from rag.store import ChunkStore
from rag.sync import SyncCoordinator
from rag.sync_state import SyncStateStore

DIM = 8


class FakeEmbedder:
    """Deterministic, hash-based embeddings so tests never touch a real
    model — only Confluence/Atlassian calls need mocking per the phase-6
    spec, but keeping tests offline everywhere is strictly better.
    """

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [b / 255.0 for b in digest[:DIM]]


class FakeLoader:
    source_type = "local_sop"

    def __init__(self, documents: list[KnowledgeDocument]) -> None:
        self._documents = documents

    def discover(self) -> list[KnowledgeDocument]:
        return self._documents


def make_document(document_id: str, content: str, version: str = "v1") -> KnowledgeDocument:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    return KnowledgeDocument(
        document_id=document_id,
        source_type="local_sop",
        title=document_id,
        content=content,
        source_uri=f"{document_id}.md",
        version=version,
        content_hash=content_hash,
        updated_at=datetime.now(timezone.utc),
        metadata={},
    )


def make_coordinator(tmp_path: Path) -> tuple[SyncCoordinator, ChunkStore, SyncStateStore]:
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    sync_state = SyncStateStore(tmp_path / "sync.sqlite3")
    coordinator = SyncCoordinator(store=store, sync_state=sync_state, embedder=FakeEmbedder())
    return coordinator, store, sync_state


def test_initial_indexing_indexes_all_documents(tmp_path: Path):
    coordinator, store, _ = make_coordinator(tmp_path)
    docs = [make_document("a", "# A\n\nContent A."), make_document("b", "# B\n\nContent B.")]

    summary = coordinator.sync_source(FakeLoader(docs))

    assert summary.documents_discovered == 2
    assert summary.documents_indexed == 2
    assert summary.documents_skipped_unchanged == 0


def test_rerunning_sync_skips_unchanged_documents(tmp_path: Path):
    coordinator, _, _ = make_coordinator(tmp_path)
    docs = [make_document("a", "# A\n\nContent A.")]

    coordinator.sync_source(FakeLoader(docs))
    summary = coordinator.sync_source(FakeLoader(docs))

    assert summary.documents_indexed == 0
    assert summary.documents_skipped_unchanged == 1


def test_changing_one_document_reindexes_only_that_document(tmp_path: Path):
    coordinator, _, _ = make_coordinator(tmp_path)
    doc_a = make_document("a", "# A\n\nContent A.")
    doc_b = make_document("b", "# B\n\nContent B.")
    coordinator.sync_source(FakeLoader([doc_a, doc_b]))

    changed_a = make_document("a", "# A\n\nChanged content A.", version="v2")
    summary = coordinator.sync_source(FakeLoader([changed_a, doc_b]))

    assert summary.documents_indexed == 1
    assert summary.documents_skipped_unchanged == 1


def test_removed_document_is_marked_unavailable_and_deleted_from_store(tmp_path: Path):
    coordinator, store, sync_state = make_coordinator(tmp_path)
    doc = make_document("a", "# A\n\nContent A.")
    coordinator.sync_source(FakeLoader([doc]))

    summary = coordinator.sync_source(FakeLoader([]))  # doc no longer discovered

    assert summary.documents_marked_unavailable == 1
    assert sync_state.get("a").status == "unavailable"

    query_vector = FakeEmbedder().embed_query("Content A.")
    assert store.search(query_vector, limit=10) == []


def test_failed_document_is_reported_without_aborting_sync(tmp_path: Path):
    coordinator, _, sync_state = make_coordinator(tmp_path)
    good = make_document("good", "# Good\n\nFine.")
    bad = make_document("bad", "# Bad\n\nWill fail.")

    class ExplodingEmbedder(FakeEmbedder):
        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            if any("Will fail" in t for t in texts):
                raise RuntimeError("embedding backend unavailable")
            return super().embed_documents(texts)

    coordinator._embedder = ExplodingEmbedder()
    summary = coordinator.sync_source(FakeLoader([good, bad]))

    assert summary.documents_indexed == 1
    assert summary.documents_failed == 1
    assert sync_state.get("good").status == "indexed"
    assert sync_state.get("bad").status == "failed"
    assert sync_state.get("bad").last_error is not None
