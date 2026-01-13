"""
GraphQL mutations for User operations.
"""

from uuid import UUID

import strawberry
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.queries.user import _convert_user_to_type
from app.graphql.types.user import (
    ChangePasswordInput,
    ChangePasswordPayload,
    DeactivateAccountInput,
    DeactivateAccountPayload,
    UpdateMeInput,
    UpdateMePayload,
)
from app.services.user_service import UserService


@strawberry.type
class UserMutations:
    """User-related mutations."""

    @strawberry.mutation
    async def update_me(
        self, info: Info[GraphQLContext, None], input: UpdateMeInput
    ) -> UpdateMePayload:
        """
        Update current user's profile.

        Requires JWT authentication.

        Args:
            input: Profile update data (name, phone)

        Returns:
            UpdateMePayload with updated user or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return UpdateMePayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = UserService(context.db)
        result = await service.update_profile(
            user_id=UUID(context.user_id),
            name=input.name,
            phone=input.phone,
        )

        if not result.success:
            return UpdateMePayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # 3. Commit transaction
        await context.db.commit()

        return UpdateMePayload(
            success=True,
            user=_convert_user_to_type(result.user),
        )

    @strawberry.mutation
    async def change_password(
        self, info: Info[GraphQLContext, None], input: ChangePasswordInput
    ) -> ChangePasswordPayload:
        """
        Change current user's password.

        Requires JWT authentication and current password verification.

        Args:
            input: Password change data (current_password, new_password)

        Returns:
            ChangePasswordPayload with success status or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return ChangePasswordPayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = UserService(context.db)
        result = await service.change_password(
            user_id=UUID(context.user_id),
            current_password=input.current_password,
            new_password=input.new_password,
        )

        if not result.success:
            return ChangePasswordPayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # 3. Commit transaction
        await context.db.commit()

        return ChangePasswordPayload(success=True)

    @strawberry.mutation
    async def deactivate_account(
        self, info: Info[GraphQLContext, None], input: DeactivateAccountInput
    ) -> DeactivateAccountPayload:
        """
        Deactivate current user's account (soft delete).

        Requires JWT authentication and password confirmation.

        Args:
            input: Account deactivation data (password for confirmation)

        Returns:
            DeactivateAccountPayload with success status or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id:
            return DeactivateAccountPayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = UserService(context.db)
        result = await service.deactivate_account(
            user_id=UUID(context.user_id),
            password=input.password,
        )

        if not result.success:
            return DeactivateAccountPayload(
                success=False,
                error_code=result.error_code,
                error_message=result.error_message,
            )

        # 3. Commit transaction
        await context.db.commit()

        return DeactivateAccountPayload(success=True)
