"""Vehicle repository for database operations.

This module provides async database access functions for vehicle-related operations.
Follows SQLAlchemy 2.0 async patterns with proper type hints.
"""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle


async def get_all_vehicles(
    db: AsyncSession,
    status_filter: str | None = None,
    search_term: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[Vehicle]:
    """Get all vehicles with optional filtering and pagination.

    Args:
        db: Async database session
        status_filter: Filter by connection status (connected, disconnected, error)
        search_term: Search by VIN (partial match, case-insensitive)
        limit: Maximum number of results to return (default: 50)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        List of Vehicle objects matching the filters

    Example:
        vehicles = await get_all_vehicles(db, status_filter="connected", limit=10)
    """
    query = select(Vehicle)

    # Apply status filter if provided
    if status_filter:
        query = query.where(Vehicle.connection_status == status_filter)

    # Apply VIN search filter if provided (partial match, case-insensitive)
    if search_term:
        query = query.where(Vehicle.vin.ilike(f"%{search_term}%"))

    # Apply pagination
    query = query.limit(limit).offset(offset)

    # Execute query
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_vehicle_by_id(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> Vehicle | None:
    """Get a single vehicle by ID.

    Args:
        db: Async database session
        vehicle_id: UUID of the vehicle to retrieve

    Returns:
        Vehicle object if found, None otherwise

    Example:
        vehicle = await get_vehicle_by_id(db, vehicle_id)
        if vehicle:
            print(f"Found vehicle: {vehicle.vin}")
    """
    result = await db.execute(
        select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
    )
    return result.scalar_one_or_none()


async def get_vehicle_by_vin(
    db: AsyncSession,
    vin: str,
) -> Vehicle | None:
    """Get a single vehicle by VIN.

    Args:
        db: Async database session
        vin: Vehicle Identification Number (exact match)

    Returns:
        Vehicle object if found, None otherwise

    Example:
        vehicle = await get_vehicle_by_vin(db, "TESTVEHICLE000001")
    """
    result = await db.execute(
        select(Vehicle).where(Vehicle.vin == vin)
    )
    return result.scalar_one_or_none()


async def update_vehicle_status(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    connection_status: str,
    last_seen_at: datetime,
) -> Vehicle | None:
    """Update vehicle connection status and last_seen_at timestamp.

    Args:
        db: Async database session
        vehicle_id: UUID of the vehicle to update
        connection_status: New connection status (connected, disconnected, error)
        last_seen_at: New timestamp for last seen

    Returns:
        Updated Vehicle object if found, None otherwise

    Example:
        from datetime import datetime, timezone
        vehicle = await update_vehicle_status(
            db,
            vehicle_id,
            "connected",
            datetime.now(timezone.utc)
        )
    """
    # Get the vehicle
    vehicle = await get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        return None

    # Update fields
    vehicle.connection_status = connection_status
    vehicle.last_seen_at = last_seen_at

    # Commit changes
    await db.commit()
    await db.refresh(vehicle)

    return vehicle
