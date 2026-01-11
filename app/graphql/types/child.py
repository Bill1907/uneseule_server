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
