import json
from datetime import datetime

import lancedb
import pyarrow as pa

from rag.models import DocumentChunk, RetrievedChunk

_TABLE_NAME = "knowledge_chunks"

# Chunks from the same document are capped at this many per query so one
# heavily-indexed page can't crowd out other relevant sources — satisfies
# "deduplicate overlapping results from the same document" without
# discarding genuinely distinct sections.
_MAX_CHUNKS_PER_DOCUMENT = 3


class ChunkStore:
    def __init__(self, db_path: str, embedding_dimension: int) -> None:
        self._db = lancedb.connect(db_path)
        self._dimension = embedding_dimension
        self._table = self._get_or_create_table()

    def _get_or_create_table(self):
        if _TABLE_NAME in self._db.table_names():
            return self._db.open_table(_TABLE_NAME)
        schema = pa.schema(
            [
                pa.field("chunk_id", pa.string()),
                pa.field("document_id", pa.string()),
                pa.field("source_type", pa.string()),
                pa.field("title", pa.string()),
                pa.field("source_uri", pa.string()),
                pa.field("section_path", pa.string()),
                pa.field("chunk_index", pa.int32()),
                pa.field("version", pa.string()),
                pa.field("content_hash", pa.string()),
                pa.field("content", pa.string()),
                pa.field("token_count", pa.int32()),
                pa.field("updated_at", pa.string()),
                pa.field("indexed_at", pa.string()),
                pa.field("metadata", pa.string()),
                pa.field("vector", pa.list_(pa.float32(), self._dimension)),
            ]
        )
        return self._db.create_table(_TABLE_NAME, schema=schema, mode="create", exist_ok=True)

    def replace_document_chunks(
        self,
        document_id: str,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
    ) -> None:
        self._table.delete(f"document_id = '{_escape(document_id)}'")
        if not chunks:
            return
        rows = [_chunk_to_row(chunk, vector) for chunk, vector in zip(chunks, vectors)]
        self._table.add(rows)

    def delete_document(self, document_id: str) -> None:
        self._table.delete(f"document_id = '{_escape(document_id)}'")

    def count_rows(self) -> int:
        return self._table.count_rows()

    def has_document(self, document_id: str) -> bool:
        """Whether any chunks for this document actually exist in the
        vector store — used to catch sync state claiming a document is
        indexed when the store itself has no record of it (e.g. sync
        state carried over to a machine with an empty local store).
        """
        return self._table.count_rows(f"document_id = '{_escape(document_id)}'") > 0

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        source_type: str | None = None,
        confluence_space_key: str | None = None,
        local_sop_path: str | None = None,
    ) -> list[RetrievedChunk]:
        if self._table.count_rows() == 0:
            return []

        query = self._table.search(query_vector).limit(max(limit * 4, limit))

        conditions = []
        if source_type:
            conditions.append(f"source_type = '{_escape(source_type)}'")
        if confluence_space_key:
            conditions.append(f"metadata LIKE '%\"space_key\": \"{_escape(confluence_space_key)}\"%'")
        if local_sop_path:
            conditions.append(f"source_uri LIKE '{_escape(local_sop_path)}%'")
        if conditions:
            query = query.where(" AND ".join(conditions))

        rows = query.to_list()
        return _dedupe_and_rank(rows, limit)


def _dedupe_and_rank(rows: list[dict], limit: int) -> list[RetrievedChunk]:
    seen_chunk_ids: set[str] = set()
    per_document_count: dict[str, int] = {}
    results: list[RetrievedChunk] = []

    # LanceDB vector search already returns rows ordered by ascending
    # distance (best match first).
    for row in rows:
        chunk_id = row["chunk_id"]
        if chunk_id in seen_chunk_ids:
            continue
        document_id = row["document_id"]
        if per_document_count.get(document_id, 0) >= _MAX_CHUNKS_PER_DOCUMENT:
            continue

        seen_chunk_ids.add(chunk_id)
        per_document_count[document_id] = per_document_count.get(document_id, 0) + 1

        distance = row.get("_distance", 0.0)
        score = max(0.0, 1.0 - distance / 2.0)  # cosine distance in [0, 2] -> similarity in [0, 1]

        results.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                content=row["content"],
                score=round(score, 4),
                source_type=row["source_type"],
                title=row["title"],
                source_uri=row["source_uri"],
                section_path=json.loads(row["section_path"]),
                updated_at=datetime.fromisoformat(row["updated_at"]) if row.get("updated_at") else None,
                metadata=json.loads(row["metadata"]),
            )
        )
        if len(results) >= limit:
            break

    return results


def _chunk_to_row(chunk: DocumentChunk, vector: list[float]) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "source_type": chunk.source_type,
        "title": chunk.title,
        "source_uri": chunk.source_uri,
        "section_path": json.dumps(chunk.section_path),
        "chunk_index": chunk.chunk_index,
        "version": chunk.version,
        "content_hash": chunk.content_hash,
        "content": chunk.content,
        "token_count": chunk.token_count,
        "updated_at": chunk.updated_at.isoformat() if chunk.updated_at else None,
        "indexed_at": chunk.indexed_at.isoformat(),
        "metadata": json.dumps(chunk.metadata, default=str),
        "vector": vector,
    }


def _escape(value: str) -> str:
    return value.replace("'", "''")
