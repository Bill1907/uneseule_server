"""
GraphQL queries for Device.
"""

from typing import Optional
from uuid import UUID

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.types.base import ConnectionStatus
from app.graphql.types.device import DeviceType
from app.models.child import Child
from app.models.device import Device


def _convert_device_to_type(device: Device) -> DeviceType:
    """Convert SQLAlchemy Device model to GraphQL DeviceType."""
    child_name = None
    if device.child:
        child_name = device.child.name

    return DeviceType(
        id=str(device.id),
        serial_number=device.serial_number,
        device_type=device.device_type,
        firmware_version=device.firmware_version,
        battery_level=device.battery_level,
        connection_status=ConnectionStatus(device.connection_status),
        is_active=device.is_active,
        paired_at=device.paired_at,
        child_id=str(device.child_id) if device.child_id else None,
        child_name=child_name,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@strawberry.type
class DeviceQueries:
    """Device-related GraphQL queries."""

    @strawberry.field
    async def my_devices(self, info: Info[GraphQLContext, None]) -> list[DeviceType]:
        """Get all devices for current user's children."""
        context = info.context
        if not context.user_id:
            return []

        # Get all devices linked to user's children
        query = (
            select(Device)
            .join(Child, Device.child_id == Child.id)
            .where(Child.user_id == context.user_id, Device.is_active == True)
            .options(selectinload(Device.child))
        )
        result = await context.db.execute(query)
        devices = result.scalars().all()

        return [_convert_device_to_type(device) for device in devices]

    @strawberry.field
    async def device(self, info: Info[GraphQLContext, None], id: str) -> Optional[DeviceType]:
        """Get specific device by ID."""
        context = info.context
        if not context.user_id:
            return None

        # Verify device belongs to user's child
        query = (
            select(Device)
            .join(Child, Device.child_id == Child.id)
            .where(
                Device.id == UUID(id),
                Child.user_id == context.user_id,
            )
            .options(selectinload(Device.child))
        )
        result = await context.db.execute(query)
        device = result.scalar_one_or_none()

        if not device:
            return None

        return _convert_device_to_type(device)
