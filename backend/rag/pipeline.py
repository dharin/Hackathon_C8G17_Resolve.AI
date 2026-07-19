import logging
from functools import lru_cache

from config import settings
from rag.embedder import Embedder
from rag.loaders.confluence import ConfluenceLoader
from rag.loaders.local_directory import LocalSopLoader
from rag.retriever import Retriever
from rag.store import ChunkStore
from rag.sync import SyncCoordinator
from rag.sync_state import SyncStateStore

logger = logging.getLogger(__name__)

_CHUNK_CONFIG = {
    "target_tokens": settings.RAG_CHUNK_TARGET_TOKENS,
    "max_tokens": settings.RAG_CHUNK_MAX_TOKENS,
    "overlap_tokens": settings.RAG_CHUNK_OVERLAP_TOKENS,
    "min_tokens": settings.RAG_MIN_CHUNK_TOKENS,
}


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder(model_name=settings.RAG_EMBEDDING_MODEL)


@lru_cache(maxsize=1)
def get_store() -> ChunkStore:
    return ChunkStore(str(settings.LANCEDB_PATH), embedding_dimension=get_embedder().dimension)


@lru_cache(maxsize=1)
def get_sync_state() -> SyncStateStore:
    return SyncStateStore(settings.RAG_SYNC_STATE_DB_PATH)


@lru_cache(maxsize=1)
def get_sync_coordinator() -> SyncCoordinator:
    return SyncCoordinator(
        store=get_store(),
        sync_state=get_sync_state(),
        embedder=get_embedder(),
        chunk_config=_CHUNK_CONFIG,
    )


@lru_cache(maxsize=1)
def get_retriever() -> Retriever:
    return Retriever(store=get_store(), embedder=get_embedder())


def build_confluence_loader() -> ConfluenceLoader | None:
    if not settings.CONFLUENCE_SITE_URL or not settings.CONFLUENCE_API_TOKEN:
        return None
    return ConfluenceLoader(
        site_url=settings.CONFLUENCE_SITE_URL,
        email=settings.CONFLUENCE_EMAIL,
        api_token=settings.CONFLUENCE_API_TOKEN,
        cloud_id=settings.CONFLUENCE_CLOUD_ID,
        included_space_keys=settings.CONFLUENCE_INCLUDED_SPACE_KEYS,
        page_limit=settings.CONFLUENCE_PAGE_LIMIT,
        sync_concurrency=settings.CONFLUENCE_SYNC_CONCURRENCY,
    )


def build_local_sop_loader() -> LocalSopLoader:
    return LocalSopLoader(
        directory=settings.LOCAL_SOP_DIRECTORY,
        allowed_extensions=settings.LOCAL_SOP_ALLOWED_EXTENSIONS,
        recursive=settings.LOCAL_SOP_RECURSIVE,
    )


def ensure_index_ready() -> None:
    """Runs once at backend startup, in a background thread (see
    main.py's lifespan), so server startup itself is never blocked on it.

    If the LanceDB index already has chunks, this is a no-op — picking up
    new/changed source documents still requires the manual `POST
    /api/v1/rag/sync` trigger (see project-spec.md "Synchronization
    Schedule"). Only an empty index (first run against a fresh
    `LANCEDB_PATH`) gets built automatically here.
    """
    try:
        store = get_store()
        existing = store.count_rows()
        if existing > 0:
            logger.info("RAG index already has %d chunk(s) — skipping auto-build.", existing)
            return

        logger.info("RAG index is empty — building it now from configured sources.")
        coordinator = get_sync_coordinator()

        confluence_loader = build_confluence_loader()
        if confluence_loader is not None:
            summary = coordinator.sync_source(confluence_loader)
            logger.info("Confluence auto-index: %s", summary)
        else:
            logger.info("Confluence not configured — skipping.")

        local_summary = coordinator.sync_source(build_local_sop_loader())
        logger.info("Local SOP auto-index: %s", local_summary)
    except Exception:
        # Never crash startup over this — the manual /rag/sync endpoint
        # remains available if automatic indexing fails.
        logger.exception("Automatic RAG index build failed.")
