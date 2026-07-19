from datetime import datetime, timezone

from rag.chunker import chunk_document, count_tokens
from rag.models import KnowledgeDocument


def make_document(content: str, **overrides) -> KnowledgeDocument:
    defaults = dict(
        document_id="local-sop:runbooks/disk.md",
        source_type="local_sop",
        title="Disk Runbook",
        content=content,
        source_uri="runbooks/disk.md",
        version="abc123456789",
        content_hash="abc123456789def0",
        updated_at=datetime.now(timezone.utc),
        metadata={},
    )
    defaults.update(overrides)
    return KnowledgeDocument(**defaults)


def test_small_document_produces_one_chunk():
    doc = make_document("# Title\n\nA short paragraph about disk cleanup.")
    chunks = chunk_document(doc, target_tokens=650, max_tokens=900, overlap_tokens=100, min_tokens=10)
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].document_id == doc.document_id
    assert chunks[0].source_type == "local_sop"


def test_long_document_splits_into_multiple_chunks_within_max_tokens():
    paragraph = "This line describes a remediation step in reasonable detail. " * 20
    sections = "\n\n".join(f"## Section {i}\n\n{paragraph}" for i in range(10))
    doc = make_document(sections)

    chunks = chunk_document(doc, target_tokens=200, max_tokens=300, overlap_tokens=20, min_tokens=20)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.token_count <= 300 + 20  # allow overlap prefix slack
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_oversized_single_block_is_split_by_sentence_or_token_boundary():
    huge_sentence = "word " * 2000  # one giant "paragraph" with no natural sentence breaks
    doc = make_document(huge_sentence)

    chunks = chunk_document(doc, target_tokens=100, max_tokens=150, overlap_tokens=0, min_tokens=10)

    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk.content) <= 150


def test_table_and_code_blocks_stay_intact_when_they_fit():
    table = "| A | B |\n| --- | --- |\n| 1 | 2 |"
    code = "```bash\nsystemctl restart nginx\n```"
    doc = make_document(f"# Runbook\n\n{table}\n\n{code}\n\nSome closing notes.")

    chunks = chunk_document(doc, target_tokens=650, max_tokens=900, overlap_tokens=100, min_tokens=10)

    combined = "\n\n".join(c.content for c in chunks)
    assert table in combined
    assert code in combined


def test_deterministic_chunk_ids_for_local_sop():
    doc = make_document("# A\n\nSome content.", content_hash="deadbeef01234567")
    chunks = chunk_document(doc)
    assert chunks[0].chunk_id.startswith("local-sop:")
    assert chunks[0].chunk_id.endswith(":chunk-0")
    assert "deadbeef" in chunks[0].chunk_id


def test_deterministic_chunk_ids_for_confluence():
    doc = make_document(
        "# A\n\nSome content.",
        source_type="confluence",
        document_id="confluence:123",
        version="4",
        metadata={"page_id": "123"},
    )
    chunks = chunk_document(doc)
    assert chunks[0].chunk_id == "confluence:123:v4:chunk-0"


def test_section_path_reflects_heading_hierarchy():
    doc = make_document("# Top\n\n## Sub\n\nSome content under sub heading.")
    chunks = chunk_document(doc, target_tokens=650, max_tokens=900, overlap_tokens=0, min_tokens=1)
    assert chunks[-1].section_path == ["Top", "Sub"]


def test_repeated_calls_are_idempotent():
    doc = make_document("# Title\n\nParagraph one.\n\nParagraph two.")
    first = chunk_document(doc)
    second = chunk_document(doc)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert [c.content for c in first] == [c.content for c in second]
