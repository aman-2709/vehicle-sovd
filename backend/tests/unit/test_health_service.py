"""Unit tests for health service functions.

Tests the actual health check logic for database and Redis connectivity.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import redis.asyncio as aioredis
from sqlalchemy import text


class TestDatabaseHealthCheck:
    """Test database health check function."""

    @pytest.mark.asyncio
    async def test_check_database_health_success(self):
        """Test database health check returns success when database is accessible."""
        from app.services.health_service import check_database_health

        # Mock the engine.connect() context manager
        with patch("app.services.health_service.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn

            # Call the function
            is_healthy, status = await check_database_health()

            # Verify result
            assert is_healthy is True
            assert status == "ok"

            # Verify SELECT 1 was executed
            mock_conn.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_database_health_connection_failure(self):
        """Test database health check returns failure when connection fails."""
        from app.services.health_service import check_database_health

        # Mock the engine.connect() to raise an exception
        with patch("app.services.health_service.engine") as mock_engine:
            mock_engine.connect.return_value.__aenter__.side_effect = Exception(
                "Connection refused"
            )

            # Call the function
            is_healthy, status = await check_database_health()

            # Verify result
            assert is_healthy is False
            assert status == "unavailable"

    @pytest.mark.asyncio
    async def test_check_database_health_query_failure(self):
        """Test database health check returns failure when query fails."""
        from app.services.health_service import check_database_health

        # Mock the engine.connect() but make execute fail
        with patch("app.services.health_service.engine") as mock_engine:
            mock_conn = AsyncMock()
            mock_conn.execute.side_effect = Exception("Query execution failed")
            mock_engine.connect.return_value.__aenter__.return_value = mock_conn

            # Call the function
            is_healthy, status = await check_database_health()

            # Verify result
            assert is_healthy is False
            assert status == "unavailable"


class TestRedisHealthCheck:
    """Test Redis health check function."""

    @pytest.mark.asyncio
    async def test_check_redis_health_success(self):
        """Test Redis health check returns success when Redis is accessible."""
        from app.services.health_service import check_redis_health

        # Mock the redis_client.ping()
        with patch("app.services.health_service.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(return_value=True)

            # Call the function
            is_healthy, status = await check_redis_health()

            # Verify result
            assert is_healthy is True
            assert status == "ok"

            # Verify ping was called
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_redis_health_connection_failure(self):
        """Test Redis health check returns failure when connection fails."""
        from app.services.health_service import check_redis_health

        # Mock the redis_client.ping() to raise RedisError
        with patch("app.services.health_service.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(side_effect=aioredis.RedisError("Connection refused"))

            # Call the function
            is_healthy, status = await check_redis_health()

            # Verify result
            assert is_healthy is False
            assert status == "unavailable"

    @pytest.mark.asyncio
    async def test_check_redis_health_generic_exception(self):
        """Test Redis health check handles generic exceptions."""
        from app.services.health_service import check_redis_health

        # Mock the redis_client.ping() to raise generic exception
        with patch("app.services.health_service.redis_client") as mock_redis:
            mock_redis.ping = AsyncMock(side_effect=Exception("Unexpected error"))

            # Call the function
            is_healthy, status = await check_redis_health()

            # Verify result
            assert is_healthy is False
            assert status == "unavailable"


class TestCheckAllDependencies:
    """Test check_all_dependencies function."""

    @pytest.mark.asyncio
    async def test_check_all_dependencies_all_healthy(self):
        """Test check_all_dependencies returns True when all dependencies are healthy."""
        from app.services.health_service import check_all_dependencies

        # Mock both health check functions to return success
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                # Call the function
                all_healthy, checks = await check_all_dependencies()

                # Verify result
                assert all_healthy is True
                assert checks == {"database": "ok", "redis": "ok"}

    @pytest.mark.asyncio
    async def test_check_all_dependencies_database_unhealthy(self):
        """Test check_all_dependencies returns False when database is unhealthy."""
        from app.services.health_service import check_all_dependencies

        # Mock database as unhealthy, Redis as healthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (True, "ok")

                # Call the function
                all_healthy, checks = await check_all_dependencies()

                # Verify result
                assert all_healthy is False
                assert checks == {"database": "unavailable", "redis": "ok"}

    @pytest.mark.asyncio
    async def test_check_all_dependencies_redis_unhealthy(self):
        """Test check_all_dependencies returns False when Redis is unhealthy."""
        from app.services.health_service import check_all_dependencies

        # Mock Redis as unhealthy, database as healthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (False, "unavailable")

                # Call the function
                all_healthy, checks = await check_all_dependencies()

                # Verify result
                assert all_healthy is False
                assert checks == {"database": "ok", "redis": "unavailable"}

    @pytest.mark.asyncio
    async def test_check_all_dependencies_all_unhealthy(self):
        """Test check_all_dependencies returns False when all dependencies are unhealthy."""
        from app.services.health_service import check_all_dependencies

        # Mock both as unhealthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                # Call the function
                all_healthy, checks = await check_all_dependencies()

                # Verify result
                assert all_healthy is False
                assert checks == {"database": "unavailable", "redis": "unavailable"}

    @pytest.mark.asyncio
    async def test_check_all_dependencies_calls_both_checks(self):
        """Test that check_all_dependencies calls both health check functions."""
        from app.services.health_service import check_all_dependencies

        # Mock both health check functions
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                # Call the function
                await check_all_dependencies()

                # Verify both were called
                mock_db.assert_called_once()
                mock_redis.assert_called_once()
