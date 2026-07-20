import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api.deps import get_current_user
from config.settings import LOCAL_SOP_ALLOWED_EXTENSIONS, LOCAL_SOP_DIRECTORY
from models.rag_sync_result import RagSyncResult, RagSyncStatus
from models.user import UserIdentity
from rag.models import RetrievedChunk, SourceSyncSummary
from rag.pipeline import build_confluence_loader, build_local_sop_loader, get_retriever, get_sync_coordinator
from services import rag_sync_meta_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])

# Browsers can't render .docx inline; it downloads instead, which is an
# acceptable fallback for "open in a new tab". .md is served as plain text
# rather than text/markdown so it displays instead of prompting a download.
_LOCAL_SOP_MEDIA_TYPES = {
    ".md": "text/plain; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


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


@router.get("/sops/{relative_path:path}")
def get_local_sop_file(
    relative_path: str,
    _user: UserIdentity = Depends(get_current_user),
) -> FileResponse:
    """Serves a local SOP document's raw content so the "Supporting sources"
    list can open it in a new browser tab the same way a Confluence link
    does — Confluence source_uri values are already real URLs, but local
    SOPs only ever carried a relative filename with nothing to serve it.

    The path is resolved and re-checked against the configured SOP
    directory (not just prefix-matched) so a `../` or an absolute
    `relative_path` can't escape it — see rag/loaders/local_directory.py for
    the same directory this endpoint reads from.
    """
    base_dir = LOCAL_SOP_DIRECTORY.resolve()
    candidate = (base_dir / relative_path).resolve()
    if candidate != base_dir and base_dir not in candidate.parents:
        raise HTTPException(status_code=404, detail="SOP document not found")

    extension = candidate.suffix.lower()
    if extension not in LOCAL_SOP_ALLOWED_EXTENSIONS or extension not in _LOCAL_SOP_MEDIA_TYPES:
        raise HTTPException(status_code=404, detail="SOP document not found")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="SOP document not found")

    return FileResponse(
        candidate,
        media_type=_LOCAL_SOP_MEDIA_TYPES[extension],
        filename=candidate.name,
        content_disposition_type="inline",
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
