"""
Pytest configuration and fixtures for testing.

Provides database session and async client fixtures for integration tests.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from unittest.mock import AsyncMock, patch

from app.database import get_db
from app.main import app
from app.models.user import User
from app.models.session import Session
from app.models.base import Base

# Test database URL (using file-based SQLite for testing)
# File-based ensures tables persist across multiple connections in the same test
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Yields:
        AsyncSession: Database session for testing
    """
    # Create async engine for test database
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Disable pooling for in-memory database
    )

    # Create only auth-related tables (users and sessions)
    # Other tables use PostgreSQL-specific types (JSONB) that aren't compatible with SQLite
    async with engine.begin() as conn:
        def create_tables(connection):
            User.__table__.create(connection, checkfirst=True)
            Session.__table__.create(connection, checkfirst=True)
        await conn.run_sync(create_tables)

    # Create session factory
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    # Create session
    async with async_session_maker() as session:
        yield session

    # Drop auth tables after test
    async with engine.begin() as conn:
        def drop_tables(connection):
            Session.__table__.drop(connection, checkfirst=True)
            User.__table__.drop(connection, checkfirst=True)
        await conn.run_sync(drop_tables)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async HTTP client for testing FastAPI endpoints.

    Args:
        db_session: Database session fixture

    Yields:
        AsyncClient: HTTP client for making test requests
    """

    # Override database dependency to use test database
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Mock audit service since audit_logs table uses JSONB (PostgreSQL-specific)
    # and integration tests use SQLite
    with patch("app.services.audit_service.log_audit_event") as mock_audit:
        mock_audit.return_value = True

        # Create async client
        from httpx import ASGITransport
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test"
        ) as client:
            yield client

    # Clear dependency overrides
    app.dependency_overrides.clear()
