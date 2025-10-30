"""
Integration tests for command history API endpoint with RBAC and filtering.

Tests the GET /api/v1/commands endpoint with pagination, filtering, and role-based access control.
Uses mocked service layer to avoid database table incompatibility (SQLite vs PostgreSQL).
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
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


@pytest.fixture
def mock_vehicle_ids():
    """Create mock vehicle IDs for testing."""
    return {
        "vehicle1": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "vehicle2": uuid.UUID("22222222-2222-2222-2222-222222222222"),
    }


@pytest.fixture
def create_mock_commands(test_engineer1: User, test_engineer2: User, mock_vehicle_ids):
    """Factory function to create mock command objects."""

    class MockCommand:
        """Mock Command object that behaves like an ORM model."""

        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    def _create_commands():
        now = datetime.now(timezone.utc)
        return [
            # Engineer1's commands
            MockCommand(
                command_id=uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
                user_id=test_engineer1.user_id,
                vehicle_id=mock_vehicle_ids["vehicle1"],
                command_name="lockDoors",
                command_params={"duration": 3600},
                status="completed",
                error_message=None,
                submitted_at=now - timedelta(days=5),
                completed_at=now - timedelta(days=5, seconds=-10),
            ),
            MockCommand(
                command_id=uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
                user_id=test_engineer1.user_id,
                vehicle_id=mock_vehicle_ids["vehicle1"],
                command_name="getStatus",
                command_params={},
                status="in_progress",
                error_message=None,
                submitted_at=now - timedelta(days=3),
                completed_at=None,
            ),
            MockCommand(
                command_id=uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
                user_id=test_engineer1.user_id,
                vehicle_id=mock_vehicle_ids["vehicle2"],
                command_name="unlockDoors",
                command_params={},
                status="pending",
                error_message=None,
                submitted_at=now - timedelta(days=1),
                completed_at=None,
            ),
            # Engineer2's commands
            MockCommand(
                command_id=uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
                user_id=test_engineer2.user_id,
                vehicle_id=mock_vehicle_ids["vehicle1"],
                command_name="startEngine",
                command_params={"warm_up": True},
                status="failed",
                error_message="Vehicle not responding",
                submitted_at=now - timedelta(days=4),
                completed_at=now - timedelta(days=4, seconds=-5),
            ),
            MockCommand(
                command_id=uuid.UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
                user_id=test_engineer2.user_id,
                vehicle_id=mock_vehicle_ids["vehicle2"],
                command_name="readDTC",
                command_params={},
                status="completed",
                error_message=None,
                submitted_at=now - timedelta(days=2),
                completed_at=now - timedelta(days=2, seconds=-8),
            ),
        ]

    return _create_commands


class TestCommandHistoryRBAC:
    """Test role-based access control for command history."""

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_engineer_sees_only_own_commands(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        engineer1_auth_headers: dict[str, str],
        test_engineer1: User,
        create_mock_commands,
    ):
        """Test that engineers can only see their own commands."""
        all_commands = create_mock_commands()
        # Filter to only engineer1's commands
        engineer1_commands = [cmd for cmd in all_commands if cmd.user_id == test_engineer1.user_id]

        mock_get_history.return_value = engineer1_commands

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

        # Verify the service was called with engineer1's user_id filter (RBAC enforcement)
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"]["user_id"] == test_engineer1.user_id

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_admin_sees_all_commands(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test that admins can see all commands from all users."""
        all_commands = create_mock_commands()
        mock_get_history.return_value = all_commands

        response = await async_client.get(
            "/api/v1/commands",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Admin should see all 5 commands
        assert len(data["commands"]) == 5

        # Verify the service was called without user_id filter (admins see all)
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"].get("user_id") is None

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_admin_can_filter_by_user(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        test_engineer2: User,
        create_mock_commands,
    ):
        """Test that admins can filter commands by user_id."""
        all_commands = create_mock_commands()
        # Filter to only engineer2's commands
        engineer2_commands = [cmd for cmd in all_commands if cmd.user_id == test_engineer2.user_id]

        mock_get_history.return_value = engineer2_commands

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

        # Verify the service was called with engineer2's user_id filter
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"]["user_id"] == test_engineer2.user_id


class TestCommandHistoryFiltering:
    """Test filtering functionality for command history."""

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_filter_by_vehicle(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        mock_vehicle_ids,
        create_mock_commands,
    ):
        """Test filtering commands by vehicle_id."""
        all_commands = create_mock_commands()
        # Filter to only vehicle1's commands
        vehicle1_commands = [
            cmd for cmd in all_commands if cmd.vehicle_id == mock_vehicle_ids["vehicle1"]
        ]

        mock_get_history.return_value = vehicle1_commands

        response = await async_client.get(
            f"/api/v1/commands?vehicle_id={mock_vehicle_ids['vehicle1']}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see 2 commands for vehicle1
        assert len(data["commands"]) == 2

        for cmd in data["commands"]:
            assert cmd["vehicle_id"] == str(mock_vehicle_ids["vehicle1"])

        # Verify the service was called with vehicle_id filter
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"]["vehicle_id"] == mock_vehicle_ids["vehicle1"]

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_filter_by_status(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test filtering commands by status."""
        all_commands = create_mock_commands()
        # Filter to only completed commands
        completed_commands = [cmd for cmd in all_commands if cmd.status == "completed"]

        mock_get_history.return_value = completed_commands

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

        # Verify the service was called with status filter
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"]["status"] == "completed"

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_filter_by_date_range(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test filtering commands by date range."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=3)
        end_date = now

        all_commands = create_mock_commands()
        # Filter to only commands in the date range (last 3 days)
        filtered_commands = [
            cmd
            for cmd in all_commands
            if start_date
            <= datetime.fromisoformat(cmd.submitted_at.isoformat().replace("Z", "+00:00"))
            <= end_date
        ]

        mock_get_history.return_value = filtered_commands

        response = await async_client.get(
            f"/api/v1/commands?start_date={start_date.isoformat()}&end_date={end_date.isoformat()}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see commands from last 3 days (3 commands)
        assert len(data["commands"]) == 3

        # Verify the service was called with date filters
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"]["start_date"] is not None
        assert call_kwargs["filters"]["end_date"] is not None

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_filter_start_date_only(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test filtering with only start_date."""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=2)

        all_commands = create_mock_commands()
        # Filter to only commands after start_date
        filtered_commands = [
            cmd
            for cmd in all_commands
            if datetime.fromisoformat(cmd.submitted_at.isoformat().replace("Z", "+00:00"))
            >= start_date
        ]

        mock_get_history.return_value = filtered_commands

        response = await async_client.get(
            f"/api/v1/commands?start_date={start_date.isoformat()}",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see commands from last 2 days (2 commands)
        assert len(data["commands"]) == 2

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_filter_end_date_only(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test filtering with only end_date."""
        now = datetime.now(timezone.utc)
        end_date = now - timedelta(days=3)

        all_commands = create_mock_commands()
        # Filter to only commands before end_date
        filtered_commands = [
            cmd
            for cmd in all_commands
            if datetime.fromisoformat(cmd.submitted_at.isoformat().replace("Z", "+00:00"))
            <= end_date
        ]

        mock_get_history.return_value = filtered_commands

        response = await async_client.get(
            f"/api/v1/commands?end_date={end_date.isoformat()}",
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
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_combined_filters(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        engineer1_auth_headers: dict[str, str],
        test_engineer1: User,
        mock_vehicle_ids,
        create_mock_commands,
    ):
        """Test combining multiple filters."""
        all_commands = create_mock_commands()
        # Filter to engineer1's completed commands on vehicle1
        filtered_commands = [
            cmd
            for cmd in all_commands
            if cmd.user_id == test_engineer1.user_id
            and cmd.vehicle_id == mock_vehicle_ids["vehicle1"]
            and cmd.status == "completed"
        ]

        mock_get_history.return_value = filtered_commands

        response = await async_client.get(
            f"/api/v1/commands?vehicle_id={mock_vehicle_ids['vehicle1']}&status=completed",
            headers=engineer1_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should see 1 command (engineer1's completed command on vehicle1)
        assert len(data["commands"]) == 1
        assert data["commands"][0]["status"] == "completed"
        assert data["commands"][0]["vehicle_id"] == str(mock_vehicle_ids["vehicle1"])


class TestCommandHistoryPagination:
    """Test pagination functionality for command history."""

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_pagination_first_page(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test getting first page of results."""
        all_commands = create_mock_commands()
        # Return only first 2 commands
        mock_get_history.return_value = (all_commands[:2], len(all_commands))

        response = await async_client.get(
            "/api/v1/commands?limit=2&offset=0",
            headers=admin_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["commands"]) == 2
        assert data["limit"] == 2
        assert data["offset"] == 0

        # Verify pagination parameters were passed
        assert mock_get_history.called
        call_kwargs = mock_get_history.call_args[1]
        assert call_kwargs["filters"]["limit"] == 2
        assert call_kwargs["filters"]["offset"] == 0

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_pagination_second_page(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test getting second page of results."""
        all_commands = create_mock_commands()
        # Return commands 3-4 (offset=2, limit=2)
        mock_get_history.return_value = (all_commands[2:4], len(all_commands))

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
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_pagination_last_page(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test getting last page with fewer results."""
        all_commands = create_mock_commands()
        # Return last 2 commands (offset=3 means start from 4th item)
        mock_get_history.return_value = (all_commands[3:], len(all_commands))

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
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_pagination_with_filters(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        engineer1_auth_headers: dict[str, str],
        test_engineer1: User,
        create_mock_commands,
    ):
        """Test pagination combined with filtering."""
        all_commands = create_mock_commands()
        # Filter to engineer1's commands (3 total), return first 2
        engineer1_commands = [cmd for cmd in all_commands if cmd.user_id == test_engineer1.user_id]
        mock_get_history.return_value = engineer1_commands[:2]

        response = await async_client.get(
            "/api/v1/commands?limit=2&offset=0",
            headers=engineer1_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Engineer1 has 3 commands, should see first 2
        assert len(data["commands"]) == 2

    @pytest.mark.asyncio
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_commands_ordered_by_submitted_at_desc(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
        create_mock_commands,
    ):
        """Test that commands are ordered by submitted_at descending (newest first)."""
        all_commands = create_mock_commands()
        # Sort by submitted_at descending (newest first)
        sorted_commands = sorted(
            all_commands, key=lambda x: x.submitted_at, reverse=True
        )

        mock_get_history.return_value = sorted_commands

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
    @patch("app.api.v1.commands.command_service.get_command_history")
    async def test_no_commands_found(
        self,
        mock_get_history: AsyncMock,
        async_client: AsyncClient,
        admin_auth_headers: dict[str, str],
    ):
        """Test response when no commands match filters."""
        mock_get_history.return_value = ([], 0)

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
