"""
Unit tests for command repository.

Tests command repository functions with database mocks.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.command import Command
from app.repositories import command_repository


class TestCreateCommand:
    """Test create_command function."""

    @pytest.mark.asyncio
    async def test_create_command_success(self):
        """Test successful command creation."""
        user_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "lockDoors"
        command_params = {"duration": 3600}

        mock_db = AsyncMock(spec=AsyncSession)

        # Create a mock command with a generated ID
        mock_command = Command(
            command_id=uuid.uuid4(),
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name=command_name,
            command_params=command_params,
            status="pending",
            submitted_at=datetime.now(timezone.utc),
        )

        # Mock the session methods
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch("app.repositories.command_repository.Command", return_value=mock_command):
            result = await command_repository.create_command(
                db=mock_db,
                user_id=user_id,
                vehicle_id=vehicle_id,
                command_name=command_name,
                command_params=command_params,
            )

            # Assertions
            assert result is not None
            assert result.user_id == user_id
            assert result.vehicle_id == vehicle_id
            assert result.command_name == command_name
            assert result.command_params == command_params
            assert result.status == "pending"

            # Verify database operations
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()


class TestGetCommandById:
    """Test get_command_by_id function."""

    @pytest.mark.asyncio
    async def test_get_command_by_id_found(self):
        """Test retrieving a command by ID when it exists."""
        command_id = uuid.uuid4()
        mock_command = Command(
            command_id=command_id,
            user_id=uuid.uuid4(),
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={},
            status="completed",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_command
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_command_by_id(mock_db, command_id)

        assert result is not None
        assert result.command_id == command_id
        assert result.command_name == "lockDoors"
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_command_by_id_not_found(self):
        """Test retrieving a command by ID when it doesn't exist."""
        command_id = uuid.uuid4()

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_command_by_id(mock_db, command_id)

        assert result is None
        mock_db.execute.assert_called_once()


class TestUpdateCommandStatus:
    """Test update_command_status function."""

    @pytest.mark.asyncio
    async def test_update_command_status_success(self):
        """Test successfully updating command status."""
        command_id = uuid.uuid4()
        mock_command = Command(
            command_id=command_id,
            user_id=uuid.uuid4(),
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={},
            status="pending",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "app.repositories.command_repository.get_command_by_id",
            return_value=mock_command,
        ) as mock_get:
            result = await command_repository.update_command_status(
                db=mock_db, command_id=command_id, status="completed"
            )

            assert result is not None
            assert result.status == "completed"
            mock_get.assert_called_once_with(mock_db, command_id)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_command_status_with_error_message(self):
        """Test updating command status with error message."""
        command_id = uuid.uuid4()
        error_message = "Vehicle not responding"
        mock_command = Command(
            command_id=command_id,
            user_id=uuid.uuid4(),
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={},
            status="in_progress",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "app.repositories.command_repository.get_command_by_id",
            return_value=mock_command,
        ) as mock_get:
            result = await command_repository.update_command_status(
                db=mock_db,
                command_id=command_id,
                status="failed",
                error_message=error_message,
            )

            assert result is not None
            assert result.status == "failed"
            assert result.error_message == error_message
            mock_get.assert_called_once_with(mock_db, command_id)

    @pytest.mark.asyncio
    async def test_update_command_status_with_completed_at(self):
        """Test updating command status with completion timestamp."""
        command_id = uuid.uuid4()
        completed_at = datetime.now(timezone.utc)
        mock_command = Command(
            command_id=command_id,
            user_id=uuid.uuid4(),
            vehicle_id=uuid.uuid4(),
            command_name="lockDoors",
            command_params={},
            status="in_progress",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        with patch(
            "app.repositories.command_repository.get_command_by_id",
            return_value=mock_command,
        ):
            result = await command_repository.update_command_status(
                db=mock_db,
                command_id=command_id,
                status="completed",
                completed_at=completed_at,
            )

            assert result is not None
            assert result.status == "completed"
            assert result.completed_at == completed_at

    @pytest.mark.asyncio
    async def test_update_command_status_command_not_found(self):
        """Test updating command status when command doesn't exist."""
        command_id = uuid.uuid4()

        mock_db = AsyncMock(spec=AsyncSession)

        with patch(
            "app.repositories.command_repository.get_command_by_id", return_value=None
        ):
            result = await command_repository.update_command_status(
                db=mock_db, command_id=command_id, status="completed"
            )

            assert result is None
            mock_db.commit.assert_not_called()


class TestGetCommands:
    """Test get_commands function with various filters."""

    @pytest.mark.asyncio
    async def test_get_commands_no_filters(self):
        """Test getting commands without any filters."""
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
                status="pending",
                submitted_at=datetime.now(timezone.utc),
            ),
        ]

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_commands
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(db=mock_db)

        assert len(result) == 2
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_commands_filter_by_vehicle_id(self):
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_command]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(db=mock_db, vehicle_id=vehicle_id)

        assert len(result) == 1
        assert result[0].vehicle_id == vehicle_id
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_commands_filter_by_user_id(self):
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_command]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(db=mock_db, user_id=user_id)

        assert len(result) == 1
        assert result[0].user_id == user_id

    @pytest.mark.asyncio
    async def test_get_commands_filter_by_status(self):
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_command]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(db=mock_db, status="completed")

        assert len(result) == 1
        assert result[0].status == "completed"

    @pytest.mark.asyncio
    async def test_get_commands_with_pagination(self):
        """Test getting commands with pagination."""
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

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = mock_commands
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(db=mock_db, limit=10, offset=5)

        assert len(result) == 10
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_commands_with_all_filters(self):
        """Test getting commands with all filters combined."""
        vehicle_id = uuid.uuid4()
        user_id = uuid.uuid4()
        mock_command = Command(
            command_id=uuid.uuid4(),
            user_id=user_id,
            vehicle_id=vehicle_id,
            command_name="lockDoors",
            command_params={},
            status="completed",
            submitted_at=datetime.now(timezone.utc),
        )

        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_command]
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(
            db=mock_db,
            vehicle_id=vehicle_id,
            user_id=user_id,
            status="completed",
            limit=20,
            offset=0,
        )

        assert len(result) == 1
        assert result[0].vehicle_id == vehicle_id
        assert result[0].user_id == user_id
        assert result[0].status == "completed"

    @pytest.mark.asyncio
    async def test_get_commands_empty_result(self):
        """Test getting commands with no results."""
        mock_db = AsyncMock(spec=AsyncSession)
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await command_repository.get_commands(db=mock_db)

        assert len(result) == 0
        mock_db.execute.assert_called_once()
