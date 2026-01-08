"""
LiveKit Cloud integration client.

Handles JWT token generation for real-time voice/video rooms.
"""

import logging
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from livekit import api

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LiveKitTokenResponse:
    """LiveKit token response."""

    token: str
    livekit_url: str
    room_name: str


class LiveKitConfigError(Exception):
    """LiveKit configuration error."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"LiveKit config error: {detail}")


class LiveKitTokenError(Exception):
    """LiveKit token generation error."""

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"LiveKit token error: {detail}")


class LiveKitClient:
    """
    LiveKit API client for token generation.

    Handles:
    - JWT access token generation
    - Room name generation
    - Participant identity management
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        livekit_url: Optional[str] = None,
        token_ttl: Optional[int] = None,
    ):
        self.api_key = api_key if api_key else settings.LIVEKIT_API_KEY
        self.api_secret = api_secret if api_secret else settings.LIVEKIT_API_SECRET
        self.livekit_url = livekit_url if livekit_url else settings.LIVEKIT_URL
        self.token_ttl = token_ttl if token_ttl else settings.LIVEKIT_TOKEN_TTL

        if not self.api_key or not self.api_secret:
            raise LiveKitConfigError(
                "LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set"
            )

    def create_token(
        self,
        room_name: str,
        participant_identity: str,
        participant_name: Optional[str] = None,
        metadata: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> LiveKitTokenResponse:
        """
        Create LiveKit access token for room connection.

        Args:
            room_name: Name of the room to join
            participant_identity: Unique identifier for the participant
            participant_name: Display name for the participant
            metadata: JSON string metadata to attach to participant
            ttl: Token validity in seconds (default: 15 minutes)

        Returns:
            LiveKitTokenResponse with token, url, and room_name

        Raises:
            LiveKitTokenError: If token generation fails
        """
        if not room_name:
            raise LiveKitTokenError("room_name is required")

        if not participant_identity:
            raise LiveKitTokenError("participant_identity is required")

        try:
            token_ttl = timedelta(seconds=ttl or self.token_ttl)

            token_builder = (
                api.AccessToken(self.api_key, self.api_secret)
                .with_identity(participant_identity)
                .with_ttl(token_ttl)
                .with_grants(
                    api.VideoGrants(
                        room_join=True,
                        room=room_name,
                    )
                )
            )

            if participant_name:
                token_builder = token_builder.with_name(participant_name)

            if metadata:
                token_builder = token_builder.with_metadata(metadata)

            token = token_builder.to_jwt()

            return LiveKitTokenResponse(
                token=token,
                livekit_url=self.livekit_url,
                room_name=room_name,
            )

        except Exception as e:
            logger.error(f"LiveKit token generation failed: {e}")
            raise LiveKitTokenError(str(e))

    @staticmethod
    def generate_room_name(device_id: str, child_id: str) -> str:
        """Generate unique room name for device-child session."""
        session_id = uuid.uuid4().hex[:8]
        return f"voice-{device_id[:8]}-{child_id[:8]}-{session_id}"


# Singleton instance (lazy initialization)
_livekit_client: Optional[LiveKitClient] = None


def get_livekit_client() -> LiveKitClient:
    """Get or create LiveKit client singleton."""
    global _livekit_client
    if _livekit_client is None:
        _livekit_client = LiveKitClient()
    return _livekit_client
