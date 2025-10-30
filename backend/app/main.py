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
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import health
from app.api.v1 import auth, commands, vehicles, websocket
from app.config import settings
from app.middleware.error_handling_middleware import (
    handle_http_exception,
    handle_unexpected_exception,
    handle_validation_error,
)
from app.middleware.logging_middleware import LoggingMiddleware
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

# Register middleware (order matters - LIFO execution)
# Execution order: LoggingMiddleware → CORSMiddleware → Endpoints
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
