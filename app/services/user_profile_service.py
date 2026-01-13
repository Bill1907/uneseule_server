"""
UserProfile service for business logic.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_profile import UserProfile
from app.repositories.user_profile_repository import UserProfileRepository

logger = logging.getLogger(__name__)


@dataclass
class UserProfileResult:
    """UserProfile operation result."""

    success: bool
    profile: Optional[UserProfile] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class UserProfileService:
    """Service for user profile operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.profile_repo = UserProfileRepository(db)

    async def get_or_create_profile(
        self,
        user_id: UUID,
        include_relations: bool = False,
    ) -> UserProfileResult:
        """
        Get existing profile or create a new one.

        This is called on first login to auto-create the profile.

        Args:
            user_id: Neon Auth user ID (from JWT sub claim)
            include_relations: Include children and subscription

        Returns:
            UserProfileResult with profile
        """
        profile = await self.profile_repo.get_or_create(
            user_id=user_id,
            include_relations=include_relations,
        )

        logger.info(f"User profile retrieved/created: {user_id}")

        return UserProfileResult(success=True, profile=profile)

    async def update_profile(
        self,
        user_id: UUID,
        phone: Optional[str] = None,
    ) -> UserProfileResult:
        """
        Update user profile information.

        Args:
            user_id: Neon Auth user ID
            phone: New phone (optional)

        Returns:
            UserProfileResult with updated profile on success
        """
        # 1. Get profile
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            return UserProfileResult(
                success=False,
                error_code="PROFILE_NOT_FOUND",
                error_message="User profile not found",
            )

        # 2. Update profile
        profile = await self.profile_repo.update(
            profile=profile,
            phone=phone,
        )

        logger.info(f"User profile updated: {user_id}")

        return UserProfileResult(success=True, profile=profile)
