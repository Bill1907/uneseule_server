"""
Unit tests for VoiceTokenService.
"""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.elevenlabs import ElevenLabsAPIError, SignedUrlResponse
from app.services.voice_token_service import VoiceTokenService, TokenResult


class TestVoiceTokenService:
    """Tests for VoiceTokenService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis = AsyncMock()
        redis.get = AsyncMock(return_value=None)
        redis.incr = AsyncMock()
        redis.ttl = AsyncMock(return_value=-1)
        redis.expire = AsyncMock()
        return redis

    @pytest.fixture
    def mock_child(self):
        """Create mock child object."""
        child = MagicMock()
        child.id = uuid.uuid4()
        child.name = "테스트"
        child.is_active = True
        child.user_id = uuid.uuid4()
        child.birth_date = date(2020, 1, 1)
        child.age = 5
        child.personality_traits = {"traits": ["curious", "energetic"]}
        return child

    @pytest.fixture
    def mock_device(self, mock_child):
        """Create mock device object."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "ABC123"
        device.child_id = mock_child.id
        device.child = mock_child
        device.is_active = True
        device.last_seen = None
        device.connection_status = "offline"
        return device

    @pytest.fixture
    def mock_subscription(self):
        """Create mock subscription object."""
        subscription = MagicMock()
        subscription.user_id = uuid.uuid4()
        subscription.plan_type = "basic"
        subscription.status = "active"
        subscription.is_expired = False
        return subscription

    @pytest.mark.asyncio
    async def test_generate_token_success(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test successful token generation."""
        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ), patch(
            "app.services.voice_token_service.get_elevenlabs_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_signed_url = AsyncMock(
                return_value=SignedUrlResponse(
                    signed_url="wss://api.elevenlabs.io/test",
                    conversation_id="conv-123",
                )
            )
            mock_get_client.return_value = mock_client

            result = await service.generate_token(mock_device)

            assert result.success is True
            assert result.signed_url == "wss://api.elevenlabs.io/test"
            assert result.conversation_id == "conv-123"
            assert result.child_context is not None
            assert result.child_context.child_name == "테스트"
            assert result.child_context.child_age == 5

    @pytest.mark.asyncio
    async def test_generate_token_device_not_paired(self, mock_db, mock_redis):
        """Test token generation fails for unpaired device."""
        device = MagicMock()
        device.child_id = None  # Not paired

        service = VoiceTokenService(mock_db, mock_redis)
        result = await service.generate_token(device)

        assert result.success is False
        assert result.error_code == "DEVICE_NOT_PAIRED"

    @pytest.mark.asyncio
    async def test_generate_token_child_inactive(
        self, mock_db, mock_redis, mock_device
    ):
        """Test token generation fails for inactive child."""
        mock_device.child.is_active = False

        service = VoiceTokenService(mock_db, mock_redis)
        result = await service.generate_token(mock_device)

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_generate_token_child_none(self, mock_db, mock_redis, mock_device):
        """Test token generation fails when child is None."""
        mock_device.child = None

        service = VoiceTokenService(mock_db, mock_redis)
        result = await service.generate_token(mock_device)

        assert result.success is False
        assert result.error_code == "CHILD_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_generate_token_subscription_not_found(
        self, mock_db, mock_redis, mock_device
    ):
        """Test token generation fails when subscription not found."""
        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(service, "_get_subscription", return_value=None):
            result = await service.generate_token(mock_device)

            assert result.success is False
            assert result.error_code == "SUBSCRIPTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_generate_token_subscription_inactive(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test token generation fails for inactive subscription."""
        mock_subscription.status = "cancelled"

        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ):
            result = await service.generate_token(mock_device)

            assert result.success is False
            assert result.error_code == "SUBSCRIPTION_INACTIVE"

    @pytest.mark.asyncio
    async def test_generate_token_subscription_expired(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test token generation fails for expired subscription."""
        mock_subscription.is_expired = True

        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ):
            result = await service.generate_token(mock_device)

            assert result.success is False
            assert result.error_code == "SUBSCRIPTION_INACTIVE"

    @pytest.mark.asyncio
    async def test_generate_token_rate_limit_exceeded(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test token generation fails when rate limit exceeded."""
        mock_redis.get = AsyncMock(return_value="200")  # At limit for basic plan

        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ):
            result = await service.generate_token(mock_device)

            assert result.success is False
            assert result.error_code == "RATE_LIMIT_EXCEEDED"

    @pytest.mark.asyncio
    async def test_generate_token_premium_unlimited(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test premium users bypass rate limit."""
        mock_subscription.plan_type = "premium"
        mock_redis.get = AsyncMock(return_value="10000")  # High usage

        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ), patch(
            "app.services.voice_token_service.get_elevenlabs_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_signed_url = AsyncMock(
                return_value=SignedUrlResponse(
                    signed_url="wss://api.elevenlabs.io/test",
                )
            )
            mock_get_client.return_value = mock_client

            result = await service.generate_token(mock_device)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_generate_token_elevenlabs_error(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test token generation fails when ElevenLabs API fails."""
        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ), patch(
            "app.services.voice_token_service.get_elevenlabs_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_signed_url = AsyncMock(
                side_effect=ElevenLabsAPIError(500, "Internal error")
            )
            mock_get_client.return_value = mock_client

            result = await service.generate_token(mock_device)

            assert result.success is False
            assert result.error_code == "ELEVENLABS_ERROR"

    @pytest.mark.asyncio
    async def test_generate_token_without_redis(
        self, mock_db, mock_device, mock_subscription
    ):
        """Test token generation works without Redis (no rate limiting)."""
        service = VoiceTokenService(mock_db, redis=None)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ), patch(
            "app.services.voice_token_service.get_elevenlabs_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_signed_url = AsyncMock(
                return_value=SignedUrlResponse(
                    signed_url="wss://api.elevenlabs.io/test",
                )
            )
            mock_get_client.return_value = mock_client

            result = await service.generate_token(mock_device)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_generate_token_empty_personality_traits(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test token generation with empty personality traits."""
        mock_device.child.personality_traits = {}

        service = VoiceTokenService(mock_db, mock_redis)

        with patch.object(
            service, "_get_subscription", return_value=mock_subscription
        ), patch(
            "app.services.voice_token_service.get_elevenlabs_client"
        ) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_signed_url = AsyncMock(
                return_value=SignedUrlResponse(
                    signed_url="wss://api.elevenlabs.io/test",
                )
            )
            mock_get_client.return_value = mock_client

            result = await service.generate_token(mock_device)

            assert result.success is True
            assert result.child_context.personality_traits == []


class TestRateLimiting:
    """Tests for rate limiting logic."""

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def mock_redis(self):
        redis = AsyncMock()
        redis.get = AsyncMock()
        redis.incr = AsyncMock()
        redis.ttl = AsyncMock()
        redis.expire = AsyncMock()
        return redis

    @pytest.fixture
    def mock_device(self):
        device = MagicMock()
        device.id = uuid.uuid4()
        return device

    @pytest.fixture
    def mock_subscription(self):
        subscription = MagicMock()
        subscription.plan_type = "free"
        return subscription

    @pytest.mark.asyncio
    async def test_check_rate_limit_under_limit(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test rate limit check passes when under limit."""
        mock_redis.get = AsyncMock(return_value="10")  # 10 calls, limit is 50

        service = VoiceTokenService(mock_db, mock_redis)
        result = await service._check_rate_limit(mock_device, mock_subscription)

        assert result is True

    @pytest.mark.asyncio
    async def test_check_rate_limit_at_limit(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test rate limit check fails when at limit."""
        mock_redis.get = AsyncMock(return_value="50")  # At limit

        service = VoiceTokenService(mock_db, mock_redis)
        result = await service._check_rate_limit(mock_device, mock_subscription)

        assert result is False

    @pytest.mark.asyncio
    async def test_check_rate_limit_no_previous_calls(
        self, mock_db, mock_redis, mock_device, mock_subscription
    ):
        """Test rate limit check passes when no previous calls."""
        mock_redis.get = AsyncMock(return_value=None)

        service = VoiceTokenService(mock_db, mock_redis)
        result = await service._check_rate_limit(mock_device, mock_subscription)

        assert result is True

    @pytest.mark.asyncio
    async def test_increment_rate_limit_sets_expiry(
        self, mock_db, mock_redis, mock_device
    ):
        """Test rate limit increment sets expiry on new key."""
        mock_redis.ttl = AsyncMock(return_value=-1)  # No expiry

        service = VoiceTokenService(mock_db, mock_redis)
        await service._increment_rate_limit(mock_device)

        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_called_once()

    @pytest.mark.asyncio
    async def test_increment_rate_limit_preserves_expiry(
        self, mock_db, mock_redis, mock_device
    ):
        """Test rate limit increment preserves existing expiry."""
        mock_redis.ttl = AsyncMock(return_value=3600)  # 1 hour remaining

        service = VoiceTokenService(mock_db, mock_redis)
        await service._increment_rate_limit(mock_device)

        mock_redis.incr.assert_called_once()
        mock_redis.expire.assert_not_called()
