import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import tiktoken

from rag.models import DocumentChunk, KnowledgeDocument

# Used only as an internal, consistent token-count proxy for chunk sizing —
# not tied to the configured embedding model's own tokenizer.
_ENCODING = tiktoken.get_encoding("cl100k_base")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)")
_LIST_ITEM_RE = re.compile(r"^(-|\*|\d+\.)\s")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


def count_tokens(text: str) -> int:
    return len(_ENCODING.encode(text))


@dataclass
class _Block:
    text: str
    kind: str  # heading | paragraph | list | table | code
    section_path: list[str] = field(default_factory=list)


def _split_blocks(content: str) -> list[_Block]:
    """Splits normalized Markdown-ish text into structural blocks, tracking
    the heading path so each block knows which section it belongs to.
    Tables and code blocks are kept atomic — they're re-split by token
    boundary only as a last resort in `_split_oversized`.
    """
    lines = content.splitlines()
    blocks: list[_Block] = []
    section_path: list[str] = []
    buffer: list[str] = []
    i, n = 0, len(lines)

    def flush(kind: str = "paragraph") -> None:
        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                blocks.append(_Block(text=text, kind=kind, section_path=list(section_path)))
            buffer.clear()

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("```"):
            flush()
            code_lines = [line]
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < n:
                code_lines.append(lines[i])
                i += 1
            blocks.append(_Block(text="\n".join(code_lines), kind="code", section_path=list(section_path)))
            continue

        heading_match = _HEADING_RE.match(stripped)
        if heading_match:
            flush()
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            section_path = section_path[: level - 1] + [title]
            blocks.append(_Block(text=stripped, kind="heading", section_path=list(section_path)))
            i += 1
            continue

        if stripped.startswith("|"):
            flush()
            table_lines = []
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            blocks.append(_Block(text="\n".join(table_lines), kind="table", section_path=list(section_path)))
            continue

        if stripped == "":
            flush()
            i += 1
            continue

        if _LIST_ITEM_RE.match(stripped):
            flush()
            list_lines = []
            while i < n and lines[i].strip() != "":
                list_lines.append(lines[i])
                i += 1
            blocks.append(_Block(text="\n".join(list_lines), kind="list", section_path=list(section_path)))
            continue

        buffer.append(line)
        i += 1

    flush()
    return blocks


def _split_oversized(block: _Block, max_tokens: int) -> list[_Block]:
    """Last-resort splitting for a single block that alone exceeds the max
    chunk size: try sentence boundaries first, then fall back to raw token
    slicing so nothing is ever silently dropped.
    """
    if block.kind not in {"paragraph"}:
        return _split_by_tokens(block, max_tokens)

    sentences = _SENTENCE_SPLIT_RE.split(block.text)
    pieces: list[_Block] = []
    current: list[str] = []
    current_tokens = 0
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        if sentence_tokens > max_tokens:
            if current:
                pieces.append(_Block(text=" ".join(current), kind=block.kind, section_path=block.section_path))
                current, current_tokens = [], 0
            pieces.extend(_split_by_tokens(_Block(text=sentence, kind=block.kind, section_path=block.section_path), max_tokens))
            continue
        if current_tokens + sentence_tokens > max_tokens:
            pieces.append(_Block(text=" ".join(current), kind=block.kind, section_path=block.section_path))
            current, current_tokens = [sentence], sentence_tokens
        else:
            current.append(sentence)
            current_tokens += sentence_tokens
    if current:
        pieces.append(_Block(text=" ".join(current), kind=block.kind, section_path=block.section_path))
    return pieces


def _split_by_tokens(block: _Block, max_tokens: int) -> list[_Block]:
    tokens = _ENCODING.encode(block.text)
    pieces = []
    for start in range(0, len(tokens), max_tokens):
        piece_tokens = tokens[start : start + max_tokens]
        pieces.append(_Block(text=_ENCODING.decode(piece_tokens), kind=block.kind, section_path=block.section_path))
    return pieces


def _group_blocks(blocks: list[_Block], target_tokens: int, max_tokens: int) -> list[list[_Block]]:
    groups: list[list[_Block]] = []
    current: list[_Block] = []
    current_tokens = 0

    def close() -> None:
        nonlocal current, current_tokens
        if current:
            groups.append(current)
        current, current_tokens = [], 0

    for block in blocks:
        block_tokens = count_tokens(block.text)

        if block_tokens > max_tokens:
            close()
            for sub in _split_oversized(block, max_tokens):
                groups.append([sub])
            continue

        if current and current_tokens + block_tokens > max_tokens:
            close()

        current.append(block)
        current_tokens += block_tokens

        if current_tokens >= target_tokens:
            close()

    close()
    return groups


def _merge_undersized(groups: list[list[_Block]], min_tokens: int) -> list[list[_Block]]:
    """Folds any chunk below the minimum useful size into its neighbor so
    retrieval never returns near-empty fragments.
    """
    if len(groups) <= 1:
        return groups

    merged: list[list[_Block]] = []
    for group in groups:
        tokens = sum(count_tokens(b.text) for b in group)
        if tokens < min_tokens and merged:
            merged[-1] = merged[-1] + group
        else:
            merged.append(group)
    return merged


def _apply_overlap(group_texts: list[str], overlap_tokens: int) -> list[str]:
    if overlap_tokens <= 0:
        return group_texts

    result = [group_texts[0]]
    for text in group_texts[1:]:
        previous_tokens = _ENCODING.encode(result[-1])
        tail_tokens = previous_tokens[-overlap_tokens:]
        if tail_tokens:
            tail_text = _ENCODING.decode(tail_tokens)
            result.append(f"{tail_text}\n\n{text}")
        else:
            result.append(text)
    return result


def chunk_document(
    document: KnowledgeDocument,
    *,
    target_tokens: int = 650,
    max_tokens: int = 900,
    overlap_tokens: int = 100,
    min_tokens: int = 100,
) -> list[DocumentChunk]:
    blocks = _split_blocks(document.content)
    if not blocks:
        return []

    groups = _group_blocks(blocks, target_tokens, max_tokens)
    groups = _merge_undersized(groups, min_tokens)
    if not groups:
        return []

    texts = [_render_group(group) for group in groups]
    texts = _apply_overlap(texts, overlap_tokens)

    now = datetime.now(timezone.utc)
    chunks: list[DocumentChunk] = []
    for index, (group, text) in enumerate(zip(groups, texts)):
        section_path = group[-1].section_path
        chunks.append(
            DocumentChunk(
                chunk_id=_deterministic_chunk_id(document, index),
                document_id=document.document_id,
                source_type=document.source_type,
                title=document.title,
                source_uri=document.source_uri,
                section_path=section_path,
                chunk_index=index,
                version=document.version,
                content_hash=document.content_hash,
                content=text,
                token_count=count_tokens(text),
                updated_at=document.updated_at,
                indexed_at=now,
                metadata=document.metadata,
            )
        )
    return chunks


def _render_group(group: list[_Block]) -> str:
    return "\n\n".join(block.text for block in group).strip()


def _deterministic_chunk_id(document: KnowledgeDocument, chunk_index: int) -> str:
    if document.source_type == "confluence":
        page_id = document.metadata.get("page_id", document.document_id)
        return f"confluence:{page_id}:v{document.version}:chunk-{chunk_index}"

    path_hash = hashlib.sha256(document.source_uri.encode("utf-8")).hexdigest()[:16]
    content_hash_prefix = document.content_hash[:8]
    return f"local-sop:{path_hash}:v{content_hash_prefix}:chunk-{chunk_index}"
