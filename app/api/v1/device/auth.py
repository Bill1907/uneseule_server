"""
Device authentication using HMAC-SHA256 signatures.

Devices authenticate with serial number + signature instead of JWT.
"""

import hashlib
import hmac
import time

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.models.device import Device
from app.repositories.device_repository import DeviceRepository


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
    # Message format: "{serial}{timestamp}{body}"
    message = f"{serial}{timestamp}{body.decode('utf-8')}".encode()
    expected_signature = hmac.new(
        secret.encode(), message, hashlib.sha256
    ).hexdigest()

    # Constant-time comparison to prevent timing attacks
    return hmac.compare_digest(signature, expected_signature)


async def verify_device(
    request: Request,
    x_device_serial: str = Header(..., description="Device serial number"),
    x_device_signature: str = Header(..., description="HMAC-SHA256 signature"),
    x_device_timestamp: str = Header(..., description="Request timestamp"),
    db: AsyncSession = Depends(get_db),
) -> Device:
    """
    FastAPI dependency to verify device authentication.

    Args:
        request: FastAPI request object (for body access)
        x_device_serial: Device serial number from header
        x_device_signature: HMAC signature from header
        x_device_timestamp: Request timestamp from header
        db: Database session

    Returns:
        Authenticated Device object

    Raises:
        HTTPException: If authentication fails
    """
    # Get request body for signature verification
    body = await request.body()

    # Retrieve device from database
    device_repo = DeviceRepository(db)
    device = await device_repo.get_by_serial_number(
        x_device_serial,
        include_child=True,
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device serial number",
        )

    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device is deactivated",
        )

    # Verify HMAC signature
    if not verify_device_signature(
        x_device_serial,
        x_device_signature,
        x_device_timestamp,
        body,
        device.device_secret,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid device signature",
        )

    return device
