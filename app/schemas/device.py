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
