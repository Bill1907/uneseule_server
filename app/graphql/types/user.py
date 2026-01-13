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
    """User (parent) account information."""

    id: str
    email: str
    name: str
    phone: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    children: list[Annotated["ChildType", strawberry.lazy("app.graphql.types.child")]]
    subscription: Optional[Annotated["SubscriptionType", strawberry.lazy("app.graphql.types.subscription")]] = None


# ===== Input Types =====


@strawberry.input
class UpdateMeInput:
    """Input for updating user profile."""

    name: Optional[str] = None
    phone: Optional[str] = None


@strawberry.input
class ChangePasswordInput:
    """Input for changing password."""

    current_password: str
    new_password: str


@strawberry.input
class DeactivateAccountInput:
    """Input for deactivating account."""

    password: str


# ===== Payload Types =====


@strawberry.type
class UpdateMePayload:
    """Payload for updateMe mutation."""

    success: bool
    user: Optional[UserType] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@strawberry.type
class ChangePasswordPayload:
    """Payload for changePassword mutation."""

    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@strawberry.type
class DeactivateAccountPayload:
    """Payload for deactivateAccount mutation."""

    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
