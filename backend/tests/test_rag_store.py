from datetime import datetime, timezone
from pathlib import Path

from rag.models import DocumentChunk
from rag.store import ChunkStore

DIM = 4


def make_chunk(chunk_id: str, document_id: str, content: str, **overrides) -> DocumentChunk:
    defaults = dict(
        chunk_id=chunk_id,
        document_id=document_id,
        source_type="local_sop",
        title="Doc",
        source_uri=f"{document_id}.md",
        section_path=["Intro"],
        chunk_index=0,
        version="v1",
        content_hash="hash",
        content=content,
        token_count=len(content.split()),
        updated_at=datetime.now(timezone.utc),
        indexed_at=datetime.now(timezone.utc),
        metadata={},
    )
    defaults.update(overrides)
    return DocumentChunk(**defaults)


def unit_vector(*weights: float) -> list[float]:
    vec = list(weights) + [0.0] * (DIM - len(weights))
    norm = sum(v * v for v in vec) ** 0.5
    return [v / norm for v in vec] if norm else vec


def test_replace_and_search_returns_closest_match(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    chunk_a = make_chunk("a:1", "a", "disk cleanup steps")
    chunk_b = make_chunk("b:1", "b", "database failover steps")

    store.replace_document_chunks("a", [chunk_a], [unit_vector(1, 0, 0, 0)])
    store.replace_document_chunks("b", [chunk_b], [unit_vector(0, 1, 0, 0)])

    results = store.search(unit_vector(1, 0, 0, 0), limit=5)
    assert results[0].chunk_id == "a:1"
    assert results[0].source_type == "local_sop"


def test_replace_document_chunks_removes_previous_chunks(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    old_chunk = make_chunk("a:1", "a", "old content", chunk_index=0)
    store.replace_document_chunks("a", [old_chunk], [unit_vector(1, 0, 0, 0)])

    new_chunk = make_chunk("a:2", "a", "new content", chunk_index=0)
    store.replace_document_chunks("a", [new_chunk], [unit_vector(1, 0, 0, 0)])

    results = store.search(unit_vector(1, 0, 0, 0), limit=10)
    chunk_ids = {r.chunk_id for r in results}
    assert "a:1" not in chunk_ids
    assert "a:2" in chunk_ids


def test_delete_document_removes_all_its_chunks(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    chunk = make_chunk("a:1", "a", "content")
    store.replace_document_chunks("a", [chunk], [unit_vector(1, 0, 0, 0)])

    store.delete_document("a")

    assert store.search(unit_vector(1, 0, 0, 0), limit=10) == []


def test_search_filters_by_source_type(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    local_chunk = make_chunk("a:1", "a", "content", source_type="local_sop")
    confluence_chunk = make_chunk("b:1", "b", "content", source_type="confluence")

    store.replace_document_chunks("a", [local_chunk], [unit_vector(1, 0, 0, 0)])
    store.replace_document_chunks("b", [confluence_chunk], [unit_vector(1, 0, 0, 0)])

    results = store.search(unit_vector(1, 0, 0, 0), limit=10, source_type="confluence")
    assert [r.chunk_id for r in results] == ["b:1"]


def test_search_returns_source_attribution(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    chunk = make_chunk("a:1", "a", "content", source_uri="runbooks/a.md", section_path=["Setup", "Steps"])
    store.replace_document_chunks("a", [chunk], [unit_vector(1, 0, 0, 0)])

    result = store.search(unit_vector(1, 0, 0, 0), limit=1)[0]
    assert result.source_uri == "runbooks/a.md"
    assert result.section_path == ["Setup", "Steps"]


def test_search_caps_chunks_per_document(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    chunks = [make_chunk(f"a:{i}", "a", f"content {i}", chunk_index=i) for i in range(5)]
    vectors = [unit_vector(1, 0, 0, 0) for _ in chunks]
    store.replace_document_chunks("a", chunks, vectors)

    results = store.search(unit_vector(1, 0, 0, 0), limit=10)
    assert len(results) <= 3


def test_empty_store_returns_no_results(tmp_path: Path):
    store = ChunkStore(str(tmp_path / "lancedb"), embedding_dimension=DIM)
    assert store.search(unit_vector(1, 0, 0, 0), limit=5) == []
