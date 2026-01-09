"""
Device REST API endpoints.

Simple, stateless operations for IoT smart toy devices.
Device registration and pairing are handled via GraphQL (parent app).
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.device.auth import verify_device
from app.core.dependencies import get_db, get_redis
from app.models.device import Device
from app.schemas.device import (
    DeviceHealthResponse,
    DeviceUnpairResponse,
    ErrorResponse,
    VoiceTokenResponse,
)
from app.services.device_service import DeviceService
from app.services.voice_token_service import VoiceTokenService


router = APIRouter(prefix="/device", tags=["device"])


# NOTE: Device registration and pairing are now handled via GraphQL
# See app/graphql/mutations/device.py - registerDevice mutation


@router.delete(
    "/pair",
    response_model=DeviceUnpairResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Device not paired"},
    },
)
async def unpair_device(
    device: Device = Depends(verify_device),
    db: AsyncSession = Depends(get_db),
):
    """
    Unpair device from child profile.

    Requires device authentication (HMAC signature).

    Returns:
        Confirmation message
    """
    service = DeviceService(db)
    result = await service.unpair(device)

    if not result.success:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error_code": result.error_code,
                "message": result.error_message,
            },
        )

    return DeviceUnpairResponse(success=True)


@router.post(
    "/token",
    response_model=VoiceTokenResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Device not paired"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        403: {"model": ErrorResponse, "description": "Subscription inactive"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "LiveKit API error"},
    },
)
async def get_voice_token(
    device: Device = Depends(verify_device),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    """
    Get AI voice session token from LiveKit Cloud.

    Requires device authentication (HMAC signature).

    Returns:
        - token: LiveKit JWT access token
        - livekit_url: LiveKit Cloud WebSocket URL
        - room_name: Room name to join
        - expires_in: Token validity in seconds (15 minutes)
        - child_context: Child profile for AI context

    Error codes:
        - DEVICE_NOT_PAIRED: Device not paired with child
        - CHILD_NOT_FOUND: Paired child not found
        - SUBSCRIPTION_NOT_FOUND: Parent subscription not found
        - SUBSCRIPTION_INACTIVE: Parent subscription inactive
        - RATE_LIMIT_EXCEEDED: Daily limit exceeded
        - LIVEKIT_ERROR: LiveKit token generation failure
    """
    service = VoiceTokenService(db, redis)
    result = await service.generate_token(device)

    if not result.success:
        status_codes = {
            "DEVICE_NOT_PAIRED": status.HTTP_400_BAD_REQUEST,
            "CHILD_NOT_FOUND": status.HTTP_400_BAD_REQUEST,
            "SUBSCRIPTION_NOT_FOUND": status.HTTP_403_FORBIDDEN,
            "SUBSCRIPTION_INACTIVE": status.HTTP_403_FORBIDDEN,
            "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
            "LIVEKIT_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        return JSONResponse(
            status_code=status_codes.get(result.error_code, 500),
            content={
                "success": False,
                "error_code": result.error_code,
                "message": result.error_message,
            },
        )

    return VoiceTokenResponse(
        success=True,
        token=result.token,
        livekit_url=result.livekit_url,
        room_name=result.room_name,
        expires_in=900,  # 15 minutes
        child_context=result.child_context,
    )


@router.get("/health", response_model=DeviceHealthResponse)
async def device_health(device: Device = Depends(verify_device)):
    """
    Device health check endpoint.

    Requires device authentication (HMAC signature).

    Args:
        device: Authenticated device from dependency

    Returns:
        Health status and device information
    """
    return DeviceHealthResponse(
        success=True,
        status="healthy",
        device_id=str(device.id),
        child_id=str(device.child_id) if device.child_id else None,
        battery_level=device.battery_level,
        connection_status=device.connection_status,
        server_time=datetime.now(timezone.utc),
    )
