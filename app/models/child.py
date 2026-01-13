"""
Child model for child profiles.

Represents children associated with parent accounts.
"""

import uuid
from datetime import date

from sqlalchemy import Boolean, CheckConstraint, Column, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Child(Base, TimestampMixin):
    """
    Child model for child profiles.

    A child belongs to one user (parent) and can have one active device.
    Personality traits are analyzed from conversation data and stored as JSONB.
    """

    __tablename__ = "children"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique child identifier",
    )

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Neon Auth user ID reference",
    )

    # Profile fields
    name = Column(
        String(100),
        nullable=False,
        comment="Child's name (TODO: Add encryption at rest)",
    )
    birth_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Child's birthdate (TODO: Add encryption at rest)",
    )
    gender = Column(
        String(20),
        nullable=True,
        comment="Optional gender",
    )

    # AI-analyzed personality data
    personality_traits = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="AI-analyzed personality traits (flexible schema)",
    )

    # Status fields
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Profile active status (soft delete flag)",
    )

    # Relationships
    user_profile = relationship(
        "UserProfile",
        back_populates="children",
    )
    device = relationship(
        "Device",
        back_populates="child",
        uselist=False,  # One-to-one relationship
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager load device with child
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "birth_date <= CURRENT_DATE",
            name="chk_children_age",
        ),
        {
            "comment": "Child profiles with AI-analyzed personality data",
        },
    )

    @property
    def age(self) -> int:
        """Calculate child's current age in years."""
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    def __repr__(self) -> str:
        return f"<Child(id={self.id}, name='{self.name}', age={self.age})>"
