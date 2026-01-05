"""
End-to-end tests for device token API.
"""

import hashlib
import hmac
import time
import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.device.router import router
from app.integrations.elevenlabs import SignedUrlResponse


# Create test app
app = FastAPI()
app.include_router(router, prefix="/api/v1")


def generate_hmac_headers(
    serial: str,
    secret: str,
    body: str = "",
) -> dict:
    """Generate HMAC authentication headers for testing."""
    timestamp = str(int(time.time()))
    message = f"{serial}{timestamp}{body}".encode()
    signature = hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    return {
        "X-Device-Serial": serial,
        "X-Device-Signature": signature,
        "X-Device-Timestamp": timestamp,
    }


class TestDeviceTokenEndpoint:
    """Tests for POST /api/v1/device/token endpoint."""

    @pytest.fixture
    def mock_device(self):
        """Create mock device."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "TEST123"
        device.device_secret = "test-secret"
        device.is_active = True
        device.child_id = uuid.uuid4()
        device.battery_level = 80
        device.connection_status = "online"
        device.last_seen = None

        # Mock child
        child = MagicMock()
        child.id = device.child_id
        child.name = "테스트아이"
        child.is_active = True
        child.user_id = uuid.uuid4()
        child.birth_date = date(2020, 5, 15)
        child.age = 4
        child.personality_traits = {"traits": ["playful"]}
        device.child = child

        return device

    @pytest.fixture
    def mock_subscription(self):
        """Create mock subscription."""
        subscription = MagicMock()
        subscription.plan_type = "basic"
        subscription.status = "active"
        subscription.is_expired = False
        return subscription

    def test_token_endpoint_success(self, mock_device, mock_subscription):
        """Test successful token request."""
        headers = generate_hmac_headers(
            mock_device.serial_number,
            mock_device.device_secret,
        )

        with patch(
            "app.api.v1.device.auth.DeviceRepository"
        ) as MockDeviceRepo, patch(
            "app.api.v1.device.router.get_db"
        ), patch(
            "app.api.v1.device.router.get_redis"
        ) as mock_get_redis, patch(
            "app.services.voice_token_service.get_elevenlabs_client"
        ) as mock_get_client:
            # Setup mocks
            mock_repo = AsyncMock()
            mock_repo.get_by_serial_number = AsyncMock(return_value=mock_device)
            mock_repo.update_last_seen = AsyncMock()
            MockDeviceRepo.return_value = mock_repo

            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value=None)
            mock_redis.incr = AsyncMock()
            mock_redis.ttl = AsyncMock(return_value=-1)
            mock_redis.expire = AsyncMock()
            mock_get_redis.return_value = mock_redis

            mock_client = AsyncMock()
            mock_client.get_signed_url = AsyncMock(
                return_value=SignedUrlResponse(
                    signed_url="wss://api.elevenlabs.io/v1/convai/test",
                    conversation_id="conv-abc123",
                )
            )
            mock_get_client.return_value = mock_client

            # Also mock subscription query
            with patch(
                "app.services.voice_token_service.VoiceTokenService._get_subscription",
                return_value=mock_subscription,
            ):
                client = TestClient(app)
                response = client.post(
                    "/api/v1/device/token",
                    headers=headers,
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "signed_url" in data
                assert data["expires_in"] == 900

    def test_token_endpoint_invalid_serial(self):
        """Test token request with invalid serial number."""
        headers = generate_hmac_headers("INVALID", "any-secret")

        with patch(
            "app.api.v1.device.auth.DeviceRepository"
        ) as MockDeviceRepo, patch("app.api.v1.device.auth.get_db"):
            mock_repo = AsyncMock()
            mock_repo.get_by_serial_number = AsyncMock(return_value=None)
            MockDeviceRepo.return_value = mock_repo

            client = TestClient(app)
            response = client.post(
                "/api/v1/device/token",
                headers=headers,
            )

            assert response.status_code == 401

    def test_token_endpoint_invalid_signature(self, mock_device):
        """Test token request with invalid HMAC signature."""
        headers = {
            "X-Device-Serial": mock_device.serial_number,
            "X-Device-Signature": "invalid-signature",
            "X-Device-Timestamp": str(int(time.time())),
        }

        with patch(
            "app.api.v1.device.auth.DeviceRepository"
        ) as MockDeviceRepo, patch("app.api.v1.device.auth.get_db"):
            mock_repo = AsyncMock()
            mock_repo.get_by_serial_number = AsyncMock(return_value=mock_device)
            MockDeviceRepo.return_value = mock_repo

            client = TestClient(app)
            response = client.post(
                "/api/v1/device/token",
                headers=headers,
            )

            assert response.status_code == 401

    def test_token_endpoint_expired_timestamp(self, mock_device):
        """Test token request with expired timestamp."""
        old_timestamp = str(int(time.time()) - 400)  # 6+ minutes ago
        message = f"{mock_device.serial_number}{old_timestamp}".encode()
        signature = hmac.new(
            mock_device.device_secret.encode(), message, hashlib.sha256
        ).hexdigest()

        headers = {
            "X-Device-Serial": mock_device.serial_number,
            "X-Device-Signature": signature,
            "X-Device-Timestamp": old_timestamp,
        }

        with patch(
            "app.api.v1.device.auth.DeviceRepository"
        ) as MockDeviceRepo, patch("app.api.v1.device.auth.get_db"):
            mock_repo = AsyncMock()
            mock_repo.get_by_serial_number = AsyncMock(return_value=mock_device)
            MockDeviceRepo.return_value = mock_repo

            client = TestClient(app)
            response = client.post(
                "/api/v1/device/token",
                headers=headers,
            )

            assert response.status_code == 401

    def test_token_endpoint_device_not_paired(self, mock_device, mock_subscription):
        """Test token request for unpaired device."""
        mock_device.child_id = None
        mock_device.child = None

        headers = generate_hmac_headers(
            mock_device.serial_number,
            mock_device.device_secret,
        )

        with patch(
            "app.api.v1.device.auth.DeviceRepository"
        ) as MockDeviceRepo, patch(
            "app.api.v1.device.router.get_db"
        ), patch(
            "app.api.v1.device.router.get_redis"
        ) as mock_get_redis:
            mock_repo = AsyncMock()
            mock_repo.get_by_serial_number = AsyncMock(return_value=mock_device)
            MockDeviceRepo.return_value = mock_repo

            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            client = TestClient(app)
            response = client.post(
                "/api/v1/device/token",
                headers=headers,
            )

            assert response.status_code == 400
            data = response.json()
            assert data["error_code"] == "DEVICE_NOT_PAIRED"

    def test_token_endpoint_missing_headers(self):
        """Test token request with missing headers."""
        client = TestClient(app)
        response = client.post("/api/v1/device/token")

        assert response.status_code == 422  # Validation error


class TestDeviceHealthEndpoint:
    """Tests for GET /api/v1/device/health endpoint."""

    @pytest.fixture
    def mock_device(self):
        """Create mock device."""
        device = MagicMock()
        device.id = uuid.uuid4()
        device.serial_number = "HEALTH123"
        device.device_secret = "health-secret"
        device.is_active = True
        device.child_id = uuid.uuid4()
        device.battery_level = 75
        device.connection_status = "online"
        device.child = MagicMock()
        device.child.is_active = True
        return device

    def test_health_endpoint_success(self, mock_device):
        """Test successful health check."""
        headers = generate_hmac_headers(
            mock_device.serial_number,
            mock_device.device_secret,
        )

        with patch(
            "app.api.v1.device.auth.DeviceRepository"
        ) as MockDeviceRepo, patch("app.api.v1.device.auth.get_db"):
            mock_repo = AsyncMock()
            mock_repo.get_by_serial_number = AsyncMock(return_value=mock_device)
            MockDeviceRepo.return_value = mock_repo

            client = TestClient(app)
            response = client.get(
                "/api/v1/device/health",
                headers=headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "healthy"
            assert data["battery_level"] == 75
            assert data["connection_status"] == "online"
