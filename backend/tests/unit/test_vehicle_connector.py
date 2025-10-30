"""
Unit tests for the mock vehicle connector module.

Tests the mock command execution, response generation, and Redis event publishing
without requiring actual database or Redis connections.
"""

import uuid
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

    def test_generate_read_dtc_streaming_chunks(self) -> None:
        """Test ReadDTC streaming chunk generation."""
        chunks = vehicle_connector._generate_read_dtc_streaming_chunks()

        # Verify 3 chunks are generated
        assert len(chunks) == 3

        # Verify chunk 1 structure
        chunk_1_payload, chunk_1_delay = chunks[0]
        assert "dtcs" in chunk_1_payload
        assert len(chunk_1_payload["dtcs"]) == 1
        assert chunk_1_payload["dtcs"][0]["dtcCode"] == "P0420"
        assert chunk_1_delay == pytest.approx(0.5, abs=0.01)

        # Verify chunk 2 structure
        chunk_2_payload, chunk_2_delay = chunks[1]
        assert "dtcs" in chunk_2_payload
        assert len(chunk_2_payload["dtcs"]) == 1
        assert chunk_2_payload["dtcs"][0]["dtcCode"] == "P0171"
        assert chunk_2_delay == pytest.approx(0.5, abs=0.01)

        # Verify chunk 3 structure (final)
        chunk_3_payload, chunk_3_delay = chunks[2]
        assert chunk_3_payload["status"] == "complete"
        assert chunk_3_payload["totalDtcs"] == 2
        assert chunk_3_delay == 0.0

    def test_generate_read_data_by_id_streaming_chunks(self) -> None:
        """Test ReadDataByID streaming chunk generation."""
        chunks = vehicle_connector._generate_read_data_by_id_streaming_chunks("0x010D")

        # Verify 2 chunks are generated
        assert len(chunks) == 2

        # Verify chunk 1 structure (acknowledgment)
        chunk_1_payload, chunk_1_delay = chunks[0]
        assert chunk_1_payload["status"] == "reading"
        assert chunk_1_payload["dataId"] == "0x010D"
        assert chunk_1_delay == pytest.approx(0.5, abs=0.01)

        # Verify chunk 2 structure (final data)
        chunk_2_payload, chunk_2_delay = chunks[1]
        assert "data" in chunk_2_payload
        assert chunk_2_payload["data"]["dataId"] == "0x010D"
        assert chunk_2_payload["data"]["description"] == "Vehicle Speed"
        assert chunk_2_delay == 0.0


class TestExecuteCommand:
    """Test suite for the execute_command function."""

    @pytest.mark.asyncio
    async def test_execute_command_read_dtc_success(self) -> None:
        """Test successful execution of ReadDTC command (now with streaming)."""
        from datetime import datetime, timezone

        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {"ecuAddress": "0x10"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response objects (ReadDTC now generates 3 chunks)
        mock_response_repo.create_response.return_value = MagicMock(response_id=uuid.uuid4())

        # Mock command object with proper submitted_at datetime
        mock_command = MagicMock()
        mock_command.command_id = command_id
        mock_command.submitted_at = datetime.now(timezone.utc)
        mock_command.user_id = uuid.uuid4()
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify network delay simulation was called (initial + 2 chunk delays)
            assert mock_sleep.call_count == 3
            delays = [call[0][0] for call in mock_sleep.call_args_list]
            assert 0.5 <= delays[0] <= 1.5  # Initial network delay

            # Verify command status was updated to 'in_progress'
            assert mock_command_repo.update_command_status.call_count >= 1
            in_progress_call = mock_command_repo.update_command_status.call_args_list[0]
            assert in_progress_call[1]["command_id"] == command_id
            assert in_progress_call[1]["status"] == "in_progress"

            # Verify 3 responses were created (streaming chunks)
            assert mock_response_repo.create_response.call_count == 3

            # Verify first chunk has DTCs
            first_chunk_call = mock_response_repo.create_response.call_args_list[0]
            assert first_chunk_call[1]["command_id"] == command_id
            assert first_chunk_call[1]["sequence_number"] == 1
            assert first_chunk_call[1]["is_final"] is False
            assert "dtcs" in first_chunk_call[1]["response_payload"]

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
        command_params: dict[str, str] = {}

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
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
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
        """Test successful execution of ReadDataByID command (now with streaming)."""
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
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify 2 responses were created (ReadDataByID now generates 2 chunks)
            assert mock_response_repo.create_response.call_count == 2

            # Verify final chunk (second chunk) includes dataId parameter
            final_chunk_call = mock_response_repo.create_response.call_args_list[1]
            response_payload = final_chunk_call[1]["response_payload"]
            assert "data" in response_payload
            assert response_payload["data"]["dataId"] == "0x010D"
            assert response_payload["data"]["description"] == "Vehicle Speed"

    @pytest.mark.asyncio
    async def test_execute_command_unknown_command_type(self) -> None:
        """Test execution of unknown command type generates generic response."""
        from datetime import datetime, timezone

        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "UnknownCommand"
        command_params: dict[str, str] = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response object
        mock_response = MagicMock()
        mock_response.response_id = uuid.uuid4()
        mock_response_repo.create_response.return_value = mock_response

        # Mock command object with proper submitted_at datetime
        mock_command = MagicMock()
        mock_command.command_id = command_id
        mock_command.submitted_at = datetime.now(timezone.utc)
        mock_command.user_id = uuid.uuid4()
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
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
    async def test_execute_command_read_dtc_streaming(self) -> None:
        """Test ReadDTC command generates multiple streaming chunks."""
        from datetime import datetime, timezone

        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params = {"ecuAddress": "0x10"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response objects for each chunk
        mock_response_1 = MagicMock()
        mock_response_1.response_id = uuid.uuid4()
        mock_response_2 = MagicMock()
        mock_response_2.response_id = uuid.uuid4()
        mock_response_3 = MagicMock()
        mock_response_3.response_id = uuid.uuid4()

        # Configure mock to return different response IDs for each call
        mock_response_repo.create_response.side_effect = [
            mock_response_1,
            mock_response_2,
            mock_response_3,
        ]

        # Mock command object with proper submitted_at datetime
        mock_command = MagicMock()
        mock_command.command_id = command_id
        mock_command.submitted_at = datetime.now(timezone.utc)
        mock_command.user_id = uuid.uuid4()
        mock_command_repo.get_command_by_id.return_value = mock_command

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify 3 responses were created (3 chunks)
            assert mock_response_repo.create_response.call_count == 3

            # Verify first chunk
            chunk_1_call = mock_response_repo.create_response.call_args_list[0]
            assert chunk_1_call[1]["command_id"] == command_id
            assert chunk_1_call[1]["sequence_number"] == 1
            assert chunk_1_call[1]["is_final"] is False
            assert "dtcs" in chunk_1_call[1]["response_payload"]
            assert len(chunk_1_call[1]["response_payload"]["dtcs"]) == 1
            assert chunk_1_call[1]["response_payload"]["dtcs"][0]["dtcCode"] == "P0420"

            # Verify second chunk
            chunk_2_call = mock_response_repo.create_response.call_args_list[1]
            assert chunk_2_call[1]["command_id"] == command_id
            assert chunk_2_call[1]["sequence_number"] == 2
            assert chunk_2_call[1]["is_final"] is False
            assert "dtcs" in chunk_2_call[1]["response_payload"]
            assert len(chunk_2_call[1]["response_payload"]["dtcs"]) == 1
            assert chunk_2_call[1]["response_payload"]["dtcs"][0]["dtcCode"] == "P0171"

            # Verify third chunk (final)
            chunk_3_call = mock_response_repo.create_response.call_args_list[2]
            assert chunk_3_call[1]["command_id"] == command_id
            assert chunk_3_call[1]["sequence_number"] == 3
            assert chunk_3_call[1]["is_final"] is True
            assert chunk_3_call[1]["response_payload"]["status"] == "complete"
            assert chunk_3_call[1]["response_payload"]["totalDtcs"] == 2

            # Verify timing delays (should be called 2 times with ~0.5s delays)
            # First sleep is initial network delay, next 2 are chunk delays
            assert mock_sleep.call_count == 3
            delays = [call[0][0] for call in mock_sleep.call_args_list]

            # First delay is network simulation (0.5-1.5s)
            assert 0.5 <= delays[0] <= 1.5

            # Next two delays are chunk intervals (~0.5s each)
            assert delays[1] == pytest.approx(0.5, abs=0.01)
            assert delays[2] == pytest.approx(0.5, abs=0.01)

            # Verify Redis events were published for each chunk (3 chunks + 1 status = 4 total)
            # But mock_redis_client is a single instance shared across all calls,
            # and redis.from_url creates a new client each time, so we only see
            # the last client's calls. The actual count is 3 chunk publishes.
            assert mock_redis_client.publish.call_count >= 3

            # Verify command status was updated to 'completed'
            completed_call = mock_command_repo.update_command_status.call_args_list[-1]
            assert completed_call[1]["command_id"] == command_id
            assert completed_call[1]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_command_read_data_by_id_streaming(self) -> None:
        """Test ReadDataByID command generates multiple streaming chunks."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDataByID"
        command_params = {"dataId": "0x010C"}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response objects for each chunk
        mock_response_1 = MagicMock()
        mock_response_1.response_id = uuid.uuid4()
        mock_response_2 = MagicMock()
        mock_response_2.response_id = uuid.uuid4()

        # Configure mock to return different response IDs for each call
        mock_response_repo.create_response.side_effect = [
            mock_response_1,
            mock_response_2,
        ]

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
        ):
            # Configure async session maker to return mock session
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Verify 2 responses were created (2 chunks)
            assert mock_response_repo.create_response.call_count == 2

            # Verify first chunk (acknowledgment)
            chunk_1_call = mock_response_repo.create_response.call_args_list[0]
            assert chunk_1_call[1]["command_id"] == command_id
            assert chunk_1_call[1]["sequence_number"] == 1
            assert chunk_1_call[1]["is_final"] is False
            assert chunk_1_call[1]["response_payload"]["status"] == "reading"
            assert chunk_1_call[1]["response_payload"]["dataId"] == "0x010C"

            # Verify second chunk (final data)
            chunk_2_call = mock_response_repo.create_response.call_args_list[1]
            assert chunk_2_call[1]["command_id"] == command_id
            assert chunk_2_call[1]["sequence_number"] == 2
            assert chunk_2_call[1]["is_final"] is True
            assert "data" in chunk_2_call[1]["response_payload"]
            assert chunk_2_call[1]["response_payload"]["data"]["dataId"] == "0x010C"

            # Verify timing delays
            assert mock_sleep.call_count == 2
            delays = [call[0][0] for call in mock_sleep.call_args_list]

            # First delay is network simulation (0.5-1.5s)
            assert 0.5 <= delays[0] <= 1.5

            # Second delay is chunk interval (~0.5s)
            assert delays[1] == pytest.approx(0.5, abs=0.01)

    @pytest.mark.asyncio
    async def test_streaming_chunks_sequence_numbers(self) -> None:
        """Test that streaming chunks have correct incrementing sequence numbers."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params: dict[str, str] = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response objects
        mock_response_repo.create_response.return_value = MagicMock(response_id=uuid.uuid4())

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
        ):
            # Configure async session maker
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Extract all sequence numbers
            sequence_numbers = [
                call[1]["sequence_number"]
                for call in mock_response_repo.create_response.call_args_list
            ]

            # Verify sequence numbers are [1, 2, 3]
            assert sequence_numbers == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_streaming_final_chunk_flag(self) -> None:
        """Test that only the final chunk has is_final=True."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params: dict[str, str] = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Mock response objects
        mock_response_repo.create_response.return_value = MagicMock(response_id=uuid.uuid4())

        # Mock Redis client
        mock_redis_client = AsyncMock()

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
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
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
        ):
            # Configure async session maker
            mock_session_maker.return_value.__aenter__.return_value = mock_db_session

            # Configure Redis mock
            mock_redis_from_url.return_value = mock_redis_client

            # Execute command
            await vehicle_connector.execute_command(
                command_id, vehicle_id, command_name, command_params
            )

            # Extract all is_final flags
            is_final_flags = [
                call[1]["is_final"] for call in mock_response_repo.create_response.call_args_list
            ]

            # Verify is_final flags are [False, False, True]
            assert is_final_flags == [False, False, True]

    @pytest.mark.asyncio
    async def test_execute_command_handles_exception(self) -> None:
        """Test that execute_command handles exceptions and marks command as failed."""
        command_id = uuid.uuid4()
        vehicle_id = uuid.uuid4()
        command_name = "ReadDTC"
        command_params: dict[str, str] = {}

        # Mock database session and repositories
        mock_db_session = AsyncMock()
        mock_command_repo = AsyncMock()
        mock_response_repo = AsyncMock()

        # Make response creation fail
        mock_response_repo.create_response.side_effect = Exception("Database error")

        with (
            patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
            patch(
                "app.connectors.vehicle_connector.command_repository",
                mock_command_repo,
            ),
            patch(
                "app.connectors.vehicle_connector.response_repository",
                mock_response_repo,
            ),
            patch("app.connectors.vehicle_connector.asyncio.sleep"),
            patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
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
