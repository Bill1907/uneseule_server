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
from app.models.user import User


def _convert_user_to_type(user: User) -> UserType:
    """Convert SQLAlchemy User model to GraphQL UserType."""
    children = [_convert_child_to_type(child) for child in user.children] if user.children else []
    subscription = _convert_subscription_to_type(user.subscription) if user.subscription else None

    return UserType(
        id=str(user.id),
        email=user.email,
        name=user.name,
        phone=user.phone,
        is_active=user.is_active,
        email_verified=user.email_verified,
        created_at=user.created_at,
        updated_at=user.updated_at,
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
        """Get current authenticated user information."""
        context = info.context
        if not context.user_id:
            return None

        query = (
            select(User)
            .where(User.id == UUID(context.user_id))
            .options(
                selectinload(User.children).selectinload(Child.device),
                selectinload(User.subscription),
            )
        )
        result = await context.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return _convert_user_to_type(user)

    @strawberry.field
    async def my_children(self, info: Info[GraphQLContext, None]) -> list[ChildType]:
        """Get list of children for current user."""
        context = info.context
        if not context.user_id:
            return []

        query = (
            select(Child)
            .where(Child.user_id == UUID(context.user_id), Child.is_active == True)
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
                Child.user_id == UUID(context.user_id),
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

        query = select(Subscription).where(Subscription.user_id == UUID(context.user_id))
        result = await context.db.execute(query)
        subscription = result.scalar_one_or_none()

        if not subscription:
            return None

        return _convert_subscription_to_type(subscription)
