"""Session model for user authentication sessions.

This module defines the Session model which manages user session lifecycle
and JWT refresh token storage for authentication.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Session(Base):
    """User authentication sessions with JWT refresh token storage.

    Manages user session lifecycle and refresh token rotation for
    secure authentication.

    Attributes:
        session_id: Primary key UUID identifier
        user_id: Foreign key to users table (CASCADE on delete)
        refresh_token: Unique JWT refresh token for session renewal (max 500 characters)
        expires_at: Token expiration timestamp for cleanup and security
        created_at: Timestamp when session was created
        user: Related User this session belongs to
    """

    __tablename__ = "sessions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )
    refresh_token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        """Return string representation of Session."""
        return (
            f"<Session(session_id={self.session_id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at})>"
        )
