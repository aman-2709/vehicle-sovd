"""
Unit tests for vehicle repository.

Tests vehicle repository functions with database mocks.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle
from app.repositories import vehicle_repository


class TestGetAllVehicles:
    """Test get_all_vehicles function."""

    @pytest.mark.asyncio
    async def test_get_all_vehicles_no_filters(self):
        """Test getting all vehicles without filters."""
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
                make="BMW",
                model="i4",
                year=2023,
                connection_status="disconnected",
                last_seen_at=datetime.now(timezone.utc),
            ),
        ]

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_vehicles
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_all_vehicles(db=mock_db)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_vehicles_filter_by_status(self):
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_vehicle]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_all_vehicles(
            db=mock_db, status_filter="connected"
        )

        assert len(result) == 1
        assert result[0].connection_status == "connected"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_vehicles_search_by_vin(self):
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_vehicle]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_all_vehicles(db=mock_db, search_term="TEST")

        assert len(result) == 1
        assert "TEST" in result[0].vin
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_vehicles_with_pagination(self):
        """Test getting vehicles with pagination."""
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_vehicles
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_all_vehicles(db=mock_db, limit=10, offset=5)

        assert len(result) == 10
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_vehicles_with_all_filters(self):
        """Test getting vehicles with all filters combined."""
        mock_vehicle = Vehicle(
            vehicle_id=uuid.uuid4(),
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_vehicle]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_all_vehicles(
            db=mock_db,
            status_filter="connected",
            search_term="TEST",
            limit=20,
            offset=0,
        )

        assert len(result) == 1
        assert result[0].connection_status == "connected"
        assert "TEST" in result[0].vin

    @pytest.mark.asyncio
    async def test_get_all_vehicles_empty_result(self):
        """Test getting vehicles with no results."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_all_vehicles(db=mock_db)

        assert len(result) == 0
        mock_db.execute.assert_called_once()


class TestGetVehicleById:
    """Test get_vehicle_by_id function."""

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_found(self):
        """Test retrieving a vehicle by ID when it exists."""
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_vehicle
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_vehicle_by_id(mock_db, vehicle_id)

        assert result is not None
        assert result.vehicle_id == vehicle_id
        assert result.vin == "TESTVIN000001"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vehicle_by_id_not_found(self):
        """Test retrieving a vehicle by ID when it doesn't exist."""
        vehicle_id = uuid.uuid4()

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_vehicle_by_id(mock_db, vehicle_id)

        assert result is None
        mock_db.execute.assert_called_once()


class TestGetVehicleByVin:
    """Test get_vehicle_by_vin function."""

    @pytest.mark.asyncio
    async def test_get_vehicle_by_vin_found(self):
        """Test retrieving a vehicle by VIN when it exists."""
        vin = "TESTVIN000001"
        mock_vehicle = Vehicle(
            vehicle_id=uuid.uuid4(),
            vin=vin,
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_vehicle
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_vehicle_by_vin(mock_db, vin)

        assert result is not None
        assert result.vin == vin
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_vehicle_by_vin_not_found(self):
        """Test retrieving a vehicle by VIN when it doesn't exist."""
        vin = "NONEXISTENT"

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.get_vehicle_by_vin(mock_db, vin)

        assert result is None
        mock_db.execute.assert_called_once()


class TestUpdateVehicleStatus:
    """Test update_vehicle_status function."""

    @pytest.mark.asyncio
    async def test_update_vehicle_status_success(self):
        """Test successfully updating vehicle status."""
        vehicle_id = uuid.uuid4()
        new_status = "connected"
        new_timestamp = datetime.now(timezone.utc)

        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="disconnected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock get_vehicle_by_id to return the vehicle
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_vehicle
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.update_vehicle_status(
            db=mock_db,
            vehicle_id=vehicle_id,
            connection_status=new_status,
            last_seen_at=new_timestamp,
        )

        assert result is not None
        assert result.connection_status == new_status
        assert result.last_seen_at == new_timestamp
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_vehicle_status_not_found(self):
        """Test updating vehicle status when vehicle doesn't exist."""
        vehicle_id = uuid.uuid4()
        new_status = "connected"
        new_timestamp = datetime.now(timezone.utc)

        mock_db = AsyncMock(spec=AsyncSession)

        # Mock get_vehicle_by_id to return None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await vehicle_repository.update_vehicle_status(
            db=mock_db,
            vehicle_id=vehicle_id,
            connection_status=new_status,
            last_seen_at=new_timestamp,
        )

        assert result is None
        mock_db.commit.assert_not_called()
