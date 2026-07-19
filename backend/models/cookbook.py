from pydantic import BaseModel, Field


class Cookbook(BaseModel):
    """An executable runbook derived from the RCA and remediation
    recommendations. Every entry in `commands`/`validation`/`rollback` is
    extracted verbatim from a recommendation's retrieved source content —
    never generated — so nothing here can be an invented step.
    """

    root_cause: str
    steps: list[str] = Field(default_factory=list)
    commands: list[str] = Field(default_factory=list)
    validation: list[str] = Field(default_factory=list)
    rollback: list[str] = Field(default_factory=list)
