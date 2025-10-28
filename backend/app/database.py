"""
Database connection and session management module.

Provides async SQLAlchemy engine and session management for the application.
Uses dependency injection pattern for FastAPI routes.
"""

import logging
from collections.abc import AsyncGenerator

import structlog
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

# Configure structlog for structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger(__name__)

# Create async SQLAlchemy engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,  # Number of connections to maintain in the pool
    max_overflow=10,  # Additional connections allowed beyond pool_size during peak load
    echo=False,  # Set to True for SQL query logging in development
    future=True,  # Use SQLAlchemy 2.0 style
)

# Log database engine creation
logger.info(
    "database_engine_created",
    database_url=settings.DATABASE_URL.split("@")[-1],  # Log only host/db, not credentials
    pool_size=20,
    max_overflow=10,
)

# Create async session factory
# expire_on_commit=False prevents lazy loading errors in async context
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection function for FastAPI routes.

    Yields an async database session and ensures proper cleanup after use.
    Use with FastAPI's Depends() for automatic session management.

    Example:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session for the request
    """
    async with async_session_maker() as session:
        try:
            logger.debug("database_session_created")
            yield session
        finally:
            logger.debug("database_session_closed")
