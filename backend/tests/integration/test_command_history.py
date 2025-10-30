"""
Integration tests for command history API endpoint with RBAC and filtering.

Tests the GET /api/v1/commands endpoint with pagination, filtering, and role-based access control.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.command import Command
from app.models.user import User
from app.models.vehicle import Vehicle
from app.services.auth_service import create_access_token, hash_password


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        username="testadmin",
        email="admin@example.com",
        password_hash=hash_password("testpassword"),
        role="admin",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_engineer1(db_session: AsyncSession) -> User:
    """Create first test engineer user."""
    user = User(
        username="engineer1",
        email="engineer1@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_engineer2(db_session: AsyncSession) -> User:
    """Create second test engineer user."""
    user = User(
        username="engineer2",
        email="engineer2@example.com",
        password_hash=hash_password("testpassword"),
        role="engineer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_vehicle1(db_session: AsyncSession) -> Vehicle:
    """Create first test vehicle."""
    vehicle = Vehicle(
        vehicle_id=uuid.uuid4(),
        vin="1HGBH41JXMN109186",
        make="Honda",
        model="Accord",
        year=2023,
        connection_status="connected",
    )
    db_session.add(vehicle)
    await db_session.commit()
    await db_session.refresh(vehicle)
    return vehicle


@pytest_asyncio.fixture
async def test_vehicle2(db_session: AsyncSession) -> Vehicle:
    """Create second test vehicle."""
    vehicle = Vehicle(
        vehicle_id=uuid.uuid4(),
        vin="1HGBH41JXMN109187",
        make="Toyota",
        model="Camry",
        year=2023,
        connection_status="connected",
    )
    db_session.add(vehicle)
    await db_session.commit()
    await db_session.refresh(vehicle)
    return vehicle


@pytest_asyncio.fixture
async def admin_auth_headers(test_admin: User) -> dict[str, str]:
    """Generate authentication headers for admin user."""
    token = create_access_token(
        user_id=test_admin.user_id,
        username=test_admin.username,
        role=test_admin.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def engineer1_auth_headers(test_engineer1: User) -> dict[str, str]:
    """Generate authentication headers for engineer1."""
    token = create_access_token(
        user_id=test_engineer1.user_id,
        username=test_engineer1.username,
        role=test_engineer1.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def engineer2_auth_headers(test_engineer2: User) -> dict[str, str]:
    """Generate authentication headers for engineer2."""
    token = create_access_token(
        user_id=test_engineer2.user_id,
        username=test_engineer2.username,
        role=test_engineer2.role,
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def sample_commands(
    db_session: AsyncSession,
    test_engineer1: User,
    test_engineer2: User,
    test_vehicle1: Vehicle,
    test_vehicle2: Vehicle,
) -> list[Command]:
    """Create sample commands for testing."""
    now = datetime.now(timezone.utc)

    commands = [
        # Engineer1's commands
        Command(
            command_id=uuid.uuid4(),
            user_id=test_engineer1.user_id,
            vehicle_id=test_vehicle1.vehicle_id,
            command_name="lockDoors",
            command_params={"duration": 3600},
            status="completed",
            submitted_at=now - timedelta(days=5),
        ),
        Command(
            command_id=uuid.uuid4(),
            user_id=test_engineer1.user_id,
            vehicle_id=test_vehicle1.vehicle_id,
            command_name="getStatus",
            command_params={},
            status="in_progress",
            submitted_at=now - timedelta(days=3),
        ),
        Command(
            command_id=uuid.uuid4(),
            user_id=test_engineer1.user_id,
            vehicle_id=test_vehicle2.vehicle_id,
            command_name="unlockDoors",
            command_params={},
            status="pending",
            submitted_at=now - timedelta(days=1),
        ),
        # Engineer2's commands
        Command(
            command_id=uuid.uuid4(),
            user_id=test_engineer2.user_id,
            vehicle_id=test_vehicle1.vehicle_id,
            command_name="startEngine",
            command_params={"warm_up": True},
            status="failed",
            error_message="Vehicle not responding",
            submitted_at=now - timedelta(days=4),
        ),
        Command(
            command_id=uuid.uuid4(),
            user_id=test_engineer2.user_id,
            vehicle_id=test_vehicle2.vehicle_id,
            command_name="readDTC",
            command_params={},
            status="completed",
            submitted_at=now - timedelta(days=2),
        ),
    ]

    for cmd in commands:
        db_session.add(cmd)

    await db_session.commit()

    for cmd in commands:
        await db_session.refresh(cmd)

    return commands


class TestCommandHistoryRBAC:
    """Test role-based access control for command history."""

    @pytest.mark.asyncio
    async def test_engineer_sees_only_own_commands(
        self,
        async_client: AsyncClient,
        engineer1_auth_headers: dict[str, str],
        sample_commands: list[Command],
        test_engineer1: User,
    ):
        """Test that engineers can only see their own commands."""
        response = await async_client.get(
            "/api/v1/commands",
            headers=engineer1_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Engineer1 should only see their 3 commands
        assert len(data["commands"]) == 3

        # Verify all commands belong to engineer1
        for cmd in data["commands"]:
            assert cmd["user_id"] == str(test_engineer1.user_id)

    @pytest.mark.asyncio
    async def test_admin_sees_all_commands(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test that admins can see all commands from all users."""
        response = await async_client.get(
            "/api/v1/commands",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Admin should see all 5 commands
        assert len(data["commands"]) == 5

    @pytest.mark.asyncio
    async def test_admin_can_filter_by_user(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
        test_engineer2: User,
    ):
        """Test that admins can filter commands by user_id."""
        response = await async_client.get(
            f"/api/v1/commands?user_id={test_engineer2.user_id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only see engineer2's commands
        assert len(data["commands"]) == 2

        for cmd in data["commands"]:
            assert cmd["user_id"] == str(test_engineer2.user_id)


class TestCommandHistoryFiltering:
    """Test filtering functionality for command history."""

    @pytest.mark.asyncio
    async def test_filter_by_vehicle(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
        test_vehicle1: Vehicle,
    ):
        """Test filtering commands by vehicle_id."""
        response = await async_client.get(
            f"/api/v1/commands?vehicle_id={test_vehicle1.vehicle_id}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see 2 commands for vehicle1
        assert len(data["commands"]) == 2

        for cmd in data["commands"]:
            assert cmd["vehicle_id"] == str(test_vehicle1.vehicle_id)

    @pytest.mark.asyncio
    async def test_filter_by_status(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test filtering commands by status."""
        response = await async_client.get(
            "/api/v1/commands?status=completed",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see 2 completed commands
        assert len(data["commands"]) == 2

        for cmd in data["commands"]:
            assert cmd["status"] == "completed"

    @pytest.mark.asyncio
    async def test_filter_by_date_range(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test filtering commands by date range."""
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=3)).isoformat()
        end_date = now.isoformat()

        response = await async_client.get(
            f"/api/v1/commands?start_date={start_date}&end_date={end_date}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see commands from last 3 days (3 commands)
        assert len(data["commands"]) == 3

    @pytest.mark.asyncio
    async def test_filter_start_date_only(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test filtering with only start_date."""
        now = datetime.now(timezone.utc)
        start_date = (now - timedelta(days=2)).isoformat()

        response = await async_client.get(
            f"/api/v1/commands?start_date={start_date}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see commands from last 2 days (2 commands)
        assert len(data["commands"]) == 2

    @pytest.mark.asyncio
    async def test_filter_end_date_only(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test filtering with only end_date."""
        now = datetime.now(timezone.utc)
        end_date = (now - timedelta(days=3)).isoformat()

        response = await async_client.get(
            f"/api/v1/commands?end_date={end_date}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see commands older than 3 days (2 commands)
        assert len(data["commands"]) == 2

    @pytest.mark.asyncio
    async def test_invalid_date_format(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ):
        """Test that invalid date format returns 400 error."""
        response = await async_client.get(
            "/api/v1/commands?start_date=invalid-date",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_combined_filters(
        self,
        async_client: AsyncClient,
        engineer1_auth_headers: dict[str, str],
        sample_commands: list[Command],
        test_vehicle1: Vehicle,
    ):
        """Test combining multiple filters."""
        response = await async_client.get(
            f"/api/v1/commands?vehicle_id={test_vehicle1.vehicle_id}&status=completed",
            headers=engineer1_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see 1 command (engineer1's completed command on vehicle1)
        assert len(data["commands"]) == 1
        assert data["commands"][0]["status"] == "completed"
        assert data["commands"][0]["vehicle_id"] == str(test_vehicle1.vehicle_id)


class TestCommandHistoryPagination:
    """Test pagination functionality for command history."""

    @pytest.mark.asyncio
    async def test_pagination_first_page(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test getting first page of results."""
        response = await async_client.get(
            "/api/v1/commands?limit=2&offset=0",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["commands"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

    @pytest.mark.asyncio
    async def test_pagination_second_page(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test getting second page of results."""
        response = await async_client.get(
            "/api/v1/commands?limit=2&offset=2",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["commands"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 2

    @pytest.mark.asyncio
    async def test_pagination_last_page(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test getting last page with fewer results."""
        response = await async_client.get(
            "/api/v1/commands?limit=3&offset=3",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["commands"]) == 2  # Only 2 commands left
        assert data["limit"] == 3
        assert data["offset"] == 3

    @pytest.mark.asyncio
    async def test_pagination_with_filters(
        self,
        async_client: AsyncClient,
        engineer1_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test pagination combined with filtering."""
        response = await async_client.get(
            "/api/v1/commands?limit=2&offset=0",
            headers=engineer1_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Engineer1 has 3 commands, should see first 2
        assert len(data["commands"]) == 2

    @pytest.mark.asyncio
    async def test_commands_ordered_by_submitted_at_desc(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        sample_commands: list[Command],
    ):
        """Test that commands are ordered by submitted_at descending (newest first)."""
        response = await async_client.get(
            "/api/v1/commands",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify commands are in descending order by submitted_at
        submitted_dates = [cmd["submitted_at"] for cmd in data["commands"]]
        assert submitted_dates == sorted(submitted_dates, reverse=True)


class TestCommandHistoryEdgeCases:
    """Test edge cases for command history."""

    @pytest.mark.asyncio
    async def test_no_commands_found(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ):
        """Test response when no commands match filters."""
        response = await async_client.get(
            "/api/v1/commands?status=nonexistent",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["commands"]) == 0

    @pytest.mark.asyncio
    async def test_unauthorized_request(
        self,
        async_client: AsyncClient,
    ):
        """Test that unauthorized requests are rejected."""
        response = await async_client.get("/api/v1/commands")

        assert response.status_code == status.HTTP_403_FORBIDDEN
