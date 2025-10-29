"""
Audit log repository module.

Provides async database access functions for audit log operations.
"""

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

logger = structlog.get_logger(__name__)


async def create_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    vehicle_id: uuid.UUID | None = None,
    command_id: uuid.UUID | None = None,
) -> AuditLog:
    """
    Create a new audit log entry in the database.

    Args:
        db: Async database session
        user_id: ID of user performing the action (nullable)
        action: Action type (e.g., "user_login", "command_submitted")
        entity_type: Type of entity being audited (e.g., "user", "command")
        entity_id: UUID of the entity being audited (nullable)
        details: Additional event-specific information (default: {})
        ip_address: Client IP address (nullable)
        user_agent: Client user agent string (nullable)
        vehicle_id: Related vehicle ID (nullable)
        command_id: Related command ID (nullable)

    Returns:
        Created AuditLog object
    """
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        vehicle_id=vehicle_id,
        command_id=command_id,
    )

    db.add(audit_log)
    await db.commit()
    await db.refresh(audit_log)

    logger.debug(
        "audit_log_created",
        log_id=str(audit_log.log_id),
        action=action,
        entity_type=entity_type,
        user_id=str(user_id) if user_id else None,
    )

    return audit_log
