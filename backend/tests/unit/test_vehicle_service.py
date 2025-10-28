"""
Unit tests for vehicle service.

Tests vehicle retrieval, filtering, pagination, and Redis caching behavior.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

import pytest
import redis.asyncio as aioredis

from app.models.vehicle import Vehicle
from app.services import vehicle_service


class TestGetAllVehicles:
    """Test get_all_vehicles function with various filters."""

    @pytest.mark.asyncio
    async def test_get_all_vehicles_no_filters(self):
        """Test getting all vehicles without any filters."""
        # Create mock vehicles
        mock_vehicles = [
            Vehicle(
                vehicle_id=uuid.uuid4(),
                vin="TESTVIN000001",
                make="Tesla",
                model="Model 3",
                year=2023,
                connection_status="connected",
                last_seen_at=datetime.now(timezone.utc),
            ),
            Vehicle(
                vehicle_id=uuid.uuid4(),
                vin="TESTVIN000002",
                make="Ford",
                model="F-150",
                year=2022,
                connection_status="disconnected",
                last_seen_at=None,
            ),
        ]

        # Mock database session
        mock_db = MagicMock()

        # Mock repository function
        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_all_vehicles = AsyncMock(return_value=mock_vehicles)

            # Call service function
            result = await vehicle_service.get_all_vehicles(
                db=mock_db,
                filters={},
                limit=50,
                offset=0,
            )

            # Assertions
            assert len(result) == 2
            assert result[0].vin == "TESTVIN000001"
            assert result[1].vin == "TESTVIN000002"
            mock_repo.get_all_vehicles.assert_called_once_with(
                db=mock_db,
                status_filter=None,
                search_term=None,
                limit=50,
                offset=0,
            )

    @pytest.mark.asyncio
    async def test_get_all_vehicles_with_status_filter(self):
        """Test filtering vehicles by connection status."""
        mock_vehicle = Vehicle(
            vehicle_id=uuid.uuid4(),
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_all_vehicles = AsyncMock(return_value=[mock_vehicle])

            result = await vehicle_service.get_all_vehicles(
                db=mock_db,
                filters={"status": "connected"},
                limit=50,
                offset=0,
            )

            assert len(result) == 1
            assert result[0].connection_status == "connected"
            mock_repo.get_all_vehicles.assert_called_once_with(
                db=mock_db,
                status_filter="connected",
                search_term=None,
                limit=50,
                offset=0,
            )

    @pytest.mark.asyncio
    async def test_get_all_vehicles_with_search(self):
        """Test searching vehicles by VIN (partial match)."""
        mock_vehicle = Vehicle(
            vehicle_id=uuid.uuid4(),
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_all_vehicles = AsyncMock(return_value=[mock_vehicle])

            result = await vehicle_service.get_all_vehicles(
                db=mock_db,
                filters={"search": "TESTVIN"},
                limit=50,
                offset=0,
            )

            assert len(result) == 1
            assert "TESTVIN" in result[0].vin
            mock_repo.get_all_vehicles.assert_called_once_with(
                db=mock_db,
                status_filter=None,
                search_term="TESTVIN",
                limit=50,
                offset=0,
            )

    @pytest.mark.asyncio
    async def test_get_all_vehicles_with_pagination(self):
        """Test pagination with limit and offset."""
        mock_vehicles = [
            Vehicle(
                vehicle_id=uuid.uuid4(),
                vin=f"TESTVIN00000{i}",
                make="Tesla",
                model="Model 3",
                year=2023,
                connection_status="connected",
                last_seen_at=datetime.now(timezone.utc),
            )
            for i in range(10)
        ]

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_all_vehicles = AsyncMock(return_value=mock_vehicles)

            result = await vehicle_service.get_all_vehicles(
                db=mock_db,
                filters={},
                limit=10,
                offset=5,
            )

            assert len(result) == 10
            mock_repo.get_all_vehicles.assert_called_once_with(
                db=mock_db,
                status_filter=None,
                search_term=None,
                limit=10,
                offset=5,
            )


class TestGetVehicleById:
    """Test get_vehicle_by_id function."""

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_found(self):
        """Test getting a vehicle by valid ID."""
        vehicle_id = uuid.uuid4()
        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)

            result = await vehicle_service.get_vehicle_by_id(mock_db, vehicle_id)

            assert result is not None
            assert result.vehicle_id == vehicle_id
            assert result.vin == "TESTVIN000001"
            mock_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_not_found(self):
        """Test getting a vehicle by invalid ID returns None."""
        vehicle_id = uuid.uuid4()
        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_vehicle_by_id = AsyncMock(return_value=None)

            result = await vehicle_service.get_vehicle_by_id(mock_db, vehicle_id)

            assert result is None
            mock_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)


class TestGetVehicleStatus:
    """Test get_vehicle_status function with Redis caching."""

    @pytest.mark.asyncio
    @patch("app.services.vehicle_service.redis_client")
    async def test_get_vehicle_status_cache_hit(self, mock_redis):
        """Test that cached status is returned from Redis."""
        vehicle_id = uuid.uuid4()
        cached_status = {
            "connection_status": "connected",
            "last_seen_at": "2025-10-28T10:00:00Z",
            "health": None,
        }

        # Mock Redis to return cached data
        mock_redis.get = AsyncMock(return_value=json.dumps(cached_status))

        mock_db = MagicMock()

        result = await vehicle_service.get_vehicle_status(mock_db, vehicle_id)

        # Assertions
        assert result is not None
        assert result["connection_status"] == "connected"
        assert result["last_seen_at"] == "2025-10-28T10:00:00Z"
        mock_redis.get.assert_called_once_with(f"vehicle_status:{vehicle_id}")

    @pytest.mark.asyncio
    @patch("app.services.vehicle_service.redis_client")
    async def test_get_vehicle_status_cache_miss(self, mock_redis):
        """Test that status is fetched from DB on cache miss."""
        vehicle_id = uuid.uuid4()
        last_seen = datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc)
        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=last_seen,
        )

        # Mock Redis to return None (cache miss)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)

            result = await vehicle_service.get_vehicle_status(mock_db, vehicle_id)

            # Assertions
            assert result is not None
            assert result["connection_status"] == "connected"
            assert result["last_seen_at"] == last_seen.isoformat()
            mock_redis.get.assert_called_once()
            mock_redis.setex.assert_called_once()
            # Verify cache key and TTL
            call_args = mock_redis.setex.call_args
            assert call_args[0][0] == f"vehicle_status:{vehicle_id}"
            assert call_args[0][1] == 30  # TTL
            mock_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)

    @pytest.mark.asyncio
    @patch("app.services.vehicle_service.redis_client")
    async def test_get_vehicle_status_redis_error(self, mock_redis):
        """Test that service falls back to DB when Redis fails."""
        vehicle_id = uuid.uuid4()
        last_seen = datetime(2025, 10, 28, 10, 0, 0, tzinfo=timezone.utc)
        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=last_seen,
        )

        # Mock Redis to raise an error
        mock_redis.get = AsyncMock(side_effect=aioredis.RedisError("Connection failed"))
        mock_redis.setex = AsyncMock(side_effect=aioredis.RedisError("Connection failed"))

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)

            result = await vehicle_service.get_vehicle_status(mock_db, vehicle_id)

            # Should still return data from database
            assert result is not None
            assert result["connection_status"] == "connected"
            assert result["last_seen_at"] == last_seen.isoformat()
            mock_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)

    @pytest.mark.asyncio
    @patch("app.services.vehicle_service.redis_client")
    async def test_get_vehicle_status_not_found(self, mock_redis):
        """Test that None is returned when vehicle doesn't exist."""
        vehicle_id = uuid.uuid4()

        # Mock Redis cache miss
        mock_redis.get = AsyncMock(return_value=None)

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_vehicle_by_id = AsyncMock(return_value=None)

            result = await vehicle_service.get_vehicle_status(mock_db, vehicle_id)

            assert result is None
            mock_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)

    @pytest.mark.asyncio
    @patch("app.services.vehicle_service.redis_client")
    async def test_get_vehicle_status_null_last_seen(self, mock_redis):
        """Test handling of vehicle with null last_seen_at."""
        vehicle_id = uuid.uuid4()
        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="disconnected",
            last_seen_at=None,  # Null last_seen_at
        )

        # Mock Redis cache miss
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        mock_db = MagicMock()

        with patch("app.services.vehicle_service.vehicle_repository") as mock_repo:
            mock_repo.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)

            result = await vehicle_service.get_vehicle_status(mock_db, vehicle_id)

            # Assertions
            assert result is not None
            assert result["connection_status"] == "disconnected"
            assert result["last_seen_at"] is None
            mock_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)
