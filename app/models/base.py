"""
Base model class and mixins for SQLAlchemy ORM models.

This module provides:
- Base: Declarative base class for all ORM models
- TimestampMixin: Adds created_at and updated_at timestamps to models
"""

from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Declarative base for all ORM models
Base = declarative_base()


class TimestampMixin:
    """
    Mixin to add created_at and updated_at timestamps to models.

    Automatically sets:
    - created_at: Timestamp when the record is created (immutable)
    - updated_at: Timestamp when the record is last modified (auto-updated)
    """

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the record was created",
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Timestamp when the record was last updated",
    )
