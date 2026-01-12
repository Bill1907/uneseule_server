"""
GraphQL mutations for Child operations.
"""

from uuid import UUID

import strawberry
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.types.child import (
    ChildType,
    CreateChildInput,
    CreateChildPayload,
    UpdateChildInput,
    UpdateChildPayload,
    DeleteChildPayload,
)
from app.services.child_service import ChildService


def _child_to_graphql(child) -> ChildType:
    """Convert Child model to GraphQL type."""
    from app.graphql.types.base import ConnectionStatus
    from app.graphql.types.device import DeviceType

    device = None
    if child.device:
        device = DeviceType(
            id=str(child.device.id),
            serial_number=child.device.serial_number,
            device_type=child.device.device_type,
            firmware_version=child.device.firmware_version,
            battery_level=child.device.battery_level,
            connection_status=ConnectionStatus(child.device.connection_status),
            is_active=child.device.is_active,
            paired_at=child.device.paired_at,
            child_id=str(child.device.child_id) if child.device.child_id else None,
            child_name=child.name,
            created_at=child.device.created_at,
            updated_at=child.device.updated_at,
        )

    return ChildType(
        id=str(child.id),
        name=child.name,
        birth_date=child.birth_date,
        gender=child.gender,
        age=child.age,
        is_active=child.is_active,
        created_at=child.created_at,
        updated_at=child.updated_at,
        device=device,
    )


@strawberry.type
class ChildMutations:
    """Child-related mutations."""

    @strawberry.mutation
    async def create_child(
        self, info: Info[GraphQLContext, None], input: CreateChildInput
    ) -> CreateChildPayload:
        """
        Create a new child profile.

        Requires JWT authentication.

        Args:
            input: Child creation data

        Returns:
            CreateChildPayload with child or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return CreateChildPayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = ChildService(context.db)
        result = await service.create_child(
            user_id=UUID(context.user_id),
            name=input.name,
            birth_date=input.birth_date,
            gender=input.gender,
        )

        if not result.success:
            return CreateChildPayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # 3. Commit transaction
        await context.db.commit()

        return CreateChildPayload(
            success=True,
            child=_child_to_graphql(result.child),
        )

    @strawberry.mutation
    async def update_child(
        self, info: Info[GraphQLContext, None], child_id: str, input: UpdateChildInput
    ) -> UpdateChildPayload:
        """
        Update a child profile.

        Requires JWT authentication and ownership.

        Args:
            child_id: Child ID to update
            input: Fields to update

        Returns:
            UpdateChildPayload with updated child or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return UpdateChildPayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = ChildService(context.db)
        result = await service.update_child(
            user_id=UUID(context.user_id),
            child_id=UUID(child_id),
            name=input.name,
            birth_date=input.birth_date,
            gender=input.gender,
        )

        if not result.success:
            return UpdateChildPayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # 3. Commit transaction
        await context.db.commit()

        return UpdateChildPayload(
            success=True,
            child=_child_to_graphql(result.child),
        )

    @strawberry.mutation
    async def delete_child(
        self, info: Info[GraphQLContext, None], child_id: str
    ) -> DeleteChildPayload:
        """
        Delete a child profile (soft delete).

        Requires JWT authentication and ownership.

        Args:
            child_id: Child ID to delete

        Returns:
            DeleteChildPayload with success status
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return DeleteChildPayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = ChildService(context.db)
        result = await service.delete_child(
            user_id=UUID(context.user_id),
            child_id=UUID(child_id),
        )

        if not result.success:
            return DeleteChildPayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # 3. Commit transaction
        await context.db.commit()

        return DeleteChildPayload(success=True)
