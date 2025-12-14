"""
Device model for smart toy devices.

Represents physical smart toy devices that can be paired with children.
"""

import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Device(Base, TimestampMixin):
    """
    Device model for smart toy hardware.

    A device can be paired with one child at a time.
    Devices authenticate using HMAC-SHA256 signatures.
    """

    __tablename__ = "devices"

    # Primary key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique device identifier",
    )

    # Device identification
    serial_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Hardware serial number (unique identifier)",
    )
    device_secret = Column(
        String(255),
        nullable=False,
        comment="HMAC authentication secret (stored securely)",
    )

    # Foreign keys (nullable - device can exist without being paired)
    child_id = Column(
        UUID(as_uuid=True),
        ForeignKey("children.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Paired child reference (nullable when unpaired)",
    )

    # Device metadata
    device_type = Column(
        String(50),
        nullable=False,
        comment="Device model type",
    )
    firmware_version = Column(
        String(20),
        nullable=False,
        comment="Current firmware version",
    )

    # Device status
    battery_level = Column(
        Integer,
        nullable=True,
        comment="Current battery percentage (0-100)",
    )
    connection_status = Column(
        String(20),
        nullable=False,
        default="offline",
        comment="Connection status: online/offline/sleep",
    )
    last_seen = Column(
        DateTime,
        nullable=True,
        comment="Last connection timestamp",
    )

    # Status fields
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Device activation status",
    )
    paired_at = Column(
        DateTime,
        nullable=True,
        comment="When device was paired with current child",
    )

    # Relationships
    child = relationship(
        "Child",
        back_populates="device",
    )

    # Constraints and indexes
    __table_args__ = (
        # Battery level must be between 0 and 100
        CheckConstraint(
            "battery_level >= 0 AND battery_level <= 100",
            name="chk_battery_range",
        ),
        # Connection status must be one of the valid values
        CheckConstraint(
            "connection_status IN ('online', 'offline', 'sleep')",
            name="chk_connection_status",
        ),
        # Partial unique index: one child can have only ONE active device
        # This allows historical device records (is_active=False) while preventing
        # multiple active devices per child
        Index(
            "idx_devices_unique_child",
            "child_id",
            unique=True,
            postgresql_where=(child_id.isnot(None)) & (is_active == True),  # noqa: E712
        ),
        # Composite index for status queries
        Index(
            "idx_devices_status",
            "connection_status",
            "last_seen",
        ),
        # Partial index for low battery queries
        Index(
            "idx_devices_battery",
            "battery_level",
            postgresql_where=(battery_level < 20),
        ),
        {
            "comment": "Smart toy devices with HMAC authentication",
        },
    )

    def __repr__(self) -> str:
        return (
            f"<Device(id={self.id}, serial='{self.serial_number}', "
            f"status='{self.connection_status}')>"
        )
