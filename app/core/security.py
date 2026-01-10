"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and verification.

Supports:
- Neon Auth JWT verification (JWKS/RS256) for user authentication
- Legacy JWT (HS256) for device authentication
"""

import time
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import httpx
from jose import JWTError, jwt
from jose.exceptions import JWKError

from app.core.config import settings


class JWKSClient:
    """JWKS client for Neon Auth JWT verification."""

    def __init__(self, jwks_url: str, cache_ttl: int = 3600):
        self.jwks_url = jwks_url
        self.cache_ttl = cache_ttl
        self._jwks: dict[str, Any] | None = None
        self._last_fetch: float = 0

    async def get_jwks(self) -> dict[str, Any]:
        """Fetch JWKS from Neon Auth, with caching."""
        now = time.time()
        if self._jwks and (now - self._last_fetch) < self.cache_ttl:
            return self._jwks

        async with httpx.AsyncClient() as client:
            response = await client.get(self.jwks_url, timeout=10.0)
            response.raise_for_status()
            self._jwks = response.json()
            self._last_fetch = now
            return self._jwks

    async def get_signing_key(self, kid: str) -> dict[str, Any] | None:
        """Get signing key by key ID."""
        jwks = await self.get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        # Key not found, try refreshing JWKS
        self._jwks = None
        jwks = await self.get_jwks()
        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None


# Global JWKS client for Neon Auth
_jwks_client: JWKSClient | None = None


def get_jwks_client() -> JWKSClient:
    """Get or create JWKS client singleton."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.NEON_AUTH_URL}/api/auth/.well-known/jwks"
        _jwks_client = JWKSClient(jwks_url, settings.NEON_AUTH_JWKS_CACHE_TTL)
    return _jwks_client


class NeonAuthVerifier:
    """Neon Auth JWT verification utilities."""

    @staticmethod
    async def verify_token(token: str) -> dict[str, Any] | None:
        """
        Verify a Neon Auth JWT token using JWKS.

        Args:
            token: JWT token string from Neon Auth

        Returns:
            Decoded token payload or None if invalid
        """
        try:
            # Get unverified header to find key ID
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")

            if not kid:
                return None

            # Fetch signing key from JWKS
            jwks_client = get_jwks_client()
            signing_key = await jwks_client.get_signing_key(kid)

            if not signing_key:
                return None

            # Verify and decode the token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=["RS256"],
                options={"verify_aud": False},  # Neon Auth doesn't set audience
            )
            return payload
        except (JWTError, JWKError):
            return None

    @staticmethod
    def get_user_id_from_payload(payload: dict[str, Any]) -> str | None:
        """Extract user ID from Neon Auth JWT payload."""
        return payload.get("sub")

    @staticmethod
    def get_user_email_from_payload(payload: dict[str, Any]) -> str | None:
        """Extract user email from Neon Auth JWT payload."""
        return payload.get("email")


# Global instance for Neon Auth verification
neon_auth = NeonAuthVerifier()


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
        Create a JWT access token.

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
        Create a JWT refresh token.

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
        Decode and validate a JWT token.

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
        except JWTError:
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
