"""Vehicle service with business logic and Redis caching.

This module orchestrates vehicle operations, implementing caching strategies
and coordinating between repository and API layers.
"""

import json
import uuid
from typing import Any

import redis.asyncio as aioredis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.vehicle import Vehicle
from app.repositories import vehicle_repository

logger = structlog.get_logger(__name__)

# Module-level Redis client (connection pool)
# Uses async Redis client to prevent blocking the event loop
redis_client = aioredis.from_url(  # type: ignore[no-untyped-call]
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True
)


async def get_all_vehicles(
    db: AsyncSession,
    filters: dict[str, Any],
    limit: int = 50,
    offset: int = 0,
) -> list[Vehicle]:
    """Get all vehicles with optional filtering and pagination.

    Orchestrates vehicle retrieval with support for filtering by connection status
    and searching by VIN (partial match).

    Args:
        db: Async database session
        filters: Dictionary with optional keys:
            - status: Filter by connection status (connected, disconnected, error)
            - search: Search by VIN (partial match, case-insensitive)
        limit: Maximum number of results to return (default: 50)
        offset: Number of results to skip for pagination (default: 0)

    Returns:
        List of Vehicle objects matching the filters

    Example:
        vehicles = await get_all_vehicles(
            db,
            filters={"status": "connected", "search": "TEST"},
            limit=10,
            offset=0
        )
    """
    # Extract filters
    status_filter = filters.get("status")
    search_term = filters.get("search")

    logger.info(
        "fetching_vehicles",
        status_filter=status_filter,
        search_term=search_term,
        limit=limit,
        offset=offset,
    )

    # Fetch vehicles from repository
    vehicles = await vehicle_repository.get_all_vehicles(
        db=db,
        status_filter=status_filter,
        search_term=search_term,
        limit=limit,
        offset=offset,
    )

    logger.info(
        "vehicles_fetched",
        count=len(vehicles),
        filters=filters,
    )

    return vehicles


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
    logger.info("fetching_vehicle_by_id", vehicle_id=str(vehicle_id))

    vehicle = await vehicle_repository.get_vehicle_by_id(db, vehicle_id)

    if vehicle:
        logger.info(
            "vehicle_found",
            vehicle_id=str(vehicle_id),
            vin=vehicle.vin,
        )
    else:
        logger.warning("vehicle_not_found", vehicle_id=str(vehicle_id))

    return vehicle


async def get_vehicle_status(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Get vehicle status with Redis caching (TTL=30s).

    This function implements a caching strategy to reduce database load for
    frequently accessed vehicle status data. The cache TTL is set to 30 seconds
    to balance freshness with performance.

    Cache behavior:
    - Cache hit: Returns cached data immediately (logged as cache_hit)
    - Cache miss: Fetches from database, caches result, returns data (logged as cache_miss)
    - Redis error: Falls back to database query without caching (logged as redis_error)

    Args:
        db: Async database session
        vehicle_id: UUID of the vehicle to get status for

    Returns:
        Dictionary with status data if vehicle found, None otherwise:
        {
            "connection_status": str,
            "last_seen_at": str (ISO format) or None,
            "health": dict or None
        }

    Example:
        status = await get_vehicle_status(db, vehicle_id)
        if status:
            print(f"Status: {status['connection_status']}")
    """
    cache_key = f"vehicle_status:{vehicle_id}"
    logger.info("fetching_vehicle_status", vehicle_id=str(vehicle_id))

    # Try to get from Redis cache first
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info("cache_hit", vehicle_id=str(vehicle_id))
            cached_data: dict[str, Any] = json.loads(cached)
            return cached_data
    except aioredis.RedisError as e:
        # Log error but don't fail - fall through to database query
        logger.warning(
            "redis_error",
            error=str(e),
            vehicle_id=str(vehicle_id),
            operation="get",
        )

    # Cache miss or Redis error - fetch from database
    logger.info("cache_miss", vehicle_id=str(vehicle_id))

    vehicle = await vehicle_repository.get_vehicle_by_id(db, vehicle_id)
    if not vehicle:
        logger.warning("vehicle_not_found_for_status", vehicle_id=str(vehicle_id))
        return None

    # Build status dictionary
    status = {
        "connection_status": vehicle.connection_status,
        "last_seen_at": vehicle.last_seen_at.isoformat() if vehicle.last_seen_at else None,
        "health": None,  # Placeholder for future health metrics
    }

    # Try to cache the result
    try:
        await redis_client.setex(
            cache_key,
            30,  # TTL = 30 seconds
            json.dumps(status),
        )
        logger.info(
            "status_cached",
            vehicle_id=str(vehicle_id),
            ttl=30,
        )
    except aioredis.RedisError as e:
        # Log error but don't fail - we still have the data to return
        logger.warning(
            "redis_error",
            error=str(e),
            vehicle_id=str(vehicle_id),
            operation="setex",
        )

    return status
