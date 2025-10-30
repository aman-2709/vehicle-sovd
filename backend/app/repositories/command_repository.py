"""
Repository layer for command data access operations.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.command import Command


async def create_command(
    db: AsyncSession,
    user_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
) -> Command:
    """
    Create a new command record.

    Args:
        db: Database session
        user_id: ID of user submitting the command
        vehicle_id: ID of target vehicle
        command_name: SOVD command identifier
        command_params: Command-specific parameters

    Returns:
        Created Command object
    """
    command = Command(
        command_id=uuid.uuid4(),
        user_id=user_id,
        vehicle_id=vehicle_id,
        command_name=command_name,
        command_params=command_params,
    )
    db.add(command)
    await db.commit()
    await db.refresh(command)
    return command


async def get_command_by_id(
    db: AsyncSession, command_id: uuid.UUID
) -> Command | None:
    """
    Retrieve a command by its ID.

    Args:
        db: Database session
        command_id: Command UUID

    Returns:
        Command object if found, None otherwise
    """
    result = await db.execute(
        select(Command).where(Command.command_id == command_id)
    )
    return result.scalar_one_or_none()


async def update_command_status(
    db: AsyncSession,
    command_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
    completed_at: datetime | None = None,
) -> Command | None:
    """
    Update the status and related fields of a command.

    Args:
        db: Database session
        command_id: Command UUID
        status: New status value
        error_message: Error message if status is 'failed'
        completed_at: Completion timestamp if applicable

    Returns:
        Updated Command object if found, None otherwise
    """
    command = await get_command_by_id(db, command_id)
    if command is None:
        return None

    command.status = status
    if error_message is not None:
        command.error_message = error_message
    if completed_at is not None:
        command.completed_at = completed_at

    await db.commit()
    await db.refresh(command)
    return command


async def get_commands(
    db: AsyncSession,
    vehicle_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    status: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Command]:
    """
    Retrieve commands with optional filtering and pagination.

    Args:
        db: Database session
        vehicle_id: Filter by vehicle ID
        user_id: Filter by user ID
        status: Filter by status
        start_date: Filter by start date (submitted_at >= start_date)
        end_date: Filter by end date (submitted_at <= end_date)
        limit: Maximum number of records to return
        offset: Number of records to skip

    Returns:
        List of Command objects
    """
    query = select(Command)

    if vehicle_id is not None:
        query = query.where(Command.vehicle_id == vehicle_id)
    if user_id is not None:
        query = query.where(Command.user_id == user_id)
    if status is not None:
        query = query.where(Command.status == status)
    if start_date is not None:
        query = query.where(Command.submitted_at >= start_date)
    if end_date is not None:
        query = query.where(Command.submitted_at <= end_date)

    query = query.order_by(Command.submitted_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())
