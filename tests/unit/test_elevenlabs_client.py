"""
Unit tests for ElevenLabs client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import httpx

from app.integrations.elevenlabs import (
    ElevenLabsClient,
    ElevenLabsAPIError,
    SignedUrlResponse,
)


class TestElevenLabsClient:
    """Tests for ElevenLabsClient."""

    @pytest.fixture
    def client(self):
        """Create test client with mock settings."""
        return ElevenLabsClient(
            api_key="test-api-key",
            base_url="https://api.elevenlabs.io/v1",
            agent_id="test-agent-id",
        )

    @pytest.mark.asyncio
    async def test_get_signed_url_success(self, client):
        """Test successful signed URL retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "signed_url": "wss://api.elevenlabs.io/v1/convai/conversation?signature=abc123",
            "conversation_id": "conv-123",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await client.get_signed_url()

            assert isinstance(result, SignedUrlResponse)
            assert result.signed_url == "wss://api.elevenlabs.io/v1/convai/conversation?signature=abc123"
            assert result.conversation_id == "conv-123"

            # Verify API call
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "convai/conversation/get-signed-url" in call_args[0][0]
            assert call_args[1]["headers"]["xi-api-key"] == "test-api-key"
            assert call_args[1]["params"]["agent_id"] == "test-agent-id"

    @pytest.mark.asyncio
    async def test_get_signed_url_with_custom_agent_id(self, client):
        """Test signed URL with custom agent ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "signed_url": "wss://example.com/ws",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            result = await client.get_signed_url(agent_id="custom-agent-id")

            call_args = mock_client.get.call_args
            assert call_args[1]["params"]["agent_id"] == "custom-agent-id"

    @pytest.mark.asyncio
    async def test_get_signed_url_api_error(self, client):
        """Test API error handling."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ElevenLabsAPIError) as exc_info:
                await client.get_signed_url()

            assert exc_info.value.status_code == 401
            assert "Unauthorized" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_signed_url_timeout(self, client):
        """Test timeout handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ElevenLabsAPIError) as exc_info:
                await client.get_signed_url()

            assert exc_info.value.status_code == 408
            assert "timeout" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_get_signed_url_request_error(self, client):
        """Test request error handling."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                side_effect=httpx.RequestError("Connection failed")
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(ElevenLabsAPIError) as exc_info:
                await client.get_signed_url()

            assert exc_info.value.status_code == 500
