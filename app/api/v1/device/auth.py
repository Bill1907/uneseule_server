"""
Device authentication using HMAC-SHA256 signatures.
Devices authenticate with serial number + signature instead of JWT.
"""

import hashlib
import hmac
import time
from typing import Optional, Any

from fastapi import Header, HTTPException, status

# TODO: Import Device model when implemented
# from app.models.device import Device
Device = Any  # Temporary type alias


# TODO: Implement device secret retrieval from database
def get_device_secret(serial_number: str) -> Optional[str]:
    """
    Retrieve device secret key from database.

    Args:
        serial_number: Device serial number

    Returns:
        Device secret key or None if not found
    """
    # Placeholder - should query database
    return None


def verify_device_signature(
    serial: str,
    signature: str,
    timestamp: str,
    body: bytes,
    secret: str,
) -> bool:
    """
    Verify HMAC-SHA256 signature for device request.

    Args:
        serial: Device serial number
        signature: HMAC signature from request header
        timestamp: Request timestamp
        body: Raw request body
        secret: Device secret key

    Returns:
        True if signature is valid, False otherwise
    """
    # Check timestamp freshness (within 5 minutes)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        if abs(current_time - request_time) > 300:  # 5 minutes
            return False
    except ValueError:
        return False

    # Compute expected signature
    message = f"{serial}{timestamp}{body.decode('utf-8')}".encode()
    expected_signature = hmac.new(
        secret.encode(), message, hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(signature, expected_signature)


async def verify_device(
    x_device_serial: str = Header(..., description="Device serial number"),
    x_device_signature: str = Header(..., description="HMAC-SHA256 signature"),
    x_device_timestamp: str = Header(..., description="Request timestamp"),
) -> Device:
    """
    FastAPI dependency to verify device authentication.

    Args:
        x_device_serial: Device serial number from header
        x_device_signature: HMAC signature from header
        x_device_timestamp: Request timestamp from header

    Returns:
        Authenticated Device object

    Raises:
        HTTPException: If authentication fails
    """
    # TODO: Retrieve device and secret from database
    secret = get_device_secret(x_device_serial)

    if not secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device serial number",
        )

    # TODO: Get request body for signature verification
    # This is a placeholder - actual implementation needs request body
    body = b""

    if not verify_device_signature(
        x_device_serial, x_device_signature, x_device_timestamp, body, secret
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device signature",
        )

    # TODO: Return actual device from database
    # This is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Device authentication not fully implemented",
    )
