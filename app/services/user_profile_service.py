"""
UserProfile service for business logic.
"""

import logging
from dataclasses import dataclass
from typing import Optional

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
        user_id: str,
        include_relations: bool = False,
    ) -> UserProfileResult:
        """
        Get existing profile or create a new one.

        This is called on first login to auto-create the profile.

        Args:
            user_id: Clerk user ID (from JWT sub claim, e.g., user_xxx)
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
        user_id: str,
        phone: Optional[str] = None,
    ) -> UserProfileResult:
        """
        Update user profile information.

        If profile doesn't exist, creates one first.

        Args:
            user_id: Clerk user ID (e.g., user_xxx)
            phone: New phone (optional)

        Returns:
            UserProfileResult with updated profile on success
        """
        # 1. Get or create profile
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            profile = await self.profile_repo.get_or_create(user_id=user_id)

        # 2. Update profile
        profile = await self.profile_repo.update(
            profile=profile,
            phone=phone,
        )

        logger.info(f"User profile updated: {user_id}")

        return UserProfileResult(success=True, profile=profile)
