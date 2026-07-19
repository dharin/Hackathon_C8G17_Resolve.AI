from models.user import UserIdentity
from services.auth.base import AuthError, AuthProvider

MOCK_USER = UserIdentity(
    id="mock-user-id",
    email="dev@example.com",
    username="dev",
    full_name="Local Dev User",
)


class MockAuthProvider(AuthProvider):
    """Accepts any non-empty bearer token and returns a fixed dev identity.

    Local development only — selected via AUTH_PROVIDER=mock when no Clerk
    instance is configured. Never use in a deployed environment.
    """

    def verify_token(self, token: str) -> UserIdentity:
        if not token:
            raise AuthError("Missing bearer token")
        return MOCK_USER
