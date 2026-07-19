from pathlib import Path

from rag.retriever import Retriever
from rag.store import ChunkStore
from tests.test_rag_sync import DIM, FakeEmbedder, FakeLoader, make_coordinator, make_document


def test_retrieve_returns_source_attributed_results(tmp_path: Path):
    coordinator, store, _ = make_coordinator(tmp_path)
    doc = make_document("a", "# Disk Cleanup\n\nFree up space by removing old logs.")
    coordinator.sync_source(FakeLoader([doc]))

    retriever = Retriever(store=store, embedder=FakeEmbedder())
    results = retriever.retrieve("Free up space by removing old logs.", limit=5)

    assert len(results) == 1
    assert results[0].source_type == "local_sop"
    assert results[0].source_uri == "a.md"


def test_retrieve_returns_empty_list_when_nothing_indexed(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    retriever = Retriever(store=store, embedder=FakeEmbedder())
    assert retriever.retrieve("anything") == []
