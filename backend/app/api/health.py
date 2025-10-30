"""Health check API endpoints.

This module provides Kubernetes-style health check endpoints:
- /health/live: Liveness probe (simple, no dependency checks)
- /health/ready: Readiness probe (checks database and Redis)

These endpoints follow Kubernetes best practices:
- Liveness checks are lightweight and don't check external dependencies
- Readiness checks verify all external dependencies are healthy
- Proper HTTP status codes (200 for healthy, 503 for unavailable)
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.services import health_service

router = APIRouter()


class LivenessResponse(BaseModel):
    """Response model for liveness endpoint."""

    status: str


class ReadinessResponse(BaseModel):
    """Response model for readiness endpoint."""

    status: str
    checks: dict[str, str]


@router.get(
    "/health/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Simple liveness check that verifies the application process is running. "
    "Does not check external dependencies. Used by Kubernetes to determine if "
    "the container should be restarted.",
    tags=["health"],
)
async def liveness() -> LivenessResponse:
    """Liveness probe endpoint.

    This endpoint always returns 200 OK if the application is running.
    It does NOT check external dependencies (database, Redis) to avoid
    cascading failures. If this endpoint fails, Kubernetes will restart
    the container.

    Returns:
        LivenessResponse: Simple status indicating the process is alive
            {"status": "ok"}

    Example:
        GET /health/live
        Response: 200 OK
        {
            "status": "ok"
        }
    """
    # Simple response with no dependency checks
    # If this code is executing, the process is alive
    return LivenessResponse(status="ok")


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness probe",
    description="Readiness check that verifies all external dependencies (database, Redis) "
    "are healthy and the application is ready to serve traffic. Returns 503 if "
    "any dependency is unavailable. Used by Kubernetes to determine if traffic "
    "should be routed to this pod.",
    responses={
        200: {
            "description": "Service is ready to serve traffic",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ready",
                        "checks": {"database": "ok", "redis": "ok"},
                    }
                }
            },
        },
        503: {
            "description": "Service is not ready (dependency unavailable)",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unavailable",
                        "checks": {"database": "ok", "redis": "unavailable"},
                    }
                }
            },
        },
    },
    tags=["health"],
)
async def readiness() -> ReadinessResponse:
    """Readiness probe endpoint.

    This endpoint checks all external dependencies (database and Redis) to
    determine if the application is ready to serve traffic. Returns 200 OK
    if all dependencies are healthy, 503 Service Unavailable if any
    dependency fails.

    If this endpoint returns 503, Kubernetes will stop routing traffic to
    this pod until it returns 200 again.

    Returns:
        ReadinessResponse: Status and individual dependency check results
            {"status": "ready|unavailable", "checks": {...}}

    Raises:
        HTTPException: 503 if any dependency is unavailable

    Example (healthy):
        GET /health/ready
        Response: 200 OK
        {
            "status": "ready",
            "checks": {
                "database": "ok",
                "redis": "ok"
            }
        }

    Example (unhealthy):
        GET /health/ready
        Response: 503 Service Unavailable
        {
            "status": "unavailable",
            "checks": {
                "database": "ok",
                "redis": "unavailable"
            }
        }
    """
    # Check all dependencies
    all_healthy, checks = await health_service.check_all_dependencies()

    # If any dependency is unhealthy, return 503
    if not all_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ReadinessResponse(
                status="unavailable",
                checks=checks,
            ).model_dump(),
        )

    # All dependencies healthy
    return ReadinessResponse(status="ready", checks=checks)
