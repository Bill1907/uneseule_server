"""
UserProfile model for extended user profile data.

Stores additional profile information for Clerk users.
The user_id is the Clerk user ID (from JWT sub claim, e.g., user_xxx).
"""

from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class UserProfile(Base, TimestampMixin):
    """
    Extended profile data for Clerk users.

    This table stores additional profile fields that are not managed by Clerk.
    The user_id is the same as Clerk user ID (extracted from JWT sub claim).
    """

    __tablename__ = "user_profiles"

    # Primary key (Clerk user ID, e.g., user_xxx)
    user_id = Column(
        String(255),
        primary_key=True,
        comment="Clerk user ID (from JWT sub claim, e.g., user_xxx)",
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
