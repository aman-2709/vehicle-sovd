"""
SOVD Command WebApp - FastAPI Application Entry Point

This is a minimal placeholder for the FastAPI application.
The full implementation will be added in subsequent tasks.

Provides:
- Basic FastAPI app instance
- Health check endpoint
- CORS middleware for frontend communication
- Structured logging with correlation IDs
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import health
from app.api.v1 import auth, commands, vehicles, websocket
from app.config import settings
from app.middleware.error_handling_middleware import (
    format_error_response,  # Used in rate_limit_exception_handler
    handle_http_exception,
    handle_unexpected_exception,
    handle_validation_error,
)
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.rate_limiting_middleware import limiter
from app.utils.error_codes import ErrorCode
from app.utils.logging import configure_logging

# Configure structured logging before creating the app
configure_logging(log_level=settings.LOG_LEVEL)

# Create FastAPI application instance
app = FastAPI(
    title="SOVD Command WebApp API",
    description="Cloud-based SOVD 2.0 command execution platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add limiter to app state (required by slowapi)
app.state.limiter = limiter


# Register global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException."""
    return await handle_http_exception(request, exc)


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTPException."""
    # Convert to FastAPI HTTPException
    fastapi_exc = HTTPException(
        status_code=exc.status_code, detail=exc.detail, headers=getattr(exc, "headers", None)
    )
    return await handle_http_exception(request, fastapi_exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    return await handle_validation_error(request, exc)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other unexpected exceptions."""
    return await handle_unexpected_exception(request, exc)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Handle rate limit exceeded errors.

    Returns standardized error response with:
    - Error code RATE_001
    - Retry-After header
    - Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining)
    """
    from structlog.contextvars import get_contextvars

    from app.utils.error_codes import get_error_message

    # Get correlation ID from context (set by LoggingMiddleware)
    context_vars = get_contextvars()
    correlation_id = context_vars.get("correlation_id", "unknown")

    # Extract retry_after from exception detail
    # slowapi formats detail as: "Rate limit exceeded: X per Y minute"
    retry_after = 60  # Default to 60 seconds

    # Get error message for RATE_001
    message = get_error_message(ErrorCode.RATE_LIMIT_EXCEEDED)

    # Format standardized error response with retry_after added
    error_response = format_error_response(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        message=message,
        correlation_id=correlation_id,
        path=str(request.url.path),
    )

    # Add retry_after to error response
    error_response["error"]["retry_after"] = retry_after

    # Create JSON response
    response = JSONResponse(
        status_code=429,
        content=error_response,
    )

    # Add Retry-After header (required by HTTP spec)
    response.headers["Retry-After"] = str(retry_after)

    # Add rate limit headers for client visibility
    # Note: slowapi adds these automatically when headers_enabled=True
    # but we ensure they're present
    if hasattr(exc, "limit"):
        response.headers["X-RateLimit-Limit"] = str(exc.limit)
        response.headers["X-RateLimit-Remaining"] = "0"

    return response

# Register middleware (order matters - LIFO execution)
# Execution order: LoggingMiddleware → CORSMiddleware → SlowAPIMiddleware → Endpoints
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(health.router, tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(vehicles.router, prefix="/api/v1", tags=["vehicles"])
app.include_router(commands.router, prefix="/api/v1", tags=["commands"])
app.include_router(websocket.router, tags=["websocket"])

# Setup Prometheus instrumentation
# This automatically creates metrics for HTTP requests and exposes /metrics endpoint
Instrumentator().instrument(app).expose(app)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """
    Health check endpoint for Docker healthcheck and monitoring.

    Returns:
        dict: Status message indicating the service is operational
    """
    return {
        "status": "healthy",
        "service": "sovd-backend",
        "version": "1.0.0",
    }


@app.get("/")
async def root() -> dict[str, str]:
    """
    Root endpoint providing basic API information.

    Returns:
        dict: Welcome message and documentation links
    """
    return {
        "message": "SOVD Command WebApp API",
        "docs": "/docs",
        "health": "/health",
    }


# Application startup event
@app.on_event("startup")
async def startup_event() -> None:
    """
    Execute initialization tasks on application startup.
    This will be expanded in future tasks to include:
    - Database connection initialization
    - Redis connection setup
    - Background task initialization
    """
    print("SOVD Backend starting up...")
    print("Environment: development")
    print("Listening on: 0.0.0.0:8000")
    print("Prometheus metrics available at: /metrics")


# Application shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """
    Execute cleanup tasks on application shutdown.
    This will be expanded to include:
    - Database connection cleanup
    - Redis connection cleanup
    - Background task cancellation
    """
    print("SOVD Backend shutting down...")
