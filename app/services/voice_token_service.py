"""
Voice token service for ElevenLabs Conversational AI.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.elevenlabs import (
    ElevenLabsAPIError,
    get_elevenlabs_client,
)
from app.models.device import Device
from app.models.subscription import Subscription
from app.repositories.device_repository import DeviceRepository
from app.schemas.device import ChildContext

logger = logging.getLogger(__name__)


# Rate limits by subscription plan
RATE_LIMITS = {
    "free": 50,
    "basic": 200,
    "premium": -1,  # unlimited
}


@dataclass
class TokenResult:
    """Voice token generation result."""

    success: bool
    signed_url: Optional[str] = None
    conversation_id: Optional[str] = None
    child_context: Optional[ChildContext] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class VoiceTokenService:
    """
    Service for generating ElevenLabs voice session tokens.

    Handles:
    - Device-child pairing validation
    - Subscription tier rate limiting
    - ElevenLabs signed URL generation
    - Child context preparation
    """

    def __init__(
        self,
        db: AsyncSession,
        redis: Optional[Redis] = None,
    ):
        self.db = db
        self.redis = redis
        self.device_repo = DeviceRepository(db)

    async def generate_token(self, device: Device) -> TokenResult:
        """
        Generate voice session token for device.

        Args:
            device: Authenticated device

        Returns:
            TokenResult with signed URL or error
        """
        # 1. Validate device-child pairing
        if not device.child_id:
            return TokenResult(
                success=False,
                error_code="DEVICE_NOT_PAIRED",
                error_message="Device is not paired with a child",
            )

        # 2. Get child with user (parent) relationship
        child = device.child
        if not child or not child.is_active:
            return TokenResult(
                success=False,
                error_code="CHILD_NOT_FOUND",
                error_message="Paired child not found or inactive",
            )

        # 3. Check subscription limits
        subscription = await self._get_subscription(child.user_id)
        if not subscription:
            return TokenResult(
                success=False,
                error_code="SUBSCRIPTION_NOT_FOUND",
                error_message="Parent subscription not found",
            )

        if not self._is_subscription_active(subscription):
            return TokenResult(
                success=False,
                error_code="SUBSCRIPTION_INACTIVE",
                error_message="Parent subscription is not active",
            )

        # 4. Check rate limits (Redis)
        if self.redis:
            is_allowed = await self._check_rate_limit(device, subscription)
            if not is_allowed:
                return TokenResult(
                    success=False,
                    error_code="RATE_LIMIT_EXCEEDED",
                    error_message="Daily API limit exceeded",
                )

        # 5. Get signed URL from ElevenLabs
        try:
            client = get_elevenlabs_client()
            url_response = await client.get_signed_url()
        except ElevenLabsAPIError as e:
            logger.error(f"ElevenLabs API error: {e}")
            return TokenResult(
                success=False,
                error_code="ELEVENLABS_ERROR",
                error_message="Failed to generate voice session",
            )

        # 6. Prepare child context
        personality_traits = child.personality_traits or {}
        child_context = ChildContext(
            child_id=str(child.id),
            child_name=child.name,
            child_age=child.age,
            personality_traits=personality_traits.get("traits", []),
        )

        # 7. Update device last_seen
        await self.device_repo.update_last_seen(device)

        # 8. Increment rate limit counter
        if self.redis:
            await self._increment_rate_limit(device)

        logger.info(
            f"Voice token generated for device {device.serial_number}, "
            f"child {child.name}"
        )

        return TokenResult(
            success=True,
            signed_url=url_response.signed_url,
            conversation_id=url_response.conversation_id,
            child_context=child_context,
        )

    async def _get_subscription(self, user_id) -> Optional[Subscription]:
        """Get subscription by user ID."""
        result = await self.db.execute(
            select(Subscription).where(Subscription.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _is_subscription_active(self, subscription: Subscription) -> bool:
        """Check if subscription is active."""
        return subscription.status == "active" and not subscription.is_expired

    def _get_daily_limit(self, subscription: Subscription) -> int:
        """Get daily API call limit for subscription plan."""
        return RATE_LIMITS.get(subscription.plan_type, 50)

    async def _check_rate_limit(
        self,
        device: Device,
        subscription: Subscription,
    ) -> bool:
        """Check if device is within rate limits."""
        daily_limit = self._get_daily_limit(subscription)
        if daily_limit == -1:  # unlimited
            return True

        key = f"rate_limit:device:{device.id}:daily"
        current = await self.redis.get(key)

        if current is None:
            return True

        return int(current) < daily_limit

    async def _increment_rate_limit(self, device: Device) -> None:
        """Increment rate limit counter."""
        key = f"rate_limit:device:{device.id}:daily"

        # Increment counter
        await self.redis.incr(key)

        # Set expiry at midnight UTC if not already set
        ttl = await self.redis.ttl(key)
        if ttl == -1:  # No expiry set
            now = datetime.now(timezone.utc)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            next_midnight = midnight + timedelta(days=1)
            seconds_until_midnight = int((next_midnight - now).total_seconds())
            await self.redis.expire(key, seconds_until_midnight)
