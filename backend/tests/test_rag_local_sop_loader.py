from pathlib import Path

from rag.loaders.local_directory import LocalSopLoader


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_discovers_markdown_and_text_files(tmp_path: Path):
    write(tmp_path / "runbook.md", "# Runbook\n\nSteps.")
    write(tmp_path / "notes.txt", "Plain text notes.")

    loader = LocalSopLoader(tmp_path, allowed_extensions={".md", ".txt"})
    documents = loader.discover()

    assert {d.source_uri for d in documents} == {"runbook.md", "notes.txt"}
    assert all(d.source_type == "local_sop" for d in documents)


def test_ignores_hidden_and_unsupported_files(tmp_path: Path):
    write(tmp_path / ".hidden.md", "# Hidden\n\nShould be ignored.")
    write(tmp_path / "image.png", "not text")
    write(tmp_path / "visible.md", "# Visible\n\nContent.")

    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"})
    documents = loader.discover()

    assert [d.source_uri for d in documents] == ["visible.md"]


def test_non_recursive_skips_subdirectories(tmp_path: Path):
    write(tmp_path / "top.md", "# Top\n\nContent.")
    write(tmp_path / "sub" / "nested.md", "# Nested\n\nContent.")

    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"}, recursive=False)
    documents = loader.discover()

    assert [d.source_uri for d in documents] == ["top.md"]


def test_recursive_includes_subdirectories(tmp_path: Path):
    write(tmp_path / "top.md", "# Top\n\nContent.")
    write(tmp_path / "sub" / "nested.md", "# Nested\n\nContent.")

    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"}, recursive=True)
    documents = loader.discover()

    assert {d.source_uri for d in documents} == {"top.md", "sub/nested.md"}


def test_deterministic_document_id_from_relative_path(tmp_path: Path):
    write(tmp_path / "a" / "b.md", "# B\n\nContent.")
    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"})
    documents = loader.discover()
    assert documents[0].document_id == "local-sop:a/b.md"


def test_content_hash_changes_when_file_changes(tmp_path: Path):
    path = tmp_path / "runbook.md"
    write(path, "# Runbook\n\nVersion one.")
    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"})
    first_hash = loader.discover()[0].content_hash

    write(path, "# Runbook\n\nVersion two.")
    second_hash = loader.discover()[0].content_hash

    assert first_hash != second_hash


def test_content_hash_stable_when_file_unchanged(tmp_path: Path):
    write(tmp_path / "runbook.md", "# Runbook\n\nStable content.")
    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"})
    first_hash = loader.discover()[0].content_hash
    second_hash = loader.discover()[0].content_hash
    assert first_hash == second_hash


def test_malformed_file_does_not_abort_entire_scan(tmp_path: Path):
    write(tmp_path / "good.md", "# Good\n\nFine content.")
    # A .docx extension with non-docx bytes should fail to parse but must not
    # stop discovery of the other, valid file.
    (tmp_path / "broken.docx").write_bytes(b"not a real docx file")

    loader = LocalSopLoader(tmp_path, allowed_extensions={".md", ".docx"})
    documents = loader.discover()

    assert [d.source_uri for d in documents] == ["good.md"]


def test_empty_file_is_skipped(tmp_path: Path):
    write(tmp_path / "empty.md", "   \n\n  ")
    loader = LocalSopLoader(tmp_path, allowed_extensions={".md"})
    assert loader.discover() == []


def test_missing_directory_returns_empty_list(tmp_path: Path):
    loader = LocalSopLoader(tmp_path / "does-not-exist", allowed_extensions={".md"})
    assert loader.discover() == []
