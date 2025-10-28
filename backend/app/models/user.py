"""User model for authentication and RBAC.

This module defines the User model which stores user account information,
authentication credentials, and role-based access control (RBAC) data.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.command import Command
    from app.models.session import Session


class User(Base):
    """User account with authentication credentials and RBAC.

    Stores user authentication data with role-based access control.
    Supports two roles: 'engineer' (basic access) and 'admin' (full access).

    Attributes:
        user_id: Primary key UUID identifier
        username: Unique username (max 50 characters)
        email: Unique email address (max 255 characters)
        password_hash: Bcrypt-hashed password for secure authentication
        role: User role for RBAC ('engineer' or 'admin')
        created_at: Timestamp when user account was created
        updated_at: Timestamp when user account was last updated
        commands: Related Command records submitted by this user
        sessions: Related Session records for this user
        audit_logs: Related AuditLog records for actions by this user
    """

    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    commands: Mapped[list["Command"]] = relationship(
        "Command", back_populates="user", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", foreign_keys="AuditLog.user_id"
    )

    def __repr__(self) -> str:
        """Return string representation of User."""
        return f"<User(user_id={self.user_id}, username={self.username}, role={self.role})>"
