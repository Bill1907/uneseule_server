"""
Unit tests for device HMAC authentication.
"""

import hashlib
import hmac
import time

import pytest

from app.api.v1.device.auth import verify_device_signature


class TestVerifyDeviceSignature:
    """Tests for HMAC signature verification."""

    @pytest.fixture
    def device_secret(self):
        """Test device secret."""
        return "test-device-secret-key"

    @pytest.fixture
    def serial_number(self):
        """Test serial number."""
        return "ABC123XYZ"

    def generate_signature(
        self,
        serial: str,
        timestamp: str,
        body: bytes,
        secret: str,
    ) -> str:
        """Generate valid HMAC signature for testing."""
        message = f"{serial}{timestamp}{body.decode('utf-8')}".encode()
        return hmac.new(secret.encode(), message, hashlib.sha256).hexdigest()

    def test_valid_signature(self, serial_number, device_secret):
        """Test valid signature verification."""
        timestamp = str(int(time.time()))
        body = b'{"test": "data"}'
        signature = self.generate_signature(
            serial_number, timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is True

    def test_valid_signature_empty_body(self, serial_number, device_secret):
        """Test valid signature with empty body."""
        timestamp = str(int(time.time()))
        body = b""
        signature = self.generate_signature(
            serial_number, timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is True

    def test_invalid_signature(self, serial_number, device_secret):
        """Test invalid signature detection."""
        timestamp = str(int(time.time()))
        body = b'{"test": "data"}'

        result = verify_device_signature(
            serial=serial_number,
            signature="invalid-signature",
            timestamp=timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is False

    def test_wrong_secret(self, serial_number, device_secret):
        """Test signature with wrong secret."""
        timestamp = str(int(time.time()))
        body = b'{"test": "data"}'
        signature = self.generate_signature(
            serial_number, timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=timestamp,
            body=body,
            secret="wrong-secret",
        )

        assert result is False

    def test_modified_body(self, serial_number, device_secret):
        """Test signature fails when body is modified."""
        timestamp = str(int(time.time()))
        original_body = b'{"test": "data"}'
        signature = self.generate_signature(
            serial_number, timestamp, original_body, device_secret
        )

        modified_body = b'{"test": "modified"}'
        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=timestamp,
            body=modified_body,
            secret=device_secret,
        )

        assert result is False

    def test_expired_timestamp(self, serial_number, device_secret):
        """Test signature fails for expired timestamp (> 5 minutes)."""
        old_timestamp = str(int(time.time()) - 400)  # 6+ minutes ago
        body = b'{"test": "data"}'
        signature = self.generate_signature(
            serial_number, old_timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=old_timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is False

    def test_future_timestamp(self, serial_number, device_secret):
        """Test signature fails for future timestamp (> 5 minutes)."""
        future_timestamp = str(int(time.time()) + 400)  # 6+ minutes in future
        body = b'{"test": "data"}'
        signature = self.generate_signature(
            serial_number, future_timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=future_timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is False

    def test_timestamp_within_window(self, serial_number, device_secret):
        """Test signature passes for timestamp within 5 minute window."""
        # 4 minutes ago (within window)
        recent_timestamp = str(int(time.time()) - 240)
        body = b'{"test": "data"}'
        signature = self.generate_signature(
            serial_number, recent_timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial=serial_number,
            signature=signature,
            timestamp=recent_timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is True

    def test_invalid_timestamp_format(self, serial_number, device_secret):
        """Test signature fails for invalid timestamp format."""
        body = b'{"test": "data"}'

        result = verify_device_signature(
            serial=serial_number,
            signature="any-signature",
            timestamp="not-a-number",
            body=body,
            secret=device_secret,
        )

        assert result is False

    def test_different_serial_numbers(self, device_secret):
        """Test signature is specific to serial number."""
        timestamp = str(int(time.time()))
        body = b'{"test": "data"}'

        signature = self.generate_signature(
            "SERIAL1", timestamp, body, device_secret
        )

        result = verify_device_signature(
            serial="SERIAL2",  # Different serial
            signature=signature,
            timestamp=timestamp,
            body=body,
            secret=device_secret,
        )

        assert result is False
