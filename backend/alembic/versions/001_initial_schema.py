"""initial_schema

Creates all database tables, indexes, and constraints for the SOVD platform.
This migration establishes the complete database schema including:
- users: User accounts and authentication
- vehicles: Vehicle registry with connection tracking
- commands: SOVD command execution records
- responses: Streaming command responses
- sessions: User authentication sessions
- audit_logs: Comprehensive audit trail

Revision ID: 001
Revises:
Create Date: 2025-10-28 20:25:58.087510

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to create all tables and indexes."""
    # ========================================================================
    # Section 1: PostgreSQL Extensions
    # ========================================================================
    # Create pgcrypto extension for UUID generation
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ========================================================================
    # Section 2: Table Creation (in dependency order)
    # ========================================================================

    # ------------------------------------------------------------------------
    # Table: users
    # ------------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('engineer', 'admin')", name="users_role_check"),
    )

    # ------------------------------------------------------------------------
    # Table: vehicles
    # ------------------------------------------------------------------------
    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vin", sa.String(length=17), nullable=False, unique=True),
        sa.Column("make", sa.String(length=100), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("connection_status", sa.String(length=20), nullable=False),
        sa.Column("last_seen_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("connection_status IN ('connected', 'disconnected', 'error')", name="vehicles_connection_status_check"),
    )

    # ------------------------------------------------------------------------
    # Table: commands
    # ------------------------------------------------------------------------
    op.create_table(
        "commands",
        sa.Column("command_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("command_name", sa.String(length=100), nullable=False),
        sa.Column("command_params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'in_progress', 'completed', 'failed')", name="commands_status_check"),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------------
    # Table: responses
    # ------------------------------------------------------------------------
    op.create_table(
        "responses",
        sa.Column("response_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("command_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("response_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("is_final", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("received_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["command_id"], ["commands.command_id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------------
    # Table: sessions
    # ------------------------------------------------------------------------
    op.create_table(
        "sessions",
        sa.Column("session_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("refresh_token", sa.String(length=500), nullable=False, unique=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )

    # ------------------------------------------------------------------------
    # Table: audit_logs
    # ------------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("log_id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("vehicle_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("command_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'")),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.vehicle_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["command_id"], ["commands.command_id"], ondelete="SET NULL"),
    )

    # ========================================================================
    # Section 3: Index Creation (21+ indexes for performance)
    # ========================================================================

    # ------------------------------------------------------------------------
    # Indexes: users table (3 indexes)
    # ------------------------------------------------------------------------
    op.create_index("idx_users_username", "users", ["username"], unique=True)
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_role", "users", ["role"], unique=False)

    # ------------------------------------------------------------------------
    # Indexes: vehicles table (3 indexes)
    # ------------------------------------------------------------------------
    op.create_index("idx_vehicles_vin", "vehicles", ["vin"], unique=True)
    op.create_index("idx_vehicles_connection_status", "vehicles", ["connection_status"], unique=False)
    op.create_index("idx_vehicles_last_seen_at", "vehicles", ["last_seen_at"], unique=False)

    # ------------------------------------------------------------------------
    # Indexes: commands table (5 indexes)
    # ------------------------------------------------------------------------
    op.create_index("idx_commands_user_id", "commands", ["user_id"], unique=False)
    op.create_index("idx_commands_vehicle_id", "commands", ["vehicle_id"], unique=False)
    op.create_index("idx_commands_status", "commands", ["status"], unique=False)
    op.create_index("idx_commands_submitted_at", "commands", ["submitted_at"], unique=False)
    op.create_index("idx_commands_vehicle_id_status", "commands", ["vehicle_id", "status"], unique=False)

    # ------------------------------------------------------------------------
    # Indexes: responses table (2 indexes)
    # ------------------------------------------------------------------------
    op.create_index("idx_responses_command_id", "responses", ["command_id"], unique=False)
    op.create_index("idx_responses_command_id_sequence", "responses", ["command_id", "sequence_number"], unique=False)

    # ------------------------------------------------------------------------
    # Indexes: sessions table (3 indexes)
    # ------------------------------------------------------------------------
    op.create_index("idx_sessions_refresh_token", "sessions", ["refresh_token"], unique=True)
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index("idx_sessions_expires_at", "sessions", ["expires_at"], unique=False)

    # ------------------------------------------------------------------------
    # Indexes: audit_logs table (5 indexes)
    # ------------------------------------------------------------------------
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index("idx_audit_logs_vehicle_id", "audit_logs", ["vehicle_id"], unique=False)
    op.create_index("idx_audit_logs_command_id", "audit_logs", ["command_id"], unique=False)
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index("idx_audit_logs_timestamp", "audit_logs", ["timestamp"], unique=False)


def downgrade() -> None:
    """Downgrade schema by dropping all tables and indexes."""
    # Drop tables in reverse dependency order
    # Indexes will be automatically dropped with their tables
    op.drop_table("audit_logs")
    op.drop_table("sessions")
    op.drop_table("responses")
    op.drop_table("commands")
    op.drop_table("vehicles")
    op.drop_table("users")

    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
