"""
FastAPI router for command management endpoints.
"""

import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.command import (
    CommandListResponse,
    CommandResponse,
    CommandSubmitRequest,
)
from app.schemas.response import ResponseDetail
from app.services import command_service

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/commands", response_model=CommandResponse, status_code=201)
async def submit_command(
    request: CommandSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> CommandResponse:
    """
    Submit a new command to a vehicle.

    Requires authentication and engineer/admin role.
    Validates vehicle existence before creating command.

    Args:
        request: Command submission request
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        CommandResponse with command details

    Raises:
        HTTPException 400: Vehicle not found
        HTTPException 401: Not authenticated
        HTTPException 403: Insufficient permissions
    """
    logger.info(
        "api_submit_command",
        user_id=str(current_user.user_id),
        vehicle_id=str(request.vehicle_id),
        command_name=request.command_name,
    )

    command = await command_service.submit_command(
        vehicle_id=request.vehicle_id,
        command_name=request.command_name,
        command_params=request.command_params,
        user_id=current_user.user_id,
        db_session=db,
        background_tasks=background_tasks,
    )

    if command is None:
        logger.warning(
            "api_submit_command_failed_vehicle_not_found",
            user_id=str(current_user.user_id),
            vehicle_id=str(request.vehicle_id),
        )
        raise HTTPException(status_code=400, detail="Vehicle not found")

    logger.info(
        "api_submit_command_success",
        command_id=str(command.command_id),
        user_id=str(current_user.user_id),
    )

    return CommandResponse.model_validate(command)


@router.get("/commands/{command_id}", response_model=CommandResponse)
async def get_command(
    command_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommandResponse:
    """
    Retrieve details of a specific command.

    Requires authentication.

    Args:
        command_id: Command UUID
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        CommandResponse with command details

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 404: Command not found
    """
    logger.info(
        "api_get_command",
        command_id=str(command_id),
        user_id=str(current_user.user_id),
    )

    command = await command_service.get_command_by_id(
        command_id=command_id, db_session=db
    )

    if command is None:
        logger.warning(
            "api_get_command_not_found",
            command_id=str(command_id),
            user_id=str(current_user.user_id),
        )
        raise HTTPException(status_code=404, detail="Command not found")

    logger.info(
        "api_get_command_success",
        command_id=str(command_id),
        user_id=str(current_user.user_id),
    )

    return CommandResponse.model_validate(command)


@router.get("/commands/{command_id}/responses", response_model=list[ResponseDetail])
async def get_command_responses(
    command_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResponseDetail]:
    """
    Retrieve all responses for a specific command.

    Returns responses ordered by sequence_number (ascending) to maintain
    proper streaming order. Returns empty list if no responses exist.

    Args:
        command_id: Command UUID
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        List of ResponseDetail objects (empty if no responses)

    Raises:
        HTTPException 401: Not authenticated
    """
    logger.info(
        "api_get_command_responses",
        command_id=str(command_id),
        user_id=str(current_user.user_id),
    )

    responses = await command_service.get_command_responses(
        command_id=command_id, db_session=db
    )

    logger.info(
        "api_get_command_responses_success",
        command_id=str(command_id),
        count=len(responses),
    )

    return [ResponseDetail.model_validate(r) for r in responses]


@router.get("/commands", response_model=CommandListResponse)
async def list_commands(
    vehicle_id: uuid.UUID | None = Query(None, description="Filter by vehicle ID"),
    status: str | None = Query(None, description="Filter by command status"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommandListResponse:
    """
    List commands with optional filtering and pagination.

    Requires authentication.

    Args:
        vehicle_id: Optional vehicle ID filter
        status: Optional status filter
        limit: Maximum records to return (1-100)
        offset: Number of records to skip
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        CommandListResponse with list of commands

    Raises:
        HTTPException 401: Not authenticated
    """
    logger.info(
        "api_list_commands",
        user_id=str(current_user.user_id),
        vehicle_id=str(vehicle_id) if vehicle_id else None,
        status=status,
        limit=limit,
        offset=offset,
    )

    filters = {
        "vehicle_id": vehicle_id,
        "status": status,
        "limit": limit,
        "offset": offset,
    }

    commands = await command_service.get_command_history(
        filters=filters, db_session=db
    )

    logger.info(
        "api_list_commands_success",
        user_id=str(current_user.user_id),
        count=len(commands),
    )

    return CommandListResponse(
        commands=[CommandResponse.model_validate(cmd) for cmd in commands],
        limit=limit,
        offset=offset,
    )
