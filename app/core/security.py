"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and verification.

Supports:
- Clerk JWT verification (JWKS/RS256) for user authentication
- Legacy JWT (HS256) for device authentication
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from app.core.config import settings

logger = logging.getLogger(__name__)


class ClerkJWKSClient:
    """JWKS client for Clerk JWT verification (RS256)."""

    def __init__(self, jwks_url: str, cache_ttl: int = 3600):
        self.jwks_url = jwks_url
        self._jwk_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=cache_ttl)

    def get_signing_key(self, token: str):
        """Extract kid from token and return corresponding signing key."""
        return self._jwk_client.get_signing_key_from_jwt(token)


# Global JWKS client for Clerk
_clerk_jwks_client: ClerkJWKSClient | None = None


def get_clerk_jwks_client() -> ClerkJWKSClient:
    """Get or create Clerk JWKS client singleton."""
    global _clerk_jwks_client
    if _clerk_jwks_client is None:
        # Clerk JWKS URL format: https://<clerk-frontend-api>/.well-known/jwks.json
        # The secret key format is sk_test_xxx or sk_live_xxx
        # Extract the frontend API from secret key pattern or use explicit config

        # Try to get JWKS URL from environment or derive from Clerk domain
        # For now, we'll use the Clerk SDK to verify tokens
        jwks_url = getattr(settings, 'CLERK_JWKS_URL', None)
        if not jwks_url:
            # Default Clerk JWKS pattern - user should set CLERK_JWKS_URL
            # Example: https://your-app.clerk.accounts.dev/.well-known/jwks.json
            raise ValueError(
                "CLERK_JWKS_URL must be set. "
                "Get it from Clerk Dashboard > API Keys > JWKS URL"
            )
        _clerk_jwks_client = ClerkJWKSClient(jwks_url, cache_ttl=3600)
    return _clerk_jwks_client


class ClerkAuthVerifier:
    """Clerk JWT verification utilities."""

    @staticmethod
    async def verify_token(token: str) -> dict[str, Any] | None:
        """
        Verify a Clerk JWT token using JWKS.

        Args:
            token: JWT token string from Clerk

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            jwks_client = get_clerk_jwks_client()
            signing_key = jwks_client.get_signing_key(token)

            # Clerk uses RS256 algorithm
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={
                    "verify_aud": False,  # Clerk doesn't use aud claim by default
                },
            )

            # Optionally verify authorized parties (azp claim)
            authorized_parties = settings.CLERK_AUTHORIZED_PARTIES
            if authorized_parties:
                azp = payload.get("azp")
                if azp and azp not in authorized_parties:
                    logger.debug(f"Unauthorized party: {azp}")
                    return None

            return payload
        except PyJWTError as e:
            logger.debug(f"Token verification failed: {e}")
            return None
        except ValueError as e:
            # JWKS URL not configured
            logger.error(f"Clerk configuration error: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error during token verification: {e}")
            return None

    @staticmethod
    def get_user_id_from_payload(payload: dict[str, Any]) -> str | None:
        """Extract user ID from Clerk JWT payload (sub claim, e.g., user_xxx)."""
        return payload.get("sub")

    @staticmethod
    def get_user_email_from_payload(payload: dict[str, Any]) -> str | None:
        """Extract user email from Clerk JWT payload."""
        # Clerk stores email in different ways depending on session
        # Check common locations
        return payload.get("email") or payload.get("primary_email")

    @staticmethod
    def get_user_name_from_payload(payload: dict[str, Any]) -> str | None:
        """Extract user name from Clerk JWT payload."""
        # Clerk may have first_name and last_name or full name
        first_name = payload.get("first_name", "")
        last_name = payload.get("last_name", "")
        if first_name or last_name:
            return f"{first_name} {last_name}".strip()
        return payload.get("name")


# Global instance for Clerk Auth verification
clerk_auth = ClerkAuthVerifier()


class SecurityUtils:
    """Security utilities for password hashing and legacy JWT operations (device auth)."""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        salt = bcrypt.gensalt(rounds=settings.PASSWORD_BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to check against

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    @staticmethod
    def create_access_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Create a JWT access token (legacy, for device auth).

        Args:
            data: Data to encode in the token
            expires_delta: Optional custom expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(data: dict[str, Any]) -> str:
        """
        Create a JWT refresh token (legacy, for device auth).

        Args:
            data: Data to encode in the token

        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """
        Decode and validate a JWT token (legacy, for device auth).

        Args:
            token: JWT token string to decode

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
            )
            return payload
        except PyJWTError:
            return None

    @staticmethod
    def verify_token_type(payload: dict[str, Any], expected_type: str) -> bool:
        """
        Verify token type (access or refresh).

        Args:
            payload: Decoded token payload
            expected_type: Expected token type ("access" or "refresh")

        Returns:
            True if token type matches, False otherwise
        """
        return payload.get("type") == expected_type


# Create a global instance for easy access
security = SecurityUtils()
