import os
from functools import lru_cache

from services.auth.base import AuthProvider
from services.auth.clerk_provider import ClerkAuthProvider
from services.auth.mock_provider import MockAuthProvider


@lru_cache
def get_auth_provider() -> AuthProvider:
    """Selects the auth backend via AUTH_PROVIDER (clerk | mock). Cached as a singleton."""
    provider = os.environ.get("AUTH_PROVIDER", "clerk").lower()
    if provider == "mock":
        return MockAuthProvider()
    if provider == "clerk":
        return ClerkAuthProvider()
    raise ValueError(f"Unknown AUTH_PROVIDER: {provider!r}")
