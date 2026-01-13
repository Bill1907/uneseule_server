"""
User repository for database operations.
"""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        user_id: UUID,
        include_relations: bool = False,
    ) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID
            include_relations: Include children and subscription

        Returns:
            User or None
        """
        query = select(User).where(
            User.id == user_id,
            User.is_active == True,
        )
        if include_relations:
            query = query.options(
                selectinload(User.children),
                selectinload(User.subscription),
            )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        user: User,
        name: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> User:
        """
        Update user profile fields.

        Args:
            user: User to update
            name: New name (optional)
            phone: New phone (optional)

        Returns:
            Updated User
        """
        if name is not None:
            user.name = name
        if phone is not None:
            user.phone = phone
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_password(
        self,
        user: User,
        password_hash: str,
    ) -> User:
        """
        Update user password hash.

        Args:
            user: User to update
            password_hash: New bcrypt hashed password

        Returns:
            Updated User
        """
        user.password_hash = password_hash
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def deactivate(self, user: User) -> User:
        """
        Deactivate user (set is_active=False).

        Args:
            user: User to deactivate

        Returns:
            Deactivated User
        """
        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)
        return user
