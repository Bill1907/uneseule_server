"""
Device API request/response schemas.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChildContext(BaseModel):
    """Child context for AI conversation."""

    child_id: str
    child_name: str
    child_age: int
    personality_traits: list[str] = Field(default_factory=list)


class VoiceTokenResponse(BaseModel):
    """Voice token response for LiveKit connection."""

    success: bool = True
    token: str = Field(..., description="LiveKit JWT access token")
    livekit_url: str = Field(..., description="LiveKit Cloud WebSocket URL")
    room_name: str = Field(..., description="Room name to join")
    expires_in: int = Field(900, description="Token validity in seconds (15 minutes)")
    child_context: Optional[ChildContext] = None


class DeviceHealthResponse(BaseModel):
    """Device health check response."""

    success: bool = True
    status: str = "healthy"
    device_id: str
    child_id: Optional[str] = None
    battery_level: Optional[int] = None
    connection_status: str
    server_time: datetime


class ErrorResponse(BaseModel):
    """Error response format."""

    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None


# ===== Device Registration =====


class DeviceRegisterRequest(BaseModel):
    """Device registration request."""

    serial_number: str = Field(..., min_length=1, max_length=100)
    device_type: str = Field(..., min_length=1, max_length=50)
    firmware_version: str = Field(..., min_length=1, max_length=20)


class DeviceRegisterResponse(BaseModel):
    """Device registration response."""

    success: bool = True
    device_id: str
    device_secret: str = Field(..., description="Store securely, shown only once")


# ===== Device Pairing =====


class DevicePairRequest(BaseModel):
    """Device pairing request."""

    pairing_code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")


class DevicePairResponse(BaseModel):
    """Device pairing response."""

    success: bool = True
    child_id: str
    child_name: str
    paired_at: datetime


class DeviceUnpairResponse(BaseModel):
    """Device unpairing response."""

    success: bool = True
    message: str = "Device unpaired successfully"
