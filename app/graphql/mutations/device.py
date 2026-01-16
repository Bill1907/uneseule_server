"""
GraphQL mutations for Device operations.
"""

from uuid import UUID

import strawberry
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.types.base import ConnectionStatus
from app.graphql.types.device import (
    DeviceType,
    RegisterDeviceInput,
    RegisterDevicePayload,
    UnpairDevicePayload,
)
from app.services.device_service import DeviceService


def _device_to_graphql(device) -> DeviceType:
    """Convert Device model to GraphQL type."""
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
        child_name=device.child.name if device.child else None,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


@strawberry.type
class DeviceMutations:
    """Device-related mutations."""

    @strawberry.mutation
    async def register_device(
        self, info: Info[GraphQLContext, None], input: RegisterDeviceInput
    ) -> RegisterDevicePayload:
        """
        Register a new device and pair it with a child.

        Requires JWT authentication.
        Called from parent app after BLE connection.

        Args:
            input: Device registration data from BLE

        Returns:
            RegisterDevicePayload with device info or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return RegisterDevicePayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = DeviceService(context.db)
        result = await service.register_and_pair(
            user_id=context.user_id,
            serial_number=input.serial_number,
            device_secret=input.device_secret,
            device_type=input.device_type,
            firmware_version=input.firmware_version,
            child_id=UUID(input.child_id),
        )

        if not result.success:
            return RegisterDevicePayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # Commit transaction
        await context.db.commit()

        return RegisterDevicePayload(
            success=True,
            device=_device_to_graphql(result.device),
        )

    @strawberry.mutation
    async def unpair_device(
        self, info: Info[GraphQLContext, None], device_id: str
    ) -> UnpairDevicePayload:
        """
        Unpair a device from its child.

        Requires JWT authentication.

        Args:
            device_id: Device ID to unpair

        Returns:
            UnpairDevicePayload with success status
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return UnpairDevicePayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = DeviceService(context.db)
        result = await service.unpair_by_id(
            user_id=context.user_id,
            device_id=UUID(device_id),
        )

        if not result.success:
            return UnpairDevicePayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # Commit transaction
        await context.db.commit()

        return UnpairDevicePayload(success=True)
