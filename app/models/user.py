"""
User model for parent accounts.

Represents parent/guardian accounts that manage children and devices.
"""

import uuid

from sqlalchemy import Boolean, Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User model for parent/guardian accounts.

    A user can have multiple children and one subscription.
    """

    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier",
    )

    # Authentication fields
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique, used for login)",
    )
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )

    # Profile fields
    name = Column(
        String(100),
        nullable=False,
        comment="Parent's full name",
    )
    phone = Column(
        String(20),
        nullable=True,
        comment="Optional phone number",
    )

    # Status fields
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Account active status (soft delete flag)",
    )
    email_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email verification status",
    )

    # Relationships
    children = relationship(
        "Child",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager load children with user
    )
    subscription = relationship(
        "Subscription",
        back_populates="user",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager load subscription with user
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.name}')>"
