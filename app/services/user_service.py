"""
User service for business logic.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import SecurityUtils
from app.models.user import User
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


@dataclass
class UserResult:
    """User operation result."""

    success: bool
    user: Optional[User] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class UserService:
    """Service for user operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def update_profile(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> UserResult:
        """
        Update user profile information.

        Args:
            user_id: User ID
            name: New name (optional)
            phone: New phone (optional)

        Returns:
            UserResult with updated user on success
        """
        # 1. Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return UserResult(
                success=False,
                error_code="USER_NOT_FOUND",
                error_message="User not found",
            )

        # 2. Update user
        user = await self.user_repo.update(
            user=user,
            name=name,
            phone=phone,
        )

        logger.info(f"User profile updated: {user.id}")

        return UserResult(success=True, user=user)

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> UserResult:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            UserResult with success status
        """
        # 1. Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return UserResult(
                success=False,
                error_code="USER_NOT_FOUND",
                error_message="User not found",
            )

        # 2. Verify current password
        if not SecurityUtils.verify_password(current_password, user.password_hash):
            return UserResult(
                success=False,
                error_code="INVALID_CURRENT_PASSWORD",
                error_message="Current password is incorrect",
            )

        # 3. Check if new password is same as current
        if SecurityUtils.verify_password(new_password, user.password_hash):
            return UserResult(
                success=False,
                error_code="SAME_PASSWORD",
                error_message="New password must be different from current password",
            )

        # 4. Hash and update password
        new_hash = SecurityUtils.hash_password(new_password)
        user = await self.user_repo.update_password(user, new_hash)

        logger.info(f"User password changed: {user.id}")

        return UserResult(success=True, user=user)

    async def deactivate_account(
        self,
        user_id: UUID,
        password: str,
    ) -> UserResult:
        """
        Deactivate user account (soft delete).

        Args:
            user_id: User ID
            password: Password for confirmation

        Returns:
            UserResult with deactivated user on success
        """
        # 1. Get user
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return UserResult(
                success=False,
                error_code="USER_NOT_FOUND",
                error_message="User not found",
            )

        # 2. Verify password
        if not SecurityUtils.verify_password(password, user.password_hash):
            return UserResult(
                success=False,
                error_code="INVALID_PASSWORD",
                error_message="Password is incorrect",
            )

        # 3. Deactivate account
        user = await self.user_repo.deactivate(user)

        logger.info(f"User account deactivated: {user.id}")

        return UserResult(success=True, user=user)
