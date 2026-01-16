"""
Child service for business logic.
"""

import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.child import Child
from app.repositories.child_repository import ChildRepository
from app.repositories.user_profile_repository import UserProfileRepository

logger = logging.getLogger(__name__)


@dataclass
class ChildResult:
    """Child operation result."""

    success: bool
    child: Optional[Child] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class ChildService:
    """Service for child operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.child_repo = ChildRepository(db)
        self.profile_repo = UserProfileRepository(db)

    async def create_child(
        self,
        user_id: str,
        name: str,
        birth_date: date,
        gender: Optional[str] = None,
    ) -> ChildResult:
        """
        Create a new child for the user.

        Args:
            user_id: Parent user ID
            name: Child name
            birth_date: Child birth date
            gender: Optional gender

        Returns:
            ChildResult with child on success
        """
        # 1. Validate birth_date (not in future)
        if birth_date > date.today():
            return ChildResult(
                success=False,
                error_code="INVALID_BIRTH_DATE",
                error_message="Birth date cannot be in the future",
            )

        # 2. Ensure user_profile exists (auto-create if needed for FK constraint)
        await self.profile_repo.get_or_create(user_id)

        # 3. Create child
        child = await self.child_repo.create(
            user_id=user_id,
            name=name,
            birth_date=birth_date,
            gender=gender,
        )

        logger.info(f"Child created: {child.id} for user {user_id}")

        return ChildResult(success=True, child=child)

    async def update_child(
        self,
        user_id: str,
        child_id: UUID,
        name: Optional[str] = None,
        birth_date: Optional[date] = None,
        gender: Optional[str] = None,
    ) -> ChildResult:
        """
        Update child information.

        Args:
            user_id: Parent user ID (for ownership verification)
            child_id: Child ID to update
            name: New name (optional)
            birth_date: New birth date (optional)
            gender: New gender (optional)

        Returns:
            ChildResult with updated child on success
        """
        # 1. Get child with ownership verification
        child = await self.child_repo.get_by_id_and_user(child_id, user_id)
        if not child:
            return ChildResult(
                success=False,
                error_code="CHILD_NOT_FOUND",
                error_message="Child not found or not owned by user",
            )

        # 2. Validate birth_date if provided
        if birth_date and birth_date > date.today():
            return ChildResult(
                success=False,
                error_code="INVALID_BIRTH_DATE",
                error_message="Birth date cannot be in the future",
            )

        # 3. Update child
        child = await self.child_repo.update(
            child=child,
            name=name,
            birth_date=birth_date,
            gender=gender,
        )

        logger.info(f"Child updated: {child.id}")

        return ChildResult(success=True, child=child)

    async def delete_child(
        self,
        user_id: str,
        child_id: UUID,
    ) -> ChildResult:
        """
        Soft delete a child.

        Args:
            user_id: Parent user ID (for ownership verification)
            child_id: Child ID to delete

        Returns:
            ChildResult with success status
        """
        # 1. Get child with ownership verification
        child = await self.child_repo.get_by_id_and_user(child_id, user_id)
        if not child:
            return ChildResult(
                success=False,
                error_code="CHILD_NOT_FOUND",
                error_message="Child not found or not owned by user",
            )

        # 2. Soft delete
        child = await self.child_repo.soft_delete(child)

        logger.info(f"Child soft deleted: {child.id}")

        return ChildResult(success=True, child=child)
