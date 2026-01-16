"""
GraphQL mutations for User operations.
"""

from uuid import UUID

import strawberry
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.queries.user import _convert_profile_to_user_type
from app.graphql.types.user import (
    UpdateMeInput,
    UpdateMePayload,
)
from app.services.user_profile_service import UserProfileService


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
            input: Profile update data (phone)

        Returns:
            UpdateMePayload with updated user or error
        """
        context = info.context

        # 1. Check authentication
        if not context.user_id or not context.user_email:
            return UpdateMePayload(
                success=False,
                error_code="UNAUTHORIZED",
                error_message="Authentication required",
            )

        # 2. Call service
        service = UserProfileService(context.db)
        result = await service.update_profile(
            user_id=context.user_id,
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
            user=_convert_profile_to_user_type(
                profile=result.profile,
                email=context.user_email,
                name=context.user_name,
            ),
        )
