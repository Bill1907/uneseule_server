"""
Unit tests for Clerk JWT verification.
"""

from unittest.mock import MagicMock, patch

import jwt
import pytest

from app.core.security import ClerkJWKSClient, ClerkAuthVerifier, get_clerk_jwks_client


class TestClerkJWKSClient:
    """Tests for Clerk JWKS client."""

    @pytest.fixture
    def jwks_client(self):
        return ClerkJWKSClient(
            jwks_url="https://test.clerk.accounts.dev/.well-known/jwks.json",
            cache_ttl=3600,
        )

    def test_jwks_client_initializes_pyjwk_client(self, jwks_client):
        """JWKS client should initialize PyJWKClient internally."""
        assert jwks_client._jwk_client is not None
        assert jwks_client.jwks_url == "https://test.clerk.accounts.dev/.well-known/jwks.json"

    def test_get_signing_key_delegates_to_pyjwk_client(self, jwks_client):
        """get_signing_key should delegate to PyJWKClient."""
        mock_key = MagicMock()
        with patch.object(
            jwks_client._jwk_client,
            "get_signing_key_from_jwt",
            return_value=mock_key,
        ) as mock_method:
            result = jwks_client.get_signing_key("test-token")
            mock_method.assert_called_once_with("test-token")
            assert result == mock_key


class TestClerkAuthVerifier:
    """Tests for Clerk JWT verification."""

    @pytest.fixture
    def verifier(self):
        return ClerkAuthVerifier()

    @pytest.fixture
    def valid_payload(self):
        return {
            "sub": "user_2NNEqL2nrIRdJ194ndJqAHwEfxC",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "iat": 1234567890,
            "exp": 9999999999,
        }

    def test_get_user_id_from_payload(self, verifier, valid_payload):
        """Should extract Clerk user ID from payload."""
        result = verifier.get_user_id_from_payload(valid_payload)
        assert result == "user_2NNEqL2nrIRdJ194ndJqAHwEfxC"

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

    def test_get_user_name_from_payload(self, verifier, valid_payload):
        """Should extract full name from first_name and last_name."""
        result = verifier.get_user_name_from_payload(valid_payload)
        assert result == "Test User"

    def test_get_user_name_from_payload_first_name_only(self, verifier):
        """Should handle first_name only."""
        result = verifier.get_user_name_from_payload({"first_name": "Test"})
        assert result == "Test"

    def test_get_user_name_from_payload_fallback_to_name(self, verifier):
        """Should fallback to name field if first/last name not present."""
        result = verifier.get_user_name_from_payload({"name": "Full Name"})
        assert result == "Full Name"

    @pytest.mark.asyncio
    async def test_verify_token_returns_none_for_invalid_token(self, verifier):
        """Should return None for invalid token."""
        result = await verifier.verify_token("invalid-token")
        assert result is None

    @pytest.mark.asyncio
    async def test_verify_token_success(self, verifier, valid_payload):
        """Should return payload for valid token."""
        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-key"

        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key.return_value = mock_signing_key

        with patch("app.core.security.get_clerk_jwks_client", return_value=mock_jwks_client):
            with patch.object(jwt, "decode", return_value=valid_payload):
                result = await verifier.verify_token("valid-token")
                assert result == valid_payload

    @pytest.mark.asyncio
    async def test_verify_token_rejects_unauthorized_party(self, verifier, valid_payload):
        """Should reject token with unauthorized azp claim."""
        payload_with_azp = {**valid_payload, "azp": "https://unauthorized.com"}

        mock_signing_key = MagicMock()
        mock_signing_key.key = "mock-key"

        mock_jwks_client = MagicMock()
        mock_jwks_client.get_signing_key.return_value = mock_signing_key

        with patch("app.core.security.get_clerk_jwks_client", return_value=mock_jwks_client):
            with patch.object(jwt, "decode", return_value=payload_with_azp):
                with patch("app.core.security.settings") as mock_settings:
                    mock_settings.CLERK_AUTHORIZED_PARTIES = ["http://localhost:3000"]
                    result = await verifier.verify_token("valid-token")
                    assert result is None


class TestGetClerkJwksClient:
    """Tests for Clerk JWKS client singleton."""

    def test_returns_same_instance(self):
        """Should return same client instance."""
        # Reset singleton
        import app.core.security as security_module

        security_module._clerk_jwks_client = None

        client1 = get_clerk_jwks_client()
        client2 = get_clerk_jwks_client()

        assert client1 is client2

        # Cleanup
        security_module._clerk_jwks_client = None
