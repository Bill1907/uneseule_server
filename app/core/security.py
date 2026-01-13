"""
Security utilities for authentication and authorization.
Handles JWT tokens, password hashing, and verification.

Supports:
- Neon Auth JWT verification (JWKS/EdDSA+RS256) for user authentication
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


class JWKSClient:
    """JWKS client for Neon Auth JWT verification (EdDSA/RS256 지원)."""

    def __init__(self, jwks_url: str, cache_ttl: int = 3600):
        self.jwks_url = jwks_url
        self._jwk_client = PyJWKClient(jwks_url, cache_keys=True, lifespan=cache_ttl)

    def get_signing_key(self, token: str):
        """토큰에서 kid를 추출하고 해당 키 반환."""
        return self._jwk_client.get_signing_key_from_jwt(token)


# Global JWKS client for Neon Auth
_jwks_client: JWKSClient | None = None


def get_jwks_client() -> JWKSClient:
    """Get or create JWKS client singleton."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = f"{settings.NEON_AUTH_URL}/.well-known/jwks.json"
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
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key(token)

            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["EdDSA", "RS256"],  # EdDSA (Ed25519) + RS256 지원
                options={"verify_aud": False},  # Neon Auth doesn't set audience
            )
            return payload
        except PyJWTError as e:
            logger.debug(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.warning(f"Unexpected error during token verification: {e}")
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
