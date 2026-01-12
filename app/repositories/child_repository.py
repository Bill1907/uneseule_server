"""
Child repository for database operations.
"""

from datetime import date
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.child import Child


class ChildRepository:
    """Repository for Child database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: UUID,
        name: str,
        birth_date: date,
        gender: Optional[str] = None,
    ) -> Child:
        """
        Create new child.

        Args:
            user_id: Parent user ID
            name: Child name
            birth_date: Child birth date
            gender: Optional gender

        Returns:
            Created Child
        """
        child = Child(
            user_id=user_id,
            name=name,
            birth_date=birth_date,
            gender=gender,
            personality_traits={},
            is_active=True,
        )
        self.db.add(child)
        await self.db.flush()
        await self.db.refresh(child)
        return child

    async def get_by_id(
        self,
        child_id: UUID,
        include_device: bool = False,
    ) -> Optional[Child]:
        """
        Get child by ID.

        Args:
            child_id: Child UUID
            include_device: Include related device

        Returns:
            Child or None
        """
        query = select(Child).where(
            Child.id == child_id,
            Child.is_active == True,
        )
        if include_device:
            query = query.options(selectinload(Child.device))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_and_user(
        self,
        child_id: UUID,
        user_id: UUID,
        include_device: bool = False,
    ) -> Optional[Child]:
        """
        Get child by ID with ownership verification.

        Args:
            child_id: Child UUID
            user_id: Parent user UUID
            include_device: Include related device

        Returns:
            Child or None if not found or not owned
        """
        query = select(Child).where(
            Child.id == child_id,
            Child.user_id == user_id,
            Child.is_active == True,
        )
        if include_device:
            query = query.options(selectinload(Child.device))
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update(
        self,
        child: Child,
        name: Optional[str] = None,
        birth_date: Optional[date] = None,
        gender: Optional[str] = None,
    ) -> Child:
        """
        Update child fields.

        Args:
            child: Child to update
            name: New name (optional)
            birth_date: New birth date (optional)
            gender: New gender (optional)

        Returns:
            Updated Child
        """
        if name is not None:
            child.name = name
        if birth_date is not None:
            child.birth_date = birth_date
        if gender is not None:
            child.gender = gender
        await self.db.flush()
        await self.db.refresh(child)
        return child

    async def soft_delete(self, child: Child) -> Child:
        """
        Soft delete child (set is_active=False).

        Args:
            child: Child to delete

        Returns:
            Deleted Child
        """
        child.is_active = False
        await self.db.flush()
        await self.db.refresh(child)
        return child

    async def get_all_by_user(
        self,
        user_id: UUID,
        include_device: bool = False,
    ) -> list[Child]:
        """
        Get all active children for a user.

        Args:
            user_id: Parent user UUID
            include_device: Include related devices

        Returns:
            List of Children
        """
        query = select(Child).where(
            Child.user_id == user_id,
            Child.is_active == True,
        )
        if include_device:
            query = query.options(selectinload(Child.device))
        result = await self.db.execute(query)
        return list(result.scalars().all())
