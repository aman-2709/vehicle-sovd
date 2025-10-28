"""Vehicle model for connected vehicle registry.

This module defines the Vehicle model which stores vehicle information,
real-time connection status, and flexible metadata for vehicle-specific attributes.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.command import Command


class Vehicle(Base):
    """Connected vehicle registry with real-time connection tracking.

    Tracks all vehicles registered in the SOVD platform with connection status
    and flexible metadata storage for vehicle-specific attributes.

    Attributes:
        vehicle_id: Primary key UUID identifier
        vin: Unique Vehicle Identification Number (17 characters, ISO 3779 standard)
        make: Vehicle manufacturer name (max 100 characters)
        model: Vehicle model name (max 100 characters)
        year: Vehicle manufacturing year
        connection_status: Real-time connection status ('connected', 'disconnected', 'error')
        last_seen_at: Timestamp when vehicle was last seen (nullable)
        vehicle_metadata: JSONB field for flexible vehicle-specific attributes
            (maps to 'metadata' column)
        created_at: Timestamp when vehicle was registered
        commands: Related Command records sent to this vehicle
        audit_logs: Related AuditLog records for actions involving this vehicle
    """

    __tablename__ = "vehicles"

    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    vin: Mapped[str] = mapped_column(String(17), unique=True, nullable=False)
    make: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    connection_status: Mapped[str] = mapped_column(String(20), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    vehicle_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB(astext_type=Text()), server_default=text("'{}'")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )

    # Relationships
    commands: Mapped[list["Command"]] = relationship(
        "Command", back_populates="vehicle", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="vehicle", foreign_keys="AuditLog.vehicle_id"
    )

    def __repr__(self) -> str:
        """Return string representation of Vehicle."""
        return (
            f"<Vehicle(vehicle_id={self.vehicle_id}, vin={self.vin}, "
            f"make={self.make}, model={self.model}, status={self.connection_status})>"
        )
