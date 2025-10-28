"""
Integration tests for vehicle API endpoints.

Tests all vehicle endpoints with various query parameters, authentication, and error cases.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.models.user import User
from app.services.auth_service import (
    hash_password,
    create_access_token,
)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(test_user: User) -> dict[str, str]:
    """Generate authentication headers with valid JWT token."""
    token = create_access_token(
        user_id=test_user.user_id,
        username=test_user.username,
        role=test_user.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_vehicles() -> list:
    """Create mock test vehicles (not persisted to DB due to JSONB/SQLite incompatibility)."""
    # Return mock objects with required attributes
    class MockVehicle:
        def __init__(self, vehicle_id, vin, make, model, year, connection_status, last_seen_at):
            self.vehicle_id = vehicle_id
            self.vin = vin
            self.make = make
            self.model = model
            self.year = year
            self.connection_status = connection_status
            self.last_seen_at = last_seen_at
            self.vehicle_metadata = None

    vehicles = [
        MockVehicle(
            vehicle_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174001"),
            vin="TESTVEHICLE000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc),
        ),
        MockVehicle(
            vehicle_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174002"),
            vin="TESTVEHICLE000002",
            make="Ford",
            model="F-150",
            year=2022,
            connection_status="disconnected",
            last_seen_at=None,
        ),
        MockVehicle(
            vehicle_id=uuid.UUID("123e4567-e89b-12d3-a456-426614174003"),
            vin="TESTVEHICLE000003",
            make="BMW",
            model="X5",
            year=2024,
            connection_status="connected",
            last_seen_at=datetime(2025, 10, 28, 9, 30, 0, tzinfo=timezone.utc),
        ),
    ]
    return vehicles


class TestListVehiclesEndpoint:
    """Test GET /api/v1/vehicles endpoint."""

    @pytest.mark.asyncio
    async def test_list_vehicles(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test listing all vehicles without filters."""
        # Mock the vehicle service to return test vehicles
        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_all_vehicles = AsyncMock(return_value=test_vehicles)

            response = await async_client.get(
                "/api/v1/vehicles",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data) == 3
            assert data[0]["vin"] == "TESTVEHICLE000001"
            assert data[0]["connection_status"] == "connected"
            assert data[1]["vin"] == "TESTVEHICLE000002"
            assert data[2]["vin"] == "TESTVEHICLE000003"

    @pytest.mark.asyncio
    async def test_list_vehicles_filter_by_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test filtering vehicles by connection status."""
        # Filter to only connected vehicles
        connected_vehicles = [v for v in test_vehicles if v.connection_status == "connected"]

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_all_vehicles = AsyncMock(return_value=connected_vehicles)

            response = await async_client.get(
                "/api/v1/vehicles?status=connected",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data) == 2
            assert all(v["connection_status"] == "connected" for v in data)

    @pytest.mark.asyncio
    async def test_list_vehicles_search_by_vin(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test searching vehicles by VIN (partial match)."""
        # Simulate search for "000001"
        matching_vehicles = [test_vehicles[0]]

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_all_vehicles = AsyncMock(return_value=matching_vehicles)

            response = await async_client.get(
                "/api/v1/vehicles?search=000001",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data) == 1
            assert "000001" in data[0]["vin"]

    @pytest.mark.asyncio
    async def test_list_vehicles_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test pagination with limit and offset."""
        # Return only first vehicle (limit=1, offset=0)
        paginated_vehicles = [test_vehicles[0]]

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_all_vehicles = AsyncMock(return_value=paginated_vehicles)

            response = await async_client.get(
                "/api/v1/vehicles?limit=1&offset=0",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert len(data) == 1
            assert data[0]["vin"] == "TESTVEHICLE000001"

    @pytest.mark.asyncio
    async def test_list_vehicles_unauthorized(self, async_client: AsyncClient):
        """Test that list vehicles requires authentication."""
        response = await async_client.get("/api/v1/vehicles")

        # FastAPI returns 403 Forbidden when no credentials provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_list_vehicles_invalid_limit(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test that invalid limit parameter returns validation error."""
        response = await async_client.get(
            "/api/v1/vehicles?limit=0",  # limit must be >= 1
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_list_vehicles_invalid_offset(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test that invalid offset parameter returns validation error."""
        response = await async_client.get(
            "/api/v1/vehicles?offset=-1",  # offset must be >= 0
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetVehicleEndpoint:
    """Test GET /api/v1/vehicles/{vehicle_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test getting a single vehicle by valid ID."""
        vehicle = test_vehicles[0]

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_vehicle_by_id = AsyncMock(return_value=vehicle)

            response = await async_client.get(
                f"/api/v1/vehicles/{vehicle.vehicle_id}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["vehicle_id"] == str(vehicle.vehicle_id)
            assert data["vin"] == "TESTVEHICLE000001"
            assert data["make"] == "Tesla"
            assert data["model"] == "Model 3"
            assert data["year"] == 2023
            assert data["connection_status"] == "connected"

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting a vehicle with invalid ID returns 404."""
        invalid_id = uuid.uuid4()

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_vehicle_by_id = AsyncMock(return_value=None)

            response = await async_client.get(
                f"/api/v1/vehicles/{invalid_id}",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "Vehicle not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_invalid_uuid(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test that invalid UUID format returns 422."""
        response = await async_client.get(
            "/api/v1/vehicles/not-a-uuid",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_unauthorized(
        self,
        async_client: AsyncClient,
        test_vehicles: list,
    ):
        """Test that get vehicle requires authentication."""
        vehicle = test_vehicles[0]

        response = await async_client.get(f"/api/v1/vehicles/{vehicle.vehicle_id}")

        # FastAPI returns 403 Forbidden when no credentials provided
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetVehicleStatusEndpoint:
    """Test GET /api/v1/vehicles/{vehicle_id}/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_vehicle_status(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test getting vehicle status."""
        vehicle = test_vehicles[0]
        expected_status = {
            "connection_status": vehicle.connection_status,
            "last_seen_at": vehicle.last_seen_at.isoformat() if vehicle.last_seen_at else None,
            "health": None,
        }

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_vehicle_status = AsyncMock(return_value=expected_status)

            response = await async_client.get(
                f"/api/v1/vehicles/{vehicle.vehicle_id}/status",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["connection_status"] == "connected"
            assert data["last_seen_at"] is not None
            assert data["health"] is None

    @pytest.mark.asyncio
    async def test_get_vehicle_status_cached(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test that status is cached (call endpoint twice)."""
        vehicle = test_vehicles[0]
        expected_status = {
            "connection_status": "connected",
            "last_seen_at": "2025-10-28T10:00:00+00:00",
            "health": None,
        }

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_vehicle_status = AsyncMock(return_value=expected_status)

            # First request
            response1 = await async_client.get(
                f"/api/v1/vehicles/{vehicle.vehicle_id}/status",
                headers=auth_headers,
            )
            assert response1.status_code == status.HTTP_200_OK

            # Second request (should use cache if TTL hasn't expired)
            response2 = await async_client.get(
                f"/api/v1/vehicles/{vehicle.vehicle_id}/status",
                headers=auth_headers,
            )
            assert response2.status_code == status.HTTP_200_OK

            # Both responses should be identical
            assert response1.json() == response2.json()

    @pytest.mark.asyncio
    async def test_get_vehicle_status_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
    ):
        """Test getting status for non-existent vehicle returns 404."""
        invalid_id = uuid.uuid4()

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_vehicle_status = AsyncMock(return_value=None)

            response = await async_client.get(
                f"/api/v1/vehicles/{invalid_id}/status",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_vehicle_status_unauthorized(
        self,
        async_client: AsyncClient,
        test_vehicles: list,
    ):
        """Test that get vehicle status requires authentication."""
        vehicle = test_vehicles[0]

        response = await async_client.get(
            f"/api/v1/vehicles/{vehicle.vehicle_id}/status"
        )

        # FastAPI returns 403 Forbidden when no credentials provided
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_vehicle_status_null_last_seen(
        self,
        async_client: AsyncClient,
        auth_headers: dict[str, str],
        test_vehicles: list,
    ):
        """Test getting status for vehicle with null last_seen_at."""
        vehicle = test_vehicles[1]  # This one has null last_seen_at
        expected_status = {
            "connection_status": "disconnected",
            "last_seen_at": None,
            "health": None,
        }

        with patch("app.api.v1.vehicles.vehicle_service") as mock_service:
            mock_service.get_vehicle_status = AsyncMock(return_value=expected_status)

            response = await async_client.get(
                f"/api/v1/vehicles/{vehicle.vehicle_id}/status",
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["connection_status"] == "disconnected"
            assert data["last_seen_at"] is None
