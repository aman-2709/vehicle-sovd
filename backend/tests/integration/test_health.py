"""Integration tests for health check API endpoints.

Tests liveness and readiness endpoints with success and failure scenarios.
Uses mocks for database and Redis to simulate healthy and unhealthy states.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


class TestLivenessEndpoint:
    """Test GET /health/live endpoint."""

    @pytest.mark.asyncio
    async def test_liveness_returns_ok(self, async_client: AsyncClient):
        """Test liveness endpoint returns 200 OK when application is running."""
        response = await async_client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_liveness_response_structure(self, async_client: AsyncClient):
        """Test liveness endpoint returns correct response structure."""
        response = await async_client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response has only the expected fields
        assert "status" in data
        assert len(data) == 1

    @pytest.mark.asyncio
    async def test_liveness_no_dependency_checks(self, async_client: AsyncClient):
        """Test liveness endpoint does not perform dependency checks.

        This test verifies that liveness always returns OK regardless of
        external dependency status, following Kubernetes best practices.
        """
        # Mock dependencies to fail
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                # Liveness should still return 200 OK
                response = await async_client.get("/health/live")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data["status"] == "ok"

                # Verify dependency check functions were never called
                mock_db.assert_not_called()
                mock_redis.assert_not_called()


class TestReadinessEndpoint:
    """Test GET /health/ready endpoint."""

    @pytest.mark.asyncio
    async def test_readiness_healthy_all_dependencies(self, async_client: AsyncClient):
        """Test readiness returns 200 OK when all dependencies are healthy."""
        # Mock all dependencies as healthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                assert data["status"] == "ready"
                assert "checks" in data
                assert data["checks"]["database"] == "ok"
                assert data["checks"]["redis"] == "ok"

    @pytest.mark.asyncio
    async def test_readiness_unhealthy_database_failure(self, async_client: AsyncClient):
        """Test readiness returns 503 when database is unavailable."""
        # Mock database as unhealthy, Redis as healthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (True, "ok")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                data = response.json()

                # Response now contains the dict directly with added correlation_id
                assert "status" in data
                assert data["status"] == "unavailable"
                assert data["checks"]["database"] == "unavailable"
                assert data["checks"]["redis"] == "ok"
                assert "correlation_id" in data

    @pytest.mark.asyncio
    async def test_readiness_unhealthy_redis_failure(self, async_client: AsyncClient):
        """Test readiness returns 503 when Redis is unavailable."""
        # Mock Redis as unhealthy, database as healthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (False, "unavailable")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                data = response.json()

                assert "status" in data
                assert data["status"] == "unavailable"
                assert data["checks"]["database"] == "ok"
                assert data["checks"]["redis"] == "unavailable"
                assert "correlation_id" in data

    @pytest.mark.asyncio
    async def test_readiness_unhealthy_all_dependencies(self, async_client: AsyncClient):
        """Test readiness returns 503 when all dependencies are unavailable."""
        # Mock all dependencies as unhealthy
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                data = response.json()

                assert "status" in data
                assert data["status"] == "unavailable"
                assert data["checks"]["database"] == "unavailable"
                assert data["checks"]["redis"] == "unavailable"
                assert "correlation_id" in data

    @pytest.mark.asyncio
    async def test_readiness_response_structure_healthy(self, async_client: AsyncClient):
        """Test readiness endpoint returns correct response structure when healthy."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Verify response structure
                assert "status" in data
                assert "checks" in data
                assert isinstance(data["checks"], dict)
                assert "database" in data["checks"]
                assert "redis" in data["checks"]

    @pytest.mark.asyncio
    async def test_readiness_response_structure_unhealthy(self, async_client: AsyncClient):
        """Test readiness endpoint returns correct response structure when unhealthy."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                data = response.json()

                # Verify response structure (dict directly with correlation_id)
                assert "status" in data
                assert "checks" in data
                assert isinstance(data["checks"], dict)
                assert "correlation_id" in data


class TestHealthEndpointEdgeCases:
    """Test edge cases and error scenarios for health endpoints."""

    @pytest.mark.asyncio
    async def test_liveness_multiple_requests(self, async_client: AsyncClient):
        """Test liveness endpoint handles multiple concurrent requests."""
        # Make multiple requests
        responses = []
        for _ in range(5):
            response = await async_client.get("/health/live")
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == status.HTTP_200_OK
            assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_readiness_multiple_requests_healthy(self, async_client: AsyncClient):
        """Test readiness endpoint handles multiple concurrent requests when healthy."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                # Make multiple requests
                responses = []
                for _ in range(5):
                    response = await async_client.get("/health/ready")
                    responses.append(response)

                # All should succeed
                for response in responses:
                    assert response.status_code == status.HTTP_200_OK
                    assert response.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_readiness_recovers_after_failure(self, async_client: AsyncClient):
        """Test readiness endpoint recovers when dependencies become healthy again."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                # First request: unhealthy
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                response1 = await async_client.get("/health/ready")
                assert response1.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

                # Second request: healthy (dependencies recovered)
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                response2 = await async_client.get("/health/ready")
                assert response2.status_code == status.HTTP_200_OK
                assert response2.json()["status"] == "ready"

    @pytest.mark.asyncio
    async def test_readiness_partial_dependency_failure(self, async_client: AsyncClient):
        """Test readiness endpoint with partial dependency failures.

        This test verifies that if one dependency fails and another succeeds,
        the endpoint correctly reports both statuses and returns 503.
        """
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                # First scenario: database fails, Redis succeeds
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (True, "ok")

                response = await async_client.get("/health/ready")
                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

                # Verify both checks are reported accurately
                data = response.json()
                assert "checks" in data
                assert data["checks"]["database"] == "unavailable"
                assert data["checks"]["redis"] == "ok"


class TestHealthEndpointIntegration:
    """Test integration scenarios for health endpoints."""

    @pytest.mark.asyncio
    async def test_liveness_and_readiness_together(self, async_client: AsyncClient):
        """Test that liveness and readiness can be called independently."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                # Setup: dependencies unhealthy
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                # Liveness should always be OK
                liveness_response = await async_client.get("/health/live")
                assert liveness_response.status_code == status.HTTP_200_OK

                # Readiness should fail
                readiness_response = await async_client.get("/health/ready")
                assert readiness_response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    @pytest.mark.asyncio
    async def test_readiness_calls_all_checks(self, async_client: AsyncClient):
        """Test that readiness endpoint calls both database and Redis checks."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                await async_client.get("/health/ready")

                # Verify both check functions were called
                mock_db.assert_called_once()
                mock_redis.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_endpoints_accessible_without_auth(self, async_client: AsyncClient):
        """Test that health endpoints are accessible without authentication.

        Health endpoints should be public for use by monitoring systems.
        """
        # Liveness without auth
        liveness_response = await async_client.get("/health/live")
        assert liveness_response.status_code == status.HTTP_200_OK

        # Readiness without auth (with mocked dependencies)
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                readiness_response = await async_client.get("/health/ready")
                assert readiness_response.status_code == status.HTTP_200_OK


class TestHealthEndpointDocumentation:
    """Test that health endpoints follow documented behavior."""

    @pytest.mark.asyncio
    async def test_liveness_returns_json(self, async_client: AsyncClient):
        """Test liveness endpoint returns valid JSON."""
        response = await async_client.get("/health/live")

        assert response.status_code == status.HTTP_200_OK
        assert response.headers["content-type"] == "application/json"

        # Should not raise exception
        data = response.json()
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_readiness_returns_json(self, async_client: AsyncClient):
        """Test readiness endpoint returns valid JSON in both success and failure cases."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                # Test success case
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                response_ok = await async_client.get("/health/ready")
                assert response_ok.status_code == status.HTTP_200_OK
                assert response_ok.headers["content-type"] == "application/json"
                data_ok = response_ok.json()
                assert isinstance(data_ok, dict)

                # Test failure case
                mock_db.return_value = (False, "unavailable")
                mock_redis.return_value = (False, "unavailable")

                response_fail = await async_client.get("/health/ready")
                assert response_fail.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                assert response_fail.headers["content-type"] == "application/json"
                data_fail = response_fail.json()
                assert isinstance(data_fail, dict)

    @pytest.mark.asyncio
    async def test_readiness_check_details_included(self, async_client: AsyncClient):
        """Test that readiness endpoint includes individual check results."""
        with patch("app.services.health_service.check_database_health") as mock_db:
            with patch("app.services.health_service.check_redis_health") as mock_redis:
                mock_db.return_value = (True, "ok")
                mock_redis.return_value = (True, "ok")

                response = await async_client.get("/health/ready")

                assert response.status_code == status.HTTP_200_OK
                data = response.json()

                # Verify individual checks are reported
                assert "checks" in data
                assert "database" in data["checks"]
                assert "redis" in data["checks"]
                assert data["checks"]["database"] == "ok"
                assert data["checks"]["redis"] == "ok"
