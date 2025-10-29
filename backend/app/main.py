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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, commands, vehicles, websocket
from app.middleware.logging_middleware import LoggingMiddleware
from app.utils.logging import configure_logging

# Configure structured logging before creating the app
configure_logging()

# Create FastAPI application instance
app = FastAPI(
    title="SOVD Command WebApp API",
    description="Cloud-based SOVD 2.0 command execution platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register middleware (order matters - logging middleware should be first)
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
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(vehicles.router, prefix="/api/v1", tags=["vehicles"])
app.include_router(commands.router, prefix="/api/v1", tags=["commands"])
app.include_router(websocket.router, tags=["websocket"])


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
