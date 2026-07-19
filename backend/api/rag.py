import logging

from fastapi import APIRouter, Depends

from api.deps import get_current_user
from models.rag_sync_result import RagSyncResult, RagSyncStatus
from models.user import UserIdentity
from rag.models import RetrievedChunk, SourceSyncSummary
from rag.pipeline import build_confluence_loader, build_local_sop_loader, get_retriever, get_sync_coordinator
from services import rag_sync_meta_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.get("/status", response_model=RagSyncStatus)
def get_sync_status(
    _user: UserIdentity = Depends(get_current_user),
) -> RagSyncStatus:
    """Read-only — lets the "Update Knowledgebase" button on the RAG
    Configuration tab show the last successful sync date on page load,
    without requiring a sync to have run in the current session.
    """
    return RagSyncStatus(last_synced_at=rag_sync_meta_store.get_last_synced_at())


@router.post("/sync", response_model=RagSyncResult)
def sync_knowledge_sources(
    _user: UserIdentity = Depends(get_current_user),
) -> RagSyncResult:
    """"Update Knowledgebase" trigger (see project-spec.md "Synchronization
    Schedule"). Uses the exact same sync coordinator and loaders as every
    other sync path in the app — nothing here is a separate implementation.

    The persisted last-synced-at timestamp only advances when every
    configured source completes without an unhandled error. If a source
    fails outright (e.g. Confluence auth/network failure before any page
    is even reached), that source's failure is isolated and reported in
    `errors`, but the timestamp is left at its previous value — the UI
    "rolls back" to it rather than showing a stale success.
    """
    coordinator = get_sync_coordinator()
    summaries: list[SourceSyncSummary] = []
    errors: list[str] = []

    confluence_loader = build_confluence_loader()
    if confluence_loader is not None:
        try:
            summaries.append(coordinator.sync_source(confluence_loader))
        except Exception as exc:  # noqa: BLE001 - isolate per-source failure
            logger.warning("Confluence knowledge-base sync failed: %s", exc)
            errors.append(f"confluence: {exc}")

    try:
        summaries.append(coordinator.sync_source(build_local_sop_loader()))
    except Exception as exc:  # noqa: BLE001 - isolate per-source failure
        logger.warning("Local SOP knowledge-base sync failed: %s", exc)
        errors.append(f"local_sop: {exc}")

    if not errors:
        rag_sync_meta_store.set_last_synced_at()

    return RagSyncResult(
        summaries=summaries,
        last_synced_at=rag_sync_meta_store.get_last_synced_at(),
        errors=errors,
    )


@router.get("/retrieve", response_model=list[RetrievedChunk])
def retrieve(
    query: str,
    limit: int = 10,
    source_type: str | None = None,
    confluence_space_key: str | None = None,
    local_sop_path: str | None = None,
    _user: UserIdentity = Depends(get_current_user),
) -> list[RetrievedChunk]:
    return get_retriever().retrieve(
        query,
        limit=limit,
        source_type=source_type,
        confluence_space_key=confluence_space_key,
        local_sop_path=local_sop_path,
    )
