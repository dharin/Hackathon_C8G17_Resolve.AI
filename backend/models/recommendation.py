from pydantic import BaseModel, Field

from rag.models import RetrievedChunk


class Recommendation(BaseModel):
    """A single grounded remediation recommendation. `sources` reuses
    `rag.models.RetrievedChunk` directly rather than a separate
    source-reference model — it already carries every field the UI needs
    (title, source_type, source_uri, section_path, updated_at).
    """

    title: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str
    sources: list[RetrievedChunk] = Field(min_length=1)
