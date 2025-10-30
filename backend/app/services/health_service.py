"""Health check service for monitoring application dependencies.

This module provides health check functions for verifying the status of
external dependencies (database, Redis) following Kubernetes health check patterns.
"""

import redis.asyncio as aioredis
import structlog
from sqlalchemy import text

from app.config import settings
from app.database import engine

logger = structlog.get_logger(__name__)

# Module-level Redis client for health checks
# Uses async Redis client matching the pattern in vehicle_service.py
redis_client = aioredis.from_url(  # type: ignore[no-untyped-call]
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def check_database_health() -> tuple[bool, str]:
    """Check database connectivity and health.

    Executes a simple SELECT 1 query to verify the database is accessible
    and can process queries. Uses the existing async engine from database.py.

    Returns:
        tuple[bool, str]: (is_healthy, status_message)
            - is_healthy: True if database is accessible, False otherwise
            - status_message: "ok" if healthy, error message if not

    Example:
        is_healthy, status = await check_database_health()
        if is_healthy:
            print("Database is healthy")
        else:
            print(f"Database error: {status}")
    """
    try:
        # Use async context manager to ensure connection cleanup
        async with engine.connect() as conn:
            # Execute simple query to verify connectivity
            await conn.execute(text("SELECT 1"))
            logger.debug("database_health_check_success")
            return True, "ok"
    except Exception as e:
        # Log error with details but don't expose internal details in status
        logger.error(
            "database_health_check_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, "unavailable"


async def check_redis_health() -> tuple[bool, str]:
    """Check Redis connectivity and health.

    Uses the PING command to verify Redis is accessible and responsive.
    Follows the Redis client pattern from vehicle_service.py.

    Returns:
        tuple[bool, str]: (is_healthy, status_message)
            - is_healthy: True if Redis is accessible, False otherwise
            - status_message: "ok" if healthy, error message if not

    Example:
        is_healthy, status = await check_redis_health()
        if is_healthy:
            print("Redis is healthy")
        else:
            print(f"Redis error: {status}")
    """
    try:
        # Use PING command to verify Redis connectivity
        # Returns True if successful, raises exception if not
        await redis_client.ping()
        logger.debug("redis_health_check_success")
        return True, "ok"
    except aioredis.RedisError as e:
        # Log Redis-specific errors
        logger.error(
            "redis_health_check_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, "unavailable"
    except Exception as e:
        # Catch any other unexpected errors
        logger.error(
            "redis_health_check_failed",
            error=str(e),
            error_type=type(e).__name__,
        )
        return False, "unavailable"


async def check_all_dependencies() -> tuple[bool, dict[str, str]]:
    """Check health of all external dependencies.

    This function checks both database and Redis, returning an overall
    health status and individual check results.

    Returns:
        tuple[bool, dict[str, str]]: (all_healthy, checks)
            - all_healthy: True only if ALL dependencies are healthy
            - checks: Dictionary with individual check results
                {"database": "ok|unavailable", "redis": "ok|unavailable"}

    Example:
        all_healthy, checks = await check_all_dependencies()
        if all_healthy:
            print("All dependencies healthy")
        else:
            print(f"Failed checks: {checks}")
    """
    # Check database health
    db_healthy, db_status = await check_database_health()

    # Check Redis health
    redis_healthy, redis_status = await check_redis_health()

    # Build checks dictionary
    checks = {
        "database": db_status,
        "redis": redis_status,
    }

    # Overall health is true only if ALL checks pass
    all_healthy = db_healthy and redis_healthy

    logger.info(
        "health_check_completed",
        all_healthy=all_healthy,
        database=db_status,
        redis=redis_status,
    )

    return all_healthy, checks
