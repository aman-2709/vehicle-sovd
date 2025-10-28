"""AuditLog model for comprehensive audit trail.

This module defines the AuditLog model which records all user actions,
system events, and security-relevant operations with complete audit trail
preservation even when related entities are deleted.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.command import Command
    from app.models.user import User
    from app.models.vehicle import Vehicle


class AuditLog(Base):
    """Comprehensive audit trail of all system events.

    Records all user actions, system events, and security-relevant operations.
    Preserves audit trail even when related entities are deleted by using
    SET NULL foreign key behavior.

    Attributes:
        log_id: Primary key UUID identifier
        user_id: Foreign key to users table (SET NULL on delete, nullable)
        vehicle_id: Foreign key to vehicles table (SET NULL on delete, nullable)
        command_id: Foreign key to commands table (SET NULL on delete, nullable)
        action: Action type (e.g., "user.login", "command.submit", "vehicle.connect")
        entity_type: Type of entity being audited (e.g., "user", "command", "vehicle")
        entity_id: UUID of the entity being audited (nullable)
        details: JSONB field for event-specific information
        ip_address: Client IP address (supports IPv4 and IPv6, max 45 characters)
        user_agent: Client user agent string (nullable)
        timestamp: Timestamp when event occurred
        user: Related User (if action was performed by a user)
        vehicle: Related Vehicle (if action involves a vehicle)
        command: Related Command (if action involves a command)
    """

    __tablename__ = "audit_logs"

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True
    )
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.vehicle_id", ondelete="SET NULL"), nullable=True
    )
    command_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commands.command_id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[dict[str, Any]] = mapped_column(
        JSONB(astext_type=Text()), server_default=text("'{}'")
    )
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="audit_logs", foreign_keys=[user_id]
    )
    vehicle: Mapped[Optional["Vehicle"]] = relationship(
        "Vehicle", back_populates="audit_logs", foreign_keys=[vehicle_id]
    )
    command: Mapped[Optional["Command"]] = relationship(
        "Command", back_populates="audit_logs", foreign_keys=[command_id]
    )

    def __repr__(self) -> str:
        """Return string representation of AuditLog."""
        return (
            f"<AuditLog(log_id={self.log_id}, action={self.action}, "
            f"entity_type={self.entity_type}, timestamp={self.timestamp})>"
        )
