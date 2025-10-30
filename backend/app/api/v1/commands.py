"""
FastAPI router for command management endpoints.
"""

import uuid

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user, require_role
from app.middleware.rate_limiting_middleware import RATE_LIMIT_COMMANDS, get_user_id_key, limiter
from app.models.user import User
from app.schemas.command import (
    CommandListResponse,
    CommandResponse,
    CommandSubmitRequest,
)
from app.schemas.response import ResponseDetail
from app.services import audit_service, command_service
from app.utils.request_utils import get_client_ip, get_user_agent

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/commands", response_model=CommandResponse, status_code=201)
@limiter.limit(RATE_LIMIT_COMMANDS, key_func=get_user_id_key)
async def submit_command(
    request: Request,
    command_request: CommandSubmitRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["engineer", "admin"])),
    db: AsyncSession = Depends(get_db),
) -> CommandResponse:
    """
    Submit a new command to a vehicle.

    Requires authentication and engineer/admin role.
    Validates vehicle existence and SOVD command format before creating command.

    Args:
        command_request: Command submission request
        http_request: FastAPI Request object for extracting IP/user-agent
        background_tasks: Background tasks for async command execution
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        CommandResponse with command details

    Raises:
        HTTPException 400: Vehicle not found or invalid SOVD command
        HTTPException 401: Not authenticated
        HTTPException 403: Insufficient permissions
    """
    # Extract client information for audit logging
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)

    logger.info(
        "api_submit_command",
        user_id=str(current_user.user_id),
        vehicle_id=str(command_request.vehicle_id),
        command_name=command_request.command_name,
    )

    command = await command_service.submit_command(
        vehicle_id=command_request.vehicle_id,
        command_name=command_request.command_name,
        command_params=command_request.command_params,
        user_id=current_user.user_id,
        db_session=db,
        background_tasks=background_tasks,
    )

    if command is None:
        logger.warning(
            "api_submit_command_failed",
            user_id=str(current_user.user_id),
            vehicle_id=str(command_request.vehicle_id),
        )
        raise HTTPException(
            status_code=400,
            detail="Invalid command: vehicle not found or command validation failed"
        )

    logger.info(
        "api_submit_command_success",
        command_id=str(command.command_id),
        user_id=str(current_user.user_id),
    )

    # Log audit event for command submission
    await audit_service.log_audit_event(
        user_id=current_user.user_id,
        action="command_submitted",
        entity_type="command",
        entity_id=command.command_id,
        details={
            "command_name": command.command_name,
            "command_params": command.command_params,
        },
        ip_address=client_ip,
        user_agent=user_agent,
        db_session=db,
        vehicle_id=command_request.vehicle_id,
        command_id=command.command_id,
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
    user_id: uuid.UUID | None = Query(None, description="Filter by user ID (admin only)"),
    start_date: str | None = Query(None, description="Filter by start date (ISO 8601 format)"),
    end_date: str | None = Query(None, description="Filter by end date (ISO 8601 format)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommandListResponse:
    """
    List commands with optional filtering and pagination.

    Requires authentication. Engineers can only see their own commands.
    Admins can see all commands and optionally filter by user.

    Args:
        vehicle_id: Optional vehicle ID filter
        status: Optional status filter
        user_id: Optional user ID filter (admin only)
        start_date: Optional start date filter (ISO 8601 format)
        end_date: Optional end date filter (ISO 8601 format)
        limit: Maximum records to return (1-100)
        offset: Number of records to skip
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        CommandListResponse with list of commands

    Raises:
        HTTPException 401: Not authenticated
        HTTPException 403: User ID filter used by non-admin
        HTTPException 400: Invalid date format
    """
    # Parse date strings to datetime objects if provided
    start_datetime = None
    end_datetime = None

    if start_date:
        try:
            from datetime import datetime
            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start_date format. Use ISO 8601 format (e.g., 2025-10-29T00:00:00Z)"
            )

    if end_date:
        try:
            from datetime import datetime
            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid end_date format. Use ISO 8601 format (e.g., 2025-10-29T23:59:59Z)"
            )

    # RBAC enforcement: Engineers can only see their own commands
    effective_user_id = None
    if current_user.role == "engineer":
        # Engineers can only see their own commands
        effective_user_id = current_user.user_id
        logger.info(
            "api_list_commands_rbac_engineer",
            user_id=str(current_user.user_id),
            enforced_filter="user_id",
        )
    elif current_user.role == "admin":
        # Admins can optionally filter by user_id or see all
        if user_id is not None:
            effective_user_id = user_id
            logger.info(
                "api_list_commands_rbac_admin_filtered",
                admin_id=str(current_user.user_id),
                filter_user_id=str(user_id),
            )
        else:
            logger.info(
                "api_list_commands_rbac_admin_all",
                admin_id=str(current_user.user_id),
            )
    else:
        # Other roles (viewer, etc.) can see their own commands
        effective_user_id = current_user.user_id
        logger.info(
            "api_list_commands_rbac_other",
            user_id=str(current_user.user_id),
            role=current_user.role,
        )

    logger.info(
        "api_list_commands",
        user_id=str(current_user.user_id),
        vehicle_id=str(vehicle_id) if vehicle_id else None,
        status=status,
        filter_user_id=str(effective_user_id) if effective_user_id else None,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )

    filters = {
        "vehicle_id": vehicle_id,
        "user_id": effective_user_id,
        "status": status,
        "start_date": start_datetime,
        "end_date": end_datetime,
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
