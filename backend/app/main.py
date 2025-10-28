"""
SOVD Command WebApp - FastAPI Application Entry Point

This is a minimal placeholder for the FastAPI application.
The full implementation will be added in subsequent tasks.

Provides:
- Basic FastAPI app instance
- Health check endpoint
- CORS middleware for frontend communication
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth

# Create FastAPI application instance
app = FastAPI(
    title="SOVD Command WebApp API",
    description="Cloud-based SOVD 2.0 command execution platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Docker healthcheck and monitoring.

    Returns:
        dict: Status message indicating the service is operational
    """
    return {
        "status": "healthy",
        "service": "sovd-backend",
        "version": "0.1.0",
    }


@app.get("/")
async def root():
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
async def startup_event():
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
async def shutdown_event():
    """
    Execute cleanup tasks on application shutdown.
    This will be expanded to include:
    - Database connection cleanup
    - Redis connection cleanup
    - Background task cancellation
    """
    print("SOVD Backend shutting down...")
