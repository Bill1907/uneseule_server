"""
Base GraphQL types and utilities.
Common types used across the schema.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

import strawberry


@strawberry.type
class BaseNode:
    """
    Base type for entities with ID and timestamps.
    Inherit from this for common fields.
    """

    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


@strawberry.type
class PaginationInfo:
    """
    Pagination metadata for list queries.
    """

    has_next_page: bool
    has_previous_page: bool
    total_count: int
    page: int
    page_size: int


@strawberry.type
class ErrorDetail:
    """
    Error detail for validation or business logic errors.
    """

    field: Optional[str] = None
    message: str
    code: str


@strawberry.type
class SuccessResponse:
    """
    Generic success response.
    """

    success: bool
    message: str


@strawberry.type
class AuthPayload:
    """
    Authentication response with tokens and user.
    """

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


# Enums
@strawberry.enum
class ConnectionStatus(str, Enum):
    """Device connection status."""

    ONLINE = "online"
    OFFLINE = "offline"
    SLEEP = "sleep"


@strawberry.enum
class PlanType(str, Enum):
    """Subscription plan types."""

    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"


@strawberry.enum
class SubscriptionStatus(str, Enum):
    """Subscription status."""

    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"
