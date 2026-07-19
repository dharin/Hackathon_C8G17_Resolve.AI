from abc import ABC, abstractmethod

from models.user import UserIdentity


class AuthError(Exception):
    """Raised when a bearer token is missing, malformed, or fails verification."""


class AuthProvider(ABC):
    """Abstraction over bearer-token verification.

    Lets the API depend on identity resolution without caring whether tokens
    are verified against real Clerk infrastructure or a local mock.
    """

    @abstractmethod
    def verify_token(self, token: str) -> UserIdentity:
        """Verify a bearer token and return the identity it belongs to.

        Raises AuthError if the token is missing, malformed, or invalid.
        """
