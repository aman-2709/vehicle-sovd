"""Vehicle API endpoints.

This module provides FastAPI routes for vehicle management operations:
- List vehicles with filtering and pagination
- Get vehicle details by ID
- Get vehicle connection status (with Redis caching)

All endpoints require JWT authentication.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.vehicle import VehicleResponse, VehicleStatusResponse
from app.services import vehicle_service

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/vehicles", response_model=list[VehicleResponse])
async def list_vehicles(  # type: ignore[no-untyped-def]

    status: str | None = Query(
        None,
        description="Filter by connection status (connected, disconnected, error)"
    ),
    search: str | None = Query(
        None,
        description="Search by VIN (partial match, case-insensitive)"
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of results to skip for pagination"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of vehicles with optional filtering and pagination.

    Query parameters:
    - status: Filter by connection status (connected, disconnected, error)
    - search: Search by VIN (partial match, case-insensitive)
    - limit: Maximum number of results (1-100, default: 50)
    - offset: Number of results to skip (default: 0)

    Requires authentication via JWT bearer token.

    Returns:
        List of vehicle objects with details (vehicle_id, vin, make, model, year,
        connection_status, last_seen_at, metadata)

    Raises:
        401 Unauthorized: If JWT token is missing or invalid
        422 Unprocessable Entity: If query parameters are invalid

    Example:
        GET /api/v1/vehicles?status=connected&limit=10&offset=0
        Headers: Authorization: Bearer {jwt_token}
    """
    logger.info(
        "list_vehicles_request",
        user_id=str(current_user.user_id),
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )

    # Build filters dictionary
    filters = {}
    if status:
        filters["status"] = status
    if search:
        filters["search"] = search

    # Fetch vehicles from service
    vehicles = await vehicle_service.get_all_vehicles(
        db=db,
        filters=filters,
        limit=limit,
        offset=offset,
    )

    logger.info(
        "list_vehicles_response",
        count=len(vehicles),
        user_id=str(current_user.user_id),
    )

    # Convert SQLAlchemy models to Pydantic models
    return [VehicleResponse.model_validate(v) for v in vehicles]


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(  # type: ignore[no-untyped-def]

    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single vehicle by ID.

    Path parameters:
    - vehicle_id: UUID of the vehicle to retrieve

    Requires authentication via JWT bearer token.

    Returns:
        Vehicle object with full details (vehicle_id, vin, make, model, year,
        connection_status, last_seen_at, metadata)

    Raises:
        401 Unauthorized: If JWT token is missing or invalid
        404 Not Found: If vehicle with given ID does not exist
        422 Unprocessable Entity: If vehicle_id is not a valid UUID

    Example:
        GET /api/v1/vehicles/123e4567-e89b-12d3-a456-426614174000
        Headers: Authorization: Bearer {jwt_token}
    """
    logger.info(
        "get_vehicle_request",
        vehicle_id=str(vehicle_id),
        user_id=str(current_user.user_id),
    )

    # Fetch vehicle from service
    vehicle = await vehicle_service.get_vehicle_by_id(db, vehicle_id)

    if not vehicle:
        logger.warning(
            "vehicle_not_found",
            vehicle_id=str(vehicle_id),
            user_id=str(current_user.user_id),
        )
        raise HTTPException(status_code=404, detail="Vehicle not found")

    logger.info(
        "get_vehicle_response",
        vehicle_id=str(vehicle_id),
        vin=vehicle.vin,
        user_id=str(current_user.user_id),
    )

    # Convert SQLAlchemy model to Pydantic model
    return VehicleResponse.model_validate(vehicle)


@router.get("/vehicles/{vehicle_id}/status", response_model=VehicleStatusResponse)
async def get_vehicle_status(  # type: ignore[no-untyped-def]

    vehicle_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get vehicle connection status (cached in Redis for 30 seconds).

    This endpoint is optimized for frequent polling by frontend dashboards.
    Vehicle status is cached in Redis with a 30-second TTL to reduce database load.

    Path parameters:
    - vehicle_id: UUID of the vehicle to get status for

    Requires authentication via JWT bearer token.

    Returns:
        Vehicle status object with connection_status, last_seen_at, and health metrics

    Raises:
        401 Unauthorized: If JWT token is missing or invalid
        404 Not Found: If vehicle with given ID does not exist
        422 Unprocessable Entity: If vehicle_id is not a valid UUID

    Example:
        GET /api/v1/vehicles/123e4567-e89b-12d3-a456-426614174000/status
        Headers: Authorization: Bearer {jwt_token}

    Note:
        Second request within 30 seconds will return cached data (faster response).
        Check logs for "cache_hit" vs "cache_miss" to verify caching behavior.
    """
    logger.info(
        "get_vehicle_status_request",
        vehicle_id=str(vehicle_id),
        user_id=str(current_user.user_id),
    )

    # Fetch vehicle status from service (with Redis caching)
    status = await vehicle_service.get_vehicle_status(db, vehicle_id)

    if not status:
        logger.warning(
            "vehicle_not_found_for_status",
            vehicle_id=str(vehicle_id),
            user_id=str(current_user.user_id),
        )
        raise HTTPException(status_code=404, detail="Vehicle not found")

    logger.info(
        "get_vehicle_status_response",
        vehicle_id=str(vehicle_id),
        connection_status=status["connection_status"],
        user_id=str(current_user.user_id),
    )

    # Return status as Pydantic model
    return VehicleStatusResponse(**status)
