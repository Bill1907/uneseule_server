"""
Device repository for database operations.
"""

import secrets
from datetime import datetime, timezone
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
        device.last_seen = datetime.now(timezone.utc)
        device.connection_status = "online"
        await self.db.flush()

    async def exists_by_serial(self, serial_number: str) -> bool:
        """Check if device with serial number exists."""
        query = select(Device.id).where(Device.serial_number == serial_number)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None

    async def create(
        self,
        serial_number: str,
        device_type: str,
        firmware_version: str,
    ) -> tuple[Device, str]:
        """
        Create new device with generated secret.

        Returns:
            Tuple of (Device, plain_secret)
        """
        device_secret = secrets.token_urlsafe(32)

        device = Device(
            serial_number=serial_number,
            device_secret=device_secret,
            device_type=device_type,
            firmware_version=firmware_version,
            is_active=True,
            connection_status="offline",
        )

        self.db.add(device)
        await self.db.flush()
        await self.db.refresh(device)

        return device, device_secret

    async def pair_with_child(self, device: Device, child_id: UUID) -> Device:
        """Pair device with a child."""
        device.child_id = child_id
        device.paired_at = datetime.now(timezone.utc)
        await self.db.flush()

        # Re-fetch with child relationship loaded
        query = select(Device).where(Device.id == device.id).options(selectinload(Device.child))
        result = await self.db.execute(query)
        return result.scalar_one()

    async def unpair(self, device: Device) -> Device:
        """Unpair device from child."""
        device.child_id = None
        device.paired_at = None
        await self.db.flush()
        await self.db.refresh(device)
        return device

    async def get_by_child_id(self, child_id: UUID) -> Optional[Device]:
        """Get active device paired with child."""
        query = select(Device).where(
            Device.child_id == child_id,
            Device.is_active == True,
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
