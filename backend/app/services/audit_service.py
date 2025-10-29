"""
Audit service module.

Provides functions for logging security-relevant events and user actions
to the audit_logs table with comprehensive error handling.
"""

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import audit_repository

logger = structlog.get_logger(__name__)


async def log_audit_event(
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    details: dict[str, Any] | None,
    ip_address: str | None,
    user_agent: str | None,
    db_session: AsyncSession,
    vehicle_id: uuid.UUID | None = None,
    command_id: uuid.UUID | None = None,
) -> bool:
    """
    Log an audit event to the database.

    This function wraps audit log creation in try-except to ensure that
    audit logging failures never break the application flow. All audit
    logging operations should use this function.

    Args:
        user_id: ID of user performing the action (nullable)
        action: Action type (e.g., "user_login", "command_submitted")
        entity_type: Type of entity being audited (e.g., "user", "command")
        entity_id: UUID of the entity being audited (nullable)
        details: Additional event-specific information (nullable)
        ip_address: Client IP address (nullable)
        user_agent: Client user agent string (nullable)
        db_session: Database session
        vehicle_id: Related vehicle ID (nullable)
        command_id: Related command ID (nullable)

    Returns:
        True if audit log was successfully created, False if an error occurred
    """
    try:
        await audit_repository.create_audit_log(
            db=db_session,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            vehicle_id=vehicle_id,
            command_id=command_id,
        )

        logger.info(
            "audit_event_logged",
            action=action,
            entity_type=entity_type,
            user_id=str(user_id) if user_id else None,
        )

        return True

    except Exception as e:
        # Never let audit logging failures break the application
        logger.error(
            "audit_event_logging_failed",
            action=action,
            entity_type=entity_type,
            error=str(e),
            exc_info=True,
        )
        return False
