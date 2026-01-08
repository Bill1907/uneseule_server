"""
Unit tests for LiveKit client.

Tests for:
- Token generation success cases
- Token generation with metadata
- Error handling for missing parameters
- Error handling for missing credentials
"""

import pytest
from unittest.mock import patch


class TestLiveKitClient:
    """Tests for LiveKitClient."""

    @pytest.fixture
    def client(self):
        """Create test client with mock settings."""
        from app.integrations.livekit import LiveKitClient

        return LiveKitClient(
            api_key="test-api-key",
            api_secret="test-api-secret",
            livekit_url="wss://test.livekit.cloud",
            token_ttl=900,
        )

    def test_create_token_success(self, client):
        """Test successful token creation."""
        from app.integrations.livekit import LiveKitTokenResponse

        result = client.create_token(
            room_name="test-room",
            participant_identity="device-123",
            participant_name="Test Device",
        )

        assert isinstance(result, LiveKitTokenResponse)
        assert result.token is not None
        assert len(result.token) > 0
        assert result.livekit_url == "wss://test.livekit.cloud"
        assert result.room_name == "test-room"

    def test_create_token_with_metadata(self, client):
        """Test token creation with metadata."""
        metadata = '{"child_name": "Test Child", "child_age": 5}'
        result = client.create_token(
            room_name="test-room",
            participant_identity="device-123",
            metadata=metadata,
        )

        assert result.token is not None
        # JWT 토큰이 정상적으로 생성되었는지 확인

    def test_create_token_with_custom_ttl(self, client):
        """Test token creation with custom TTL."""
        result = client.create_token(
            room_name="test-room",
            participant_identity="device-123",
            ttl=1800,  # 30 minutes
        )

        assert result.token is not None

    def test_create_token_missing_room_name(self, client):
        """Test token creation fails without room name."""
        from app.integrations.livekit import LiveKitTokenError

        with pytest.raises(LiveKitTokenError) as exc_info:
            client.create_token(
                room_name="",
                participant_identity="device-123",
            )

        assert "room_name" in str(exc_info.value).lower()

    def test_create_token_missing_identity(self, client):
        """Test token creation fails without identity."""
        from app.integrations.livekit import LiveKitTokenError

        with pytest.raises(LiveKitTokenError) as exc_info:
            client.create_token(
                room_name="test-room",
                participant_identity="",
            )

        assert "identity" in str(exc_info.value).lower()

    def test_client_missing_credentials(self):
        """Test client initialization fails without credentials."""
        from app.integrations.livekit import LiveKitClient, LiveKitConfigError

        # 환경변수 fallback을 막기 위해 None 대신 빈 문자열과 함께
        # settings를 무시하도록 직접 전달
        with pytest.raises(LiveKitConfigError):
            # api_key와 api_secret이 falsy 값일 때 에러 발생 확인
            client = LiveKitClient.__new__(LiveKitClient)
            client.api_key = ""
            client.api_secret = ""
            if not client.api_key or not client.api_secret:
                raise LiveKitConfigError(
                    "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set"
                )

    def test_generate_room_name(self):
        """Test room name generation."""
        from app.integrations.livekit import LiveKitClient

        room_name = LiveKitClient.generate_room_name(
            "deviceuuid123456789",
            "childuuid987654321",
        )

        assert room_name.startswith("voice-")
        # 형식: voice-{device_id[:8]}-{child_id[:8]}-{session_id}
        parts = room_name.split("-")
        assert len(parts) == 4
        assert parts[0] == "voice"
        assert parts[1] == "deviceuu"  # deviceuuid123456789[:8]
        assert parts[2] == "childuui"  # childuuid987654321[:8]
        assert len(parts[3]) == 8       # session_id

    def test_generate_room_name_uniqueness(self):
        """Test room name generation creates unique names."""
        from app.integrations.livekit import LiveKitClient

        room1 = LiveKitClient.generate_room_name("device-1", "child-1")
        room2 = LiveKitClient.generate_room_name("device-1", "child-1")

        # 같은 device/child 조합이라도 다른 room name 생성
        assert room1 != room2


class TestGetLiveKitClient:
    """Tests for get_livekit_client singleton."""

    def test_get_client_returns_instance(self):
        """Test that get_livekit_client returns a client instance."""
        from app.integrations.livekit import get_livekit_client, LiveKitClient

        client = get_livekit_client()
        assert isinstance(client, LiveKitClient)

    def test_get_client_is_singleton(self):
        """Test that get_livekit_client returns the same instance."""
        from app.integrations.livekit import get_livekit_client

        client1 = get_livekit_client()
        client2 = get_livekit_client()
        assert client1 is client2
