"""
GraphQL queries for User, Child, and Subscription.
"""

from typing import Optional
from uuid import UUID

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from strawberry.types import Info

from app.graphql.context import GraphQLContext
from app.graphql.types.base import PlanType, SubscriptionStatus
from app.graphql.types.child import ChildType
from app.graphql.types.subscription import SubscriptionType
from app.graphql.types.user import UserType
from app.models.child import Child
from app.models.subscription import Subscription
from app.models.user_profile import UserProfile
from app.services.user_profile_service import UserProfileService


def _convert_profile_to_user_type(
    profile: UserProfile,
    email: str,
    name: Optional[str] = None,
) -> UserType:
    """Convert UserProfile to GraphQL UserType with Clerk data."""
    children = [_convert_child_to_type(child) for child in profile.children] if profile.children else []
    subscription = _convert_subscription_to_type(profile.subscription) if profile.subscription else None

    return UserType(
        id=str(profile.user_id),
        email=email,
        name=name,
        phone=profile.phone,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        children=children,
        subscription=subscription,
    )


def _convert_child_to_type(child: Child) -> ChildType:
    """Convert SQLAlchemy Child model to GraphQL ChildType."""
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


def _convert_subscription_to_type(sub: Subscription) -> SubscriptionType:
    """Convert SQLAlchemy Subscription model to GraphQL SubscriptionType."""
    return SubscriptionType(
        id=str(sub.id),
        plan_type=PlanType(sub.plan_type),
        status=SubscriptionStatus(sub.status),
        started_at=sub.started_at,
        expires_at=sub.expires_at,
        auto_renew=sub.auto_renew,
        is_expired=sub.is_expired,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


@strawberry.type
class UserQueries:
    """User-related GraphQL queries."""

    @strawberry.field
    async def me(self, info: Info[GraphQLContext, None]) -> Optional[UserType]:
        """Get current authenticated user information.

        Combines data from Clerk JWT (id, email, name) with
        user_profiles table (phone, children, subscription).
        """
        context = info.context
        if not context.user_id or not context.user_email:
            return None

        user_id = context.user_id

        # Get or create user profile (auto-creates on first login)
        service = UserProfileService(context.db)
        result = await service.get_or_create_profile(
            user_id=user_id,
            include_relations=True,
        )

        if not result.success or not result.profile:
            return None

        # Commit to persist auto-created profile
        await context.db.commit()

        return _convert_profile_to_user_type(
            profile=result.profile,
            email=context.user_email,
            name=context.user_name,
        )

    @strawberry.field
    async def my_children(self, info: Info[GraphQLContext, None]) -> list[ChildType]:
        """Get list of children for current user."""
        context = info.context
        if not context.user_id:
            return []

        query = (
            select(Child)
            .where(Child.user_id == context.user_id, Child.is_active == True)
            .options(selectinload(Child.device))
        )
        result = await context.db.execute(query)
        children = result.scalars().all()

        return [_convert_child_to_type(child) for child in children]

    @strawberry.field
    async def child(self, info: Info[GraphQLContext, None], id: str) -> Optional[ChildType]:
        """Get specific child by ID."""
        context = info.context
        if not context.user_id:
            return None

        query = (
            select(Child)
            .where(
                Child.id == UUID(id),
                Child.user_id == context.user_id,
            )
            .options(selectinload(Child.device))
        )
        result = await context.db.execute(query)
        child = result.scalar_one_or_none()

        if not child:
            return None

        return _convert_child_to_type(child)

    @strawberry.field
    async def my_subscription(self, info: Info[GraphQLContext, None]) -> Optional[SubscriptionType]:
        """Get subscription information for current user."""
        context = info.context
        if not context.user_id:
            return None

        query = select(Subscription).where(Subscription.user_id == context.user_id)
        result = await context.db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        return _convert_subscription_to_type(subscription)
