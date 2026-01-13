"""
UserProfile model for extended user profile data.

Stores additional profile information for Neon Auth users.
The user_id references neon_auth.user.id (from JWT sub claim).
"""

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    """
    Extended profile data for Neon Auth users.

    This table stores additional profile fields that are not managed by Neon Auth.
    The user_id is the same as neon_auth.user.id (extracted from JWT sub claim).
    """

    __tablename__ = "user_profiles"

    # Primary key (same as neon_auth.user.id)
    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        comment="Neon Auth user ID (from JWT sub claim)",
    )

    # Profile fields
    phone = Column(
        String(20),
        nullable=True,
        comment="Optional phone number",
    )

    # Relationships
    children = relationship(
        "Child",
        back_populates="user_profile",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    subscription = relationship(
        "Subscription",
        back_populates="user_profile",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<UserProfile(user_id={self.user_id}, phone='{self.phone}')>"
