"""Command model for SOVD command execution tracking.

This module defines the Command model which tracks SOVD commands submitted by
users to vehicles with complete lifecycle status tracking.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.response import Response
    from app.models.user import User
    from app.models.vehicle import Vehicle


class Command(Base):
    """SOVD command execution records with status tracking.

    Tracks all commands submitted by users to vehicles, including command
    parameters, execution status, and error information.

    Attributes:
        command_id: Primary key UUID identifier
        user_id: Foreign key to users table (CASCADE on delete)
        vehicle_id: Foreign key to vehicles table (CASCADE on delete)
        command_name: SOVD command identifier (e.g., "read_dtc", "clear_dtc")
        command_params: JSONB field for command-specific parameters
        status: Command execution lifecycle status ('pending', 'in_progress', 'completed', 'failed')
        error_message: Optional error message if command failed
        submitted_at: Timestamp when command was submitted
        completed_at: Timestamp when command was completed (nullable)
        user: Related User who submitted the command
        vehicle: Related Vehicle the command was sent to
        responses: Related Response records for this command
        audit_logs: Related AuditLog records for this command
    """

    __tablename__ = "commands"

    command_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vehicles.vehicle_id", ondelete="CASCADE"), nullable=False
    )
    command_name: Mapped[str] = mapped_column(String(100), nullable=False)
    command_params: Mapped[dict[str, Any]] = mapped_column(
        JSONB(astext_type=Text()), nullable=False, server_default=text("'{}'")
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default=text("'pending'")
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()")
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="commands")
    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="commands")
    responses: Mapped[list["Response"]] = relationship(
        "Response", back_populates="command", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="command", foreign_keys="AuditLog.command_id"
    )

    def __repr__(self) -> str:
        """Return string representation of Command."""
        return (
            f"<Command(command_id={self.command_id}, command_name={self.command_name}, "
            f"status={self.status}, user_id={self.user_id}, vehicle_id={self.vehicle_id})>"
        )
