"""Response model for streaming command responses.

This module defines the Response model which stores ordered response chunks
from vehicle command execution with sequence tracking.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.command import Command


class Response(Base):
    """Streaming command responses with sequence tracking.

    Stores ordered response chunks from vehicle command execution,
    enabling proper reassembly of streaming responses.

    Attributes:
        response_id: Primary key UUID identifier
        command_id: Foreign key to commands table (CASCADE on delete)
        response_payload: JSONB field for streaming response data chunks
        sequence_number: Sequence order for reassembling streaming responses
        is_final: Flag indicating the final response chunk in the stream
        received_at: Timestamp when response was received
        command: Related Command this response belongs to
    """

    __tablename__ = "responses"

    response_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    command_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("commands.command_id", ondelete="CASCADE"), nullable=False
    )
    response_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB(astext_type=Text()), nullable=False
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    command: Mapped["Command"] = relationship("Command", back_populates="responses")

    def __repr__(self) -> str:
        """Return string representation of Response."""
        return (
            f"<Response(response_id={self.response_id}, command_id={self.command_id}, "
            f"sequence_number={self.sequence_number}, is_final={self.is_final})>"
        )
