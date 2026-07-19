from pydantic import BaseModel


class UserIdentity(BaseModel):
    """Safe identity object exposed to API consumers — no raw token claims."""

    id: str
    email: str | None = None
    username: str | None = None
    full_name: str | None = None
    image_url: str | None = None
