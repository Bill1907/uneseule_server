"""
Subscription model for payment plans.

Represents user subscription plans and payment information.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Subscription(Base, TimestampMixin):
    """
    Subscription model for user payment plans.

    A user has exactly one subscription (one-to-one relationship).
    Supports free, basic, and premium tiers with usage limits.
    """

    __tablename__ = "subscriptions"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique subscription identifier",
    )

    # Foreign key (unique - one subscription per user)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
        comment="Neon Auth user ID reference (one-to-one)",
    )

    # Subscription details
    plan_type = Column(
        String(20),
        nullable=False,
        comment="Subscription plan: free/basic/premium",
    )
    status = Column(
        String(20),
        nullable=False,
        comment="Subscription status: active/cancelled/expired/trial",
    )

    # Subscription timeline
    started_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Subscription start date",
    )
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Expiration date (null = lifetime/no expiry)",
    )

    # Payment information
    auto_renew = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Auto-renewal flag",
    )
    payment_method_id = Column(
        String(100),
        nullable=True,
        comment="Stripe/Toss payment method ID",
    )

    # Usage limits (flexible schema for different plan tiers)
    usage_limits = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Voice minutes, API calls, and other usage limits",
    )

    # Relationships
    user_profile = relationship(
        "UserProfile",
        back_populates="subscription",
    )

    # Constraints and indexes
    __table_args__ = (
        # Plan type must be one of the valid values
        CheckConstraint(
            "plan_type IN ('free', 'basic', 'premium')",
            name="chk_plan_type",
        ),
        # Status must be one of the valid values
        CheckConstraint(
            "status IN ('active', 'cancelled', 'expired', 'trial')",
            name="chk_status",
        ),
        # Expiration date must be after start date (if set)
        CheckConstraint(
            "expires_at IS NULL OR expires_at > started_at",
            name="chk_subscription_dates",
        ),
        # Composite index for subscription status queries
        Index(
            "idx_subscriptions_status",
            "status",
            "expires_at",
        ),
        # Index for plan type queries
        Index(
            "idx_subscriptions_plan",
            "plan_type",
        ),
        # Partial index for active subscriptions with expiry
        Index(
            "idx_subscriptions_expiry",
            "expires_at",
            postgresql_where=(expires_at.isnot(None)),
        ),
        {
            "comment": "User subscription plans with usage limits",
        },
    )

    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        if self.expires_at is None:
            return False  # No expiry date = lifetime subscription
        return datetime.now(timezone.utc) > self.expires_at

    def __repr__(self) -> str:
        return (
            f"<Subscription(id={self.id}, user_id={self.user_id}, "
            f"plan='{self.plan_type}', status='{self.status}')>"
        )
