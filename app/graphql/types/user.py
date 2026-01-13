"""
GraphQL types for User operations.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry

if TYPE_CHECKING:
    from app.graphql.types.child import ChildType
    from app.graphql.types.subscription import SubscriptionType


@strawberry.type
class UserType:
    """User (parent) account information.

    Combines data from Neon Auth (id, email, name) and user_profiles (phone).
    """

    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    children: list[Annotated["ChildType", strawberry.lazy("app.graphql.types.child")]]
    subscription: Optional[Annotated["SubscriptionType", strawberry.lazy("app.graphql.types.subscription")]] = None


# ===== Input Types =====


@strawberry.input
class UpdateMeInput:
    """Input for updating user profile."""

    phone: Optional[str] = None


# ===== Payload Types =====


@strawberry.type
class UpdateMePayload:
    """Payload for updateMe mutation."""

    success: bool
    user: Optional[UserType] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
