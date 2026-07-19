import os
from typing import Any

import httpx
import jwt
from jwt import PyJWKClient

from models.user import UserIdentity
from services.auth.base import AuthError, AuthProvider

CLERK_API_BASE = "https://api.clerk.com/v1"


class ClerkAuthProvider(AuthProvider):
    """Verifies Clerk-issued session JWTs against Clerk's published JWKS.

    Session tokens only carry a stable subject (sub) claim by default; the
    rest of the profile (email, username, name) is resolved via a follow-up
    call to Clerk's Backend API using CLERK_SECRET_KEY.
    """

    def __init__(self, jwks_url: str | None = None, secret_key: str | None = None) -> None:
        jwks_url = jwks_url or os.environ.get("CLERK_JWKS_URL")
        if not jwks_url:
            raise AuthError(
                "CLERK_JWKS_URL is not configured; required when AUTH_PROVIDER=clerk"
            )
        self._jwks_client = PyJWKClient(jwks_url)
        self._secret_key = secret_key or os.environ.get("CLERK_SECRET_KEY")

    def verify_token(self, token: str) -> UserIdentity:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise AuthError(f"Invalid or expired token: {exc}") from exc

        user_id = claims.get("sub")
        if not user_id:
            raise AuthError("Token is missing a subject (sub) claim")

        return self._fetch_identity(user_id)

    def _fetch_identity(self, user_id: str) -> UserIdentity:
        if not self._secret_key:
            # Degrade gracefully: identity limited to what the token itself proves.
            return UserIdentity(id=user_id)

        try:
            response = httpx.get(
                f"{CLERK_API_BASE}/users/{user_id}",
                headers={"Authorization": f"Bearer {self._secret_key}"},
                timeout=5.0,
            )
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise AuthError(f"Failed to fetch user profile from Clerk: {exc}") from exc

        data = response.json()
        primary_email = next(
            (
                entry["email_address"]
                for entry in data.get("email_addresses", [])
                if entry.get("id") == data.get("primary_email_address_id")
            ),
            None,
        )
        full_name = (
            " ".join(part for part in [data.get("first_name"), data.get("last_name")] if part)
            or None
        )

        return UserIdentity(
            id=user_id,
            email=primary_email,
            username=data.get("username"),
            full_name=full_name,
            image_url=data.get("image_url"),
        )
