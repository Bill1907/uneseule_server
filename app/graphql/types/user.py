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
