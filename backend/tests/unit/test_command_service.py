"""
Unit tests for command service.

Tests command submission, retrieval, and history with various scenarios.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.command import Command
from app.models.vehicle import Vehicle
from app.services import command_service


class TestSubmitCommand:
    """Test submit_command function."""

    @pytest.mark.asyncio
    async def test_submit_command_success(self):
        """Test successful command submission."""
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_id = uuid.uuid4()
        command_name = "lockDoors"
        command_params = {"duration": 3600}

        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_command_pending = Command(
            command_id=command_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name=command_name,
            command_params=command_params,
            status="pending",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_command_in_progress = Command(
            command_id=command_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name=command_name,
            command_params=command_params,
            status="in_progress",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.command_service.vehicle_repository") as mock_vehicle_repo:
            with patch("app.services.command_service.command_repository") as mock_cmd_repo:
                mock_vehicle_repo.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
                mock_cmd_repo.create_command = AsyncMock(return_value=mock_command_pending)
                mock_cmd_repo.update_command_status = AsyncMock(
                    return_value=mock_command_in_progress
                )

                result = await command_service.submit_command(
                    vehicle_id=vehicle_id,
                    command_name=command_name,
                    command_params=command_params,
                    user_id=user_id,
                    db_session=mock_db,
                )

                # Assertions
                assert result is not None
                assert result.command_id == command_id
                assert result.status == "in_progress"
                assert result.command_name == command_name
                assert result.vehicle_id == vehicle_id
                assert result.user_id == user_id

                # Verify repository calls
                mock_vehicle_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)
                mock_cmd_repo.create_command.assert_called_once_with(
                    db=mock_db,
                    user_id=user_id,
                    vehicle_id=vehicle_id,
                    command_name=command_name,
                    command_params=command_params,
                )
                mock_cmd_repo.update_command_status.assert_called_once_with(
                    db=mock_db, command_id=command_id, status="in_progress"
                )

    @pytest.mark.asyncio
    async def test_submit_command_vehicle_not_found(self):
        """Test command submission with invalid vehicle ID."""
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_name = "lockDoors"
        command_params = {}

        mock_db = MagicMock()

        with patch("app.services.command_service.vehicle_repository") as mock_vehicle_repo:
            with patch("app.services.command_service.command_repository") as mock_cmd_repo:
                mock_vehicle_repo.get_vehicle_by_id = AsyncMock(return_value=None)

                result = await command_service.submit_command(
                    vehicle_id=vehicle_id,
                    command_name=command_name,
                    command_params=command_params,
                    user_id=user_id,
                    db_session=mock_db,
                )

                # Assertions
                assert result is None
                mock_vehicle_repo.get_vehicle_by_id.assert_called_once_with(mock_db, vehicle_id)
                mock_cmd_repo.create_command.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_command_empty_params(self):
        """Test command submission with empty parameters."""
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        command_id = uuid.uuid4()
        command_name = "getStatus"
        command_params = {}

        mock_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            vin="TESTVIN000001",
            make="Tesla",
            model="Model 3",
            year=2023,
            connection_status="connected",
            last_seen_at=datetime.now(timezone.utc),
        )

        mock_command_pending = Command(
            command_id=command_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name=command_name,
            command_params=command_params,
            status="pending",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_command_in_progress = Command(
            command_id=command_id,
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name=command_name,
            command_params=command_params,
            status="in_progress",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.command_service.vehicle_repository") as mock_vehicle_repo:
            with patch("app.services.command_service.command_repository") as mock_cmd_repo:
                mock_vehicle_repo.get_vehicle_by_id = AsyncMock(return_value=mock_vehicle)
                mock_cmd_repo.create_command = AsyncMock(return_value=mock_command_pending)
                mock_cmd_repo.update_command_status = AsyncMock(
                    return_value=mock_command_in_progress
                )

                result = await command_service.submit_command(
                    vehicle_id=vehicle_id,
                    command_name=command_name,
                    command_params=command_params,
                    user_id=user_id,
                    db_session=mock_db,
                )

                # Assertions
                assert result is not None
                assert result.command_params == {}


class TestGetCommandById:
    """Test get_command_by_id function."""

    @pytest.mark.asyncio
    async def test_get_command_by_id_found(self):
        """Test getting a command by valid ID."""
        command_id = uuid.uuid4()
        mock_command = Command(
            command_id=command_id,
            user_id=uuid.uuid4(),
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={"duration": 3600},
            status="completed",
            submitted_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_command_by_id = AsyncMock(return_value=mock_command)

            result = await command_service.get_command_by_id(command_id, mock_db)

            assert result is not None
            assert result.command_id == command_id
            assert result.status == "completed"
            mock_repo.get_command_by_id.assert_called_once_with(mock_db, command_id)

    @pytest.mark.asyncio
    async def test_get_command_by_id_not_found(self):
        """Test getting a command by invalid ID returns None."""
        command_id = uuid.uuid4()
        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_command_by_id = AsyncMock(return_value=None)

            result = await command_service.get_command_by_id(command_id, mock_db)

            assert result is None
            mock_repo.get_command_by_id.assert_called_once_with(mock_db, command_id)


class TestGetCommandHistory:
    """Test get_command_history function with various filters."""

    @pytest.mark.asyncio
    async def test_get_command_history_no_filters(self):
        """Test getting command history without filters."""
        mock_commands = [
            Command(
                command_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                vehicle_id=uuid.uuid4(),
                command_name="lockDoors",
                command_params={},
                status="completed",
                submitted_at=datetime.now(timezone.utc),
            ),
            Command(
                command_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                vehicle_id=uuid.uuid4(),
                command_name="unlockDoors",
                command_params={},
                status="in_progress",
                submitted_at=datetime.now(timezone.utc),
            ),
        ]

        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_commands = AsyncMock(return_value=mock_commands)

            result = await command_service.get_command_history(
                filters={"limit": 50, "offset": 0}, db_session=mock_db
            )

            assert len(result) == 2
            mock_repo.get_commands.assert_called_once_with(
                db=mock_db,
                vehicle_id=None,
                user_id=None,
                status=None,
                limit=50,
                offset=0,
            )

    @pytest.mark.asyncio
    async def test_get_command_history_with_vehicle_filter(self):
        """Test filtering commands by vehicle ID."""
        vehicle_id = uuid.uuid4()
        mock_command = Command(
            command_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            vehicle_id=vehicle_id,
            command_name="lockDoors",
            command_params={},
            status="completed",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_commands = AsyncMock(return_value=[mock_command])

            result = await command_service.get_command_history(
                filters={"vehicle_id": vehicle_id, "limit": 50, "offset": 0},
                db_session=mock_db,
            )

            assert len(result) == 1
            assert result[0].vehicle_id == vehicle_id
            mock_repo.get_commands.assert_called_once_with(
                db=mock_db,
                vehicle_id=vehicle_id,
                user_id=None,
                status=None,
                limit=50,
                offset=0,
            )

    @pytest.mark.asyncio
    async def test_get_command_history_with_status_filter(self):
        """Test filtering commands by status."""
        mock_command = Command(
            command_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={},
            status="completed",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_commands = AsyncMock(return_value=[mock_command])

            result = await command_service.get_command_history(
                filters={"status": "completed", "limit": 50, "offset": 0},
                db_session=mock_db,
            )

            assert len(result) == 1
            assert result[0].status == "completed"
            mock_repo.get_commands.assert_called_once_with(
                db=mock_db,
                vehicle_id=None,
                user_id=None,
                status="completed",
                limit=50,
                offset=0,
            )

    @pytest.mark.asyncio
    async def test_get_command_history_with_user_filter(self):
        """Test filtering commands by user ID."""
        user_id = uuid.uuid4()
        mock_command = Command(
            command_id=uuid.uuid4(),
            user_id=user_id,
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={},
            status="completed",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_commands = AsyncMock(return_value=[mock_command])

            result = await command_service.get_command_history(
                filters={"user_id": user_id, "limit": 50, "offset": 0},
                db_session=mock_db,
            )

            assert len(result) == 1
            assert result[0].user_id == user_id

    @pytest.mark.asyncio
    async def test_get_command_history_with_pagination(self):
        """Test pagination with limit and offset."""
        mock_commands = [
            Command(
                command_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                vehicle_id=uuid.uuid4(),
                command_name=f"command_{i}",
                command_params={},
                status="completed",
                submitted_at=datetime.now(timezone.utc),
            )
            for i in range(10)
        ]

        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_commands = AsyncMock(return_value=mock_commands)

            result = await command_service.get_command_history(
                filters={"limit": 10, "offset": 5}, db_session=mock_db
            )

            assert len(result) == 10
            mock_repo.get_commands.assert_called_once_with(
                db=mock_db,
                vehicle_id=None,
                user_id=None,
                status=None,
                limit=10,
                offset=5,
            )

    @pytest.mark.asyncio
    async def test_get_command_history_empty_result(self):
        """Test command history with no results."""
        mock_db = MagicMock()

        with patch("app.services.command_service.command_repository") as mock_repo:
            mock_repo.get_commands = AsyncMock(return_value=[])

            result = await command_service.get_command_history(
                filters={"limit": 50, "offset": 0}, db_session=mock_db
            )

            assert len(result) == 0
