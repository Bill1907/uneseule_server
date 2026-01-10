"""
GraphQL types for Subscription operations.
"""

from datetime import datetime
from typing import Optional

import strawberry

from app.graphql.types.base import PlanType, SubscriptionStatus


@strawberry.type
class SubscriptionType:
    """Subscription information."""

    id: str
    plan_type: PlanType
    status: SubscriptionStatus
    started_at: datetime
    expires_at: Optional[datetime] = None
    auto_renew: bool
    is_expired: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
