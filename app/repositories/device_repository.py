"""
Device repository for database operations.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.device import Device


class DeviceRepository:
    """Repository for Device database operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_serial_number(
        self,
        serial_number: str,
        include_child: bool = False,
    ) -> Optional[Device]:
        """
        Get device by serial number.

        Args:
            serial_number: Device serial number
            include_child: Include related child in query

        Returns:
            Device or None
        """
        query = select(Device).where(Device.serial_number == serial_number)

        if include_child:
            query = query.options(selectinload(Device.child))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(
        self,
        device_id: UUID,
        include_child: bool = False,
    ) -> Optional[Device]:
        """Get device by ID."""
        query = select(Device).where(Device.id == device_id)

        if include_child:
            query = query.options(selectinload(Device.child))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def update_last_seen(self, device: Device) -> None:
        """Update device last_seen timestamp and set status to online."""
        device.last_seen = datetime.utcnow()
        device.connection_status = "online"
        await self.db.flush()
