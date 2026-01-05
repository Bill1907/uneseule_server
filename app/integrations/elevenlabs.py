"""
ElevenLabs Conversational AI integration client.

Handles signed URL generation for voice conversations.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class SignedUrlResponse:
    """ElevenLabs signed URL response."""

    signed_url: str
    conversation_id: Optional[str] = None


class ElevenLabsAPIError(Exception):
    """ElevenLabs API error."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"ElevenLabs API error: {status_code} - {detail}")


class ElevenLabsClient:
    """
    ElevenLabs API client for Conversational AI.

    Handles:
    - Signed URL generation for WebSocket connections
    - Error handling and retry logic
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        agent_id: Optional[str] = None,
    ):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.base_url = base_url or settings.ELEVENLABS_BASE_URL
        self.agent_id = agent_id or settings.ELEVENLABS_AGENT_ID

    async def get_signed_url(
        self,
        agent_id: Optional[str] = None,
        include_conversation_id: bool = True,
    ) -> SignedUrlResponse:
        """
        Get signed URL for Conversational AI WebSocket connection.

        Args:
            agent_id: Override default agent ID
            include_conversation_id: Include conversation ID in response

        Returns:
            SignedUrlResponse with signed_url and optional conversation_id

        Raises:
            ElevenLabsAPIError: If API call fails
        """
        target_agent_id = agent_id or self.agent_id

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/convai/conversation/get-signed-url",
                    headers={"xi-api-key": self.api_key},
                    params={
                        "agent_id": target_agent_id,
                        "include_conversation_id": str(include_conversation_id).lower(),
                    },
                    timeout=10.0,
                )

                if response.status_code != 200:
                    logger.error(
                        f"ElevenLabs API error: {response.status_code} - {response.text}"
                    )
                    raise ElevenLabsAPIError(
                        status_code=response.status_code,
                        detail=response.text,
                    )

                data = response.json()
                return SignedUrlResponse(
                    signed_url=data["signed_url"],
                    conversation_id=data.get("conversation_id"),
                )

            except httpx.TimeoutException as e:
                logger.error(f"ElevenLabs API timeout: {e}")
                raise ElevenLabsAPIError(
                    status_code=408,
                    detail="Request timeout",
                )
            except httpx.RequestError as e:
                logger.error(f"ElevenLabs API request error: {e}")
                raise ElevenLabsAPIError(
                    status_code=500,
                    detail=str(e),
                )


# Singleton instance (lazy initialization)
_elevenlabs_client: Optional[ElevenLabsClient] = None


def get_elevenlabs_client() -> ElevenLabsClient:
    """Get or create ElevenLabs client singleton."""
    global _elevenlabs_client
    if _elevenlabs_client is None:
        _elevenlabs_client = ElevenLabsClient()
    return _elevenlabs_client
