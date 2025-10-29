"""
Unit tests for the mock vehicle connector module.

Tests the mock command execution, response generation, and Redis event publishing
without requiring actual database or Redis connections.
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.connectors import vehicle_connector


class TestMockResponseGenerators:
    """Test suite for mock response generator functions."""

    def test_generate_read_dtc_response(self) -> None:
        """Test ReadDTC mock response generation."""
        response = vehicle_connector._generate_read_dtc_response()

        assert "dtcs" in response
        assert isinstance(response["dtcs"], list)
        assert len(response["dtcs"]) > 0

        # Verify DTC structure
        dtc = response["dtcs"][0]
        assert "dtcCode" in dtc
        assert "description" in dtc
        assert "status" in dtc
        assert "ecuAddress" in dtc

        # Verify timestamp
        assert "timestamp" in response
        assert "ecuAddress" in response

    def test_generate_clear_dtc_response(self) -> None:
        """Test ClearDTC mock response generation."""
        response = vehicle_connector._generate_clear_dtc_response()

        assert response["status"] == "success"
        assert "message" in response
        assert "clearedCount" in response
        assert isinstance(response["clearedCount"], int)
        assert "ecuAddress" in response
        assert "timestamp" in response

    def test_generate_read_data_by_id_response_with_known_id(self) -> None:
        """Test ReadDataByID mock response with known data identifier."""
        # Test Engine RPM (0x010C)
        response = vehicle_connector._generate_read_data_by_id_response("0x010C")

        assert "data" in response
        assert response["data"]["dataId"] == "0x010C"
        assert response["data"]["description"] == "Engine RPM"
        assert "value" in response["data"]
        assert response["data"]["unit"] == "rpm"
        assert "ecuAddress" in response
        assert "timestamp" in response

    def test_generate_read_data_by_id_response_with_unknown_id(self) -> None:
        """Test ReadDataByID mock response with unknown data identifier."""
        response = vehicle_connector._generate_read_data_by_id_response("0xFFFF")

        assert "data" in response
        assert response["data"]["dataId"] == "0xFFFF"
        assert response["data"]["description"] == "Unknown Data Identifier"
        assert response["data"]["value"] == "N/A"

    def test_generate_read_data_by_id_response_default(self) -> None:
        """Test ReadDataByID mock response with no data identifier (default)."""
        response = vehicle_connector._generate_read_data_by_id_response()

        assert "data" in response
        assert response["data"]["dataId"] == "0x010C"  # Default

    def test_mock_response_generators_mapping(self) -> None:
        """Test that all expected commands are mapped to generators."""
        assert "ReadDTC" in vehicle_connector.MOCK_RESPONSE_GENERATORS
        assert "ClearDTC" in vehicle_connector.MOCK_RESPONSE_GENERATORS
        assert "ReadDataByID" in vehicle_connector.MOCK_RESPONSE_GENERATORS

        # Verify generators are callable
        assert callable(vehicle_connector.MOCK_RESPONSE_GENERATORS["ReadDTC"])
        assert callable(vehicle_connector.MOCK_RESPONSE_GENERATORS["ClearDTC"])
        assert callable(vehicle_connector.MOCK_RESPONSE_GENERATORS["ReadDataByID"])


class TestExecuteCommand:
    """Test suite for the execute_command function."""

    @pytest.mark.asyncio
    async def test_execute_command_read_dtc_success(self) -> None:
        """Test successful execution of ReadDTC command."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {"ecuAddress": "0x10"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response object
        mock_response = MagicMock()
        mock_response.response_id = uuid.uuid4()
        mock_response_repo.create_response.return_value = mock_response

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch(
                "app.connectors.vehicle_connector.async_session_maker"
            ) as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis_from_url,
            patch("app.connectors.vehicle_connector.asyncio.sleep") as mock_sleep,
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify network delay simulation was called
            mock_sleep.assert_called_once()
            delay = mock_sleep.call_args[0][0]
            assert 0.5 <= delay <= 1.5

            # Verify command status was updated to 'in_progress'
            assert mock_command_repo.update_command_status.call_count >= 1
            in_progress_call = mock_command_repo.update_command_status.call_args_list[0]
            assert in_progress_call[1]["command_id"] == command_id
            assert in_progress_call[1]["status"] == "in_progress"

            # Verify response was created
            mock_response_repo.create_response.assert_called_once()
            create_response_call = mock_response_repo.create_response.call_args[1]
            assert create_response_call["command_id"] == command_id
            assert create_response_call["sequence_number"] == 1
            assert create_response_call["is_final"] is True
            assert "dtcs" in create_response_call["response_payload"]

            # Verify Redis event was published
            mock_redis_client.publish.assert_called_once()
            publish_call = mock_redis_client.publish.call_args[0]
            assert publish_call[0] == f"response:{command_id}"

            # Verify event data structure
            event_data = json.loads(publish_call[1])
            assert event_data["event"] == "response"
            assert event_data["command_id"] == str(command_id)
            assert event_data["response_id"] == str(mock_response.response_id)
            assert event_data["sequence_number"] == 1
            assert event_data["is_final"] is True

            # Verify Redis client was closed
            mock_redis_client.aclose.assert_called_once()

            # Verify command status was updated to 'completed'
            completed_call = mock_command_repo.update_command_status.call_args_list[-1]
            assert completed_call[1]["command_id"] == command_id
            assert completed_call[1]["status"] == "completed"
            assert "completed_at" in completed_call[1]

    @pytest.mark.asyncio
    async def test_execute_command_clear_dtc_success(self) -> None:
        """Test successful execution of ClearDTC command."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ClearDTC"
        command_params = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response object
        mock_response = MagicMock()
        mock_response.response_id = uuid.uuid4()
        mock_response_repo.create_response.return_value = mock_response

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch(
                "app.connectors.vehicle_connector.async_session_maker"
            ) as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis_from_url,
            patch("app.connectors.vehicle_connector.asyncio.sleep"),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify response payload matches ClearDTC structure
            mock_response_repo.create_response.assert_called_once()
            create_response_call = mock_response_repo.create_response.call_args[1]
            response_payload = create_response_call["response_payload"]
            assert response_payload["status"] == "success"
            assert "clearedCount" in response_payload

    @pytest.mark.asyncio
    async def test_execute_command_read_data_by_id_success(self) -> None:
        """Test successful execution of ReadDataByID command with data identifier."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDataByID"
        command_params = {"dataId": "0x010D"}  # Vehicle Speed

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response object
        mock_response = MagicMock()
        mock_response.response_id = uuid.uuid4()
        mock_response_repo.create_response.return_value = mock_response

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch(
                "app.connectors.vehicle_connector.async_session_maker"
            ) as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis_from_url,
            patch("app.connectors.vehicle_connector.asyncio.sleep"),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify response payload includes dataId parameter
            mock_response_repo.create_response.assert_called_once()
            create_response_call = mock_response_repo.create_response.call_args[1]
            response_payload = create_response_call["response_payload"]
            assert "data" in response_payload
            assert response_payload["data"]["dataId"] == "0x010D"
            assert response_payload["data"]["description"] == "Vehicle Speed"

    @pytest.mark.asyncio
    async def test_execute_command_unknown_command_type(self) -> None:
        """Test execution of unknown command type generates generic response."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "UnknownCommand"
        command_params = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response object
        mock_response = MagicMock()
        mock_response.response_id = uuid.uuid4()
        mock_response_repo.create_response.return_value = mock_response

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch(
                "app.connectors.vehicle_connector.async_session_maker"
            ) as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis_from_url,
            patch("app.connectors.vehicle_connector.asyncio.sleep"),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify generic response was created
            mock_response_repo.create_response.assert_called_once()
            create_response_call = mock_response_repo.create_response.call_args[1]
            response_payload = create_response_call["response_payload"]
            assert response_payload["status"] == "success"
            assert "UnknownCommand" in response_payload["message"]

            # Verify command still completed successfully
            completed_call = mock_command_repo.update_command_status.call_args_list[-1]
            assert completed_call[1]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_command_handles_exception(self) -> None:
        """Test that execute_command handles exceptions and marks command as failed."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Make response creation fail
        mock_response_repo.create_response.side_effect = Exception("Database error")

        with (
            patch(
                "app.connectors.vehicle_connector.async_session_maker"
            ) as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch("app.connectors.vehicle_connector.asyncio.sleep"),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Execute command (should not raise exception)
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify command status was updated to 'failed'
            failed_call = mock_command_repo.update_command_status.call_args_list[-1]
            assert failed_call[1]["command_id"] == command_id
            assert failed_call[1]["status"] == "failed"
            assert "error_message" in failed_call[1]
            assert "Database error" in failed_call[1]["error_message"]
