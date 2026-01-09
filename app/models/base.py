"""
Base model class and mixins for SQLAlchemy ORM models.

This module provides:
- Base: Declarative base class for all ORM models
- TimestampMixin: Adds created_at and updated_at timestamps to models
"""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime
from sqlalchemy.orm import declarative_base

# Declarative base for all ORM models
Base = declarative_base()


def utc_now():
    """Return current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.

    Automatically sets:
    - created_at: Timestamp when the record is created (immutable)
    - updated_at: Timestamp when the record is last modified (auto-updated)
    """

    created_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        comment="Timestamp when the record was created",
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
        comment="Timestamp when the record was last updated",
    )
