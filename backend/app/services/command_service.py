"""
Business logic for command management operations.
"""

import uuid
from typing import Any

import structlog
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors import vehicle_connector
from app.models.command import Command
from app.models.response import Response
from app.repositories import command_repository, response_repository, vehicle_repository
from app.services import sovd_protocol_handler

logger = structlog.get_logger(__name__)


async def submit_command(
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
    user_id: uuid.UUID,
    db_session: AsyncSession,
    background_tasks: BackgroundTasks,
) -> Command | None:
    """
    Submit a command to a vehicle.

    Validates vehicle existence, creates command record, and triggers
    asynchronous mock command execution via the vehicle connector.

    Args:
        vehicle_id: Target vehicle UUID
        command_name: SOVD command identifier
        command_params: Command-specific parameters
        user_id: ID of user submitting the command
        db_session: Database session
        background_tasks: FastAPI background tasks for async execution

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

    # Validate SOVD command
    validation_error = sovd_protocol_handler.validate_command(command_name, command_params)
    if validation_error:
        logger.warning(
            "command_submission_failed_invalid_sovd_command",
            command_name=command_name,
            validation_error=validation_error,
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

    # Trigger async command execution via vehicle connector
    background_tasks.add_task(
        vehicle_connector.execute_command,
        command.command_id,
        vehicle_id,
        command_name,
        command_params,
    )

    logger.info(
        "command_submitted",
        command_id=str(command.command_id),
        status=command.status,
        vehicle_id=str(vehicle_id),
        user_id=str(user_id),
    )

    return command


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


async def get_command_responses(
    command_id: uuid.UUID, db_session: AsyncSession
) -> list[Response]:
    """
    Retrieve all responses for a command, ordered by sequence number.

    Args:
        command_id: Command UUID
        db_session: Database session

    Returns:
        List of Response objects ordered by sequence_number (ascending).
        Returns empty list if no responses exist.
    """
    logger.info("command_responses_retrieval", command_id=str(command_id))

    responses = await response_repository.get_responses_by_command_id(
        db_session, command_id
    )

    logger.info(
        "command_responses_retrieved",
        command_id=str(command_id),
        count=len(responses),
    )

    return responses
