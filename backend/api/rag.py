from fastapi import APIRouter, Depends

from api.deps import get_current_user
from models.user import UserIdentity
from rag.models import RetrievedChunk, SourceSyncSummary
from rag.pipeline import build_confluence_loader, build_local_sop_loader, get_retriever, get_sync_coordinator

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])


@router.post("/sync", response_model=list[SourceSyncSummary])
def sync_knowledge_sources(
    _user: UserIdentity = Depends(get_current_user),
) -> list[SourceSyncSummary]:
    """Manual sync trigger for the hackathon demo (see project-spec.md
    "Synchronization Schedule"). Runs both sources; a missing/unconfigured
    Confluence source is skipped rather than treated as a failure.
    """
    coordinator = get_sync_coordinator()
    summaries: list[SourceSyncSummary] = []

    confluence_loader = build_confluence_loader()
    if confluence_loader is not None:
        summaries.append(coordinator.sync_source(confluence_loader))

    summaries.append(coordinator.sync_source(build_local_sop_loader()))
    return summaries


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
