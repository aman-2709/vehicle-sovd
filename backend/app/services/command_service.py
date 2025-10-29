"""
Business logic for command management operations.
"""

import uuid
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.command import Command
from app.repositories import command_repository, vehicle_repository

logger = structlog.get_logger(__name__)


async def submit_command(
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
    user_id: uuid.UUID,
    db_session: AsyncSession,
) -> Command | None:
    """
    Submit a command to a vehicle.

    Validates vehicle existence, creates command record, and marks as in_progress.
    Actual vehicle communication is stubbed for now (will be implemented in I2.T5).

    Args:
        vehicle_id: Target vehicle UUID
        command_name: SOVD command identifier
        command_params: Command-specific parameters
        user_id: ID of user submitting the command
        db_session: Database session

    Returns:
        Created Command object if vehicle exists, None otherwise
    """
    logger.info(
        "command_submission_started",
        vehicle_id=str(vehicle_id),
        command_name=command_name,
        user_id=str(user_id),
    )

    # Validate vehicle exists
    vehicle = await vehicle_repository.get_vehicle_by_id(db_session, vehicle_id)
    if vehicle is None:
        logger.warning(
            "command_submission_failed_vehicle_not_found",
            vehicle_id=str(vehicle_id),
            user_id=str(user_id),
        )
        return None

    # Create command with status='pending' (default)
    command = await command_repository.create_command(
        db=db_session,
        user_id=user_id,
        vehicle_id=vehicle_id,
        command_name=command_name,
        command_params=command_params,
    )

    logger.info(
        "command_created",
        command_id=str(command.command_id),
        status=command.status,
    )

    # Update status to 'in_progress' (stub for vehicle connector)
    updated_command = await command_repository.update_command_status(
        db=db_session, command_id=command.command_id, status="in_progress"
    )

    # This should never be None since we just created the command
    assert updated_command is not None, "Failed to update command status"

    logger.info(
        "command_submitted",
        command_id=str(updated_command.command_id),
        status=updated_command.status,
        vehicle_id=str(vehicle_id),
        user_id=str(user_id),
    )

    return updated_command


async def get_command_by_id(
    command_id: uuid.UUID, db_session: AsyncSession
) -> Command | None:
    """
    Retrieve a command by its ID.

    Args:
        command_id: Command UUID
        db_session: Database session

    Returns:
        Command object if found, None otherwise
    """
    logger.info("command_retrieval", command_id=str(command_id))
    command = await command_repository.get_command_by_id(db_session, command_id)

    if command:
        logger.info("command_found", command_id=str(command_id))
    else:
        logger.warning("command_not_found", command_id=str(command_id))

    return command


async def get_command_history(
    filters: dict[str, Any], db_session: AsyncSession
) -> list[Command]:
    """
    Retrieve command history with filtering and pagination.

    Args:
        filters: Dictionary containing optional filters:
            - vehicle_id: Filter by vehicle UUID
            - user_id: Filter by user UUID
            - status: Filter by command status
            - limit: Maximum number of records (default 50)
            - offset: Number of records to skip (default 0)
        db_session: Database session

    Returns:
        List of Command objects
    """
    logger.info("command_history_retrieval", filters=filters)

    commands = await command_repository.get_commands(
        db=db_session,
        vehicle_id=filters.get("vehicle_id"),
        user_id=filters.get("user_id"),
        status=filters.get("status"),
        limit=filters.get("limit", 50),
        offset=filters.get("offset", 0),
    )

    logger.info("command_history_retrieved", count=len(commands))

    return commands
