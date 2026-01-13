"""
UserProfile repository for database operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user_profile import UserProfile


class UserProfileRepository:
    """Repository for UserProfile database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(
        self,
        user_id: UUID,
        include_relations: bool = False,
    ) -> Optional[UserProfile]:
        """
        Get user profile by Neon Auth user ID.

        Args:
            user_id: Neon Auth user UUID (from JWT sub claim)
            include_relations: Include children and subscription

        Returns:
            UserProfile or None
        """
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        if include_relations:
            query = query.options(
                selectinload(UserProfile.children),
                selectinload(UserProfile.subscription),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        user_id: UUID,
        include_relations: bool = False,
    ) -> UserProfile:
        """
        Get existing profile or create a new one.

        This is used on first login to auto-create the profile.

        Args:
            user_id: Neon Auth user UUID (from JWT sub claim)
            include_relations: Include children and subscription

        Returns:
            UserProfile (existing or newly created)
        """
        profile = await self.get_by_user_id(user_id, include_relations)
        if profile is None:
            profile = UserProfile(user_id=user_id)
            self.db.add(profile)
            await self.db.flush()
            await self.db.refresh(profile)
        return profile

    async def update(
        self,
        profile: UserProfile,
        phone: Optional[str] = None,
    ) -> UserProfile:
        """
        Update user profile fields.

        Args:
            profile: UserProfile to update
            phone: New phone (optional)

        Returns:
            Updated UserProfile
        """
        if phone is not None:
            profile.phone = phone
        await self.db.flush()
        await self.db.refresh(profile)
        return profile
