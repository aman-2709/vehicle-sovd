"""Response repository for database operations on streaming command responses."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.response import Response


async def create_response(
    db: AsyncSession,
    command_id: uuid.UUID,
    response_payload: dict[str, Any],
    sequence_number: int,
    is_final: bool,
) -> Response:
    """
    Create a new command response record.

    Args:
        db: Database session
        command_id: UUID of the parent command
        response_payload: JSONB data from vehicle (flexible schema)
        sequence_number: Order of this response chunk (1-indexed)
        is_final: Whether this is the final response chunk

    Returns:
        Created Response object

    Raises:
        IntegrityError: If (command_id, sequence_number) already exists
    """
    response = Response(
        response_id=uuid.uuid4(),
        command_id=command_id,
        response_payload=response_payload,
        sequence_number=sequence_number,
        is_final=is_final,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response


async def get_responses_by_command_id(
    db: AsyncSession, command_id: uuid.UUID
) -> list[Response]:
    """
    Retrieve all responses for a command, ordered by sequence number.

    Args:
        db: Database session
        command_id: UUID of the command

    Returns:
        List of Response objects ordered by sequence_number (ascending).
        Returns empty list if no responses exist.
    """
    query = (
        select(Response)
        .where(Response.command_id == command_id)
        .order_by(Response.sequence_number)
    )

    result = await db.execute(query)
    return list(result.scalars().all())
