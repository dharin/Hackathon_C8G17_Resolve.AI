from pydantic import BaseModel


class IntegrationHealth(BaseModel):
    key: str
    name: str
    healthy: bool
    status_text: str
    detail: str | None = None


class HealthCheckResult(BaseModel):
    integrations: list[IntegrationHealth]
