"""
GraphQL types for Child operations.
"""

from datetime import date, datetime
from typing import TYPE_CHECKING, Annotated, Optional

import strawberry

if TYPE_CHECKING:
    from app.graphql.types.device import DeviceType


@strawberry.type
class ChildType:
    """Child profile information."""

    id: str
    name: str
    birth_date: date
    gender: Optional[str] = None
    age: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    device: Optional[Annotated["DeviceType", strawberry.lazy("app.graphql.types.device")]] = None


# ===== Input Types =====


@strawberry.input
class CreateChildInput:
    """Input for creating a child."""

    name: str
    birth_date: date
    gender: Optional[str] = None


@strawberry.input
class UpdateChildInput:
    """Input for updating a child."""

    name: Optional[str] = None
    birth_date: Optional[date] = None
    gender: Optional[str] = None


# ===== Payload Types =====


@strawberry.type
class CreateChildPayload:
    """Response for child creation."""

    success: bool
    child: Optional[ChildType] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@strawberry.type
class UpdateChildPayload:
    """Response for child update."""

    success: bool
    child: Optional[ChildType] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


@strawberry.type
class DeleteChildPayload:
    """Response for child deletion."""

    success: bool
    error_code: Optional[str] = None
    error_message: Optional[str] = None
