"""
Unit tests for Neon Auth JWT verification.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

from app.core.security import JWKSClient, NeonAuthVerifier, get_jwks_client


class TestJWKSClient:
    """Tests for JWKS client."""

    @pytest.fixture
    def jwks_client(self):
        return JWKSClient(
            jwks_url="https://auth.test.neon.tech/api/auth/.well-known/jwks",
            cache_ttl=3600,
        )

    @pytest.fixture
    def mock_jwks_response(self):
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "kid": "test-key-id",
                    "use": "sig",
                    "alg": "RS256",
                    "n": "test-modulus",
                    "e": "AQAB",
                }
            ]
        }

    @pytest.mark.asyncio
    async def test_get_jwks_fetches_from_url(self, jwks_client, mock_jwks_response):
        """JWKS client should fetch keys from URL."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks_response
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.security.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await jwks_client.get_jwks()

            assert result == mock_jwks_response

    @pytest.mark.asyncio
    async def test_get_jwks_uses_cache(self, jwks_client, mock_jwks_response):
        """JWKS client should cache results."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks_response
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.security.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            # First call
            await jwks_client.get_jwks()
            # Second call should use cache
            await jwks_client.get_jwks()

            assert mock_instance.get.call_count == 1

    @pytest.mark.asyncio
    async def test_get_signing_key_returns_key(self, jwks_client, mock_jwks_response):
        """Should return signing key by kid."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks_response
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.security.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await jwks_client.get_signing_key("test-key-id")

            assert result["kid"] == "test-key-id"

    @pytest.mark.asyncio
    async def test_get_signing_key_returns_none_for_unknown_kid(
        self, jwks_client, mock_jwks_response
    ):
        """Should return None for unknown key ID."""
        mock_response = MagicMock()
        mock_response.json.return_value = mock_jwks_response
        mock_response.raise_for_status = MagicMock()

        with patch("app.core.security.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await jwks_client.get_signing_key("unknown-key-id")

            assert result is None


class TestNeonAuthVerifier:
    """Tests for Neon Auth JWT verification."""

    @pytest.fixture
    def verifier(self):
        return NeonAuthVerifier()

    @pytest.fixture
    def valid_payload(self):
        return {
            "sub": "user-123",
            "email": "test@example.com",
            "iat": 1234567890,
            "exp": 9999999999,
        }

    def test_get_user_id_from_payload(self, verifier, valid_payload):
        """Should extract user ID from payload."""
        result = verifier.get_user_id_from_payload(valid_payload)
        assert result == "user-123"

    def test_get_user_id_from_payload_missing_sub(self, verifier):
        """Should return None if sub is missing."""
        result = verifier.get_user_id_from_payload({})
        assert result is None

    def test_get_user_email_from_payload(self, verifier, valid_payload):
        """Should extract email from payload."""
        result = verifier.get_user_email_from_payload(valid_payload)
        assert result == "test@example.com"

    def test_get_user_email_from_payload_missing_email(self, verifier):
        """Should return None if email is missing."""
        result = verifier.get_user_email_from_payload({})
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_invalid_token(self, verifier):
        """Should return None for invalid token."""
        result = await verifier.verify_token("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_when_no_kid(self, verifier):
        """Should return None when token has no kid."""
        # Create a token without kid in header
        with patch.object(jwt, "get_unverified_header", return_value={}):
            result = await verifier.verify_token("token-without-kid")
            assert result is None


class TestGetJwksClient:
    """Tests for JWKS client singleton."""

    def test_returns_same_instance(self):
        """Should return same client instance."""
        # Reset singleton
        import app.core.security as security_module

        security_module._jwks_client = None

        client1 = get_jwks_client()
        client2 = get_jwks_client()

        assert client1 is client2

        # Cleanup
        security_module._jwks_client = None
