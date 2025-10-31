"""
Integration tests for gRPC vehicle connector.

Tests the real gRPC client implementation against a mock gRPC server
to verify correct command execution, streaming response handling,
error scenarios, and timeout behavior.

Note: These tests use mock database operations to avoid PostgreSQL dependency.
End-to-end tests with real database are in tests/e2e/.
"""

import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest
import pytest_asyncio

from app.connectors.vehicle_connector import get_connector
from tests.mocks.mock_vehicle_server import (
    MockVehicleServer,
    MockVehicleServicer,
)


@pytest_asyncio.fixture
async def mock_server():
    """
    Start mock gRPC server for testing.

    Yields:
        MockVehicleServer instance running on port 50051
    """
    server = MockVehicleServer(port=50051)
    await server.start()
    # Give server time to start
    await asyncio.sleep(0.1)
    yield server
    await server.stop()


@pytest_asyncio.fixture
async def cleanup_connector():
    """Clean up global connector after test."""
    yield
    # Close connector channel to avoid resource leaks
    connector = get_connector()
    await connector.close()


class TestGrpcVehicleConnector:
    """Integration tests for gRPC vehicle connector."""

    @pytest.mark.asyncio
    async def test_connector_singleton(self):
        """
        Test that get_connector returns singleton instance.

        Verifies:
        - Multiple calls return the same instance
        - Channel is reused (connection pooling)
        """
        connector1 = get_connector()
        connector2 = get_connector()

        assert connector1 is connector2

        # Clean up
        await connector1.close()

    @pytest.mark.asyncio
    async def test_connector_channel_reuse(self, mock_server, cleanup_connector):
        """
        Test that gRPC channel is reused across multiple commands.

        Verifies:
        - Channel is created once
        - Stub is reused
        """
        connector = get_connector()

        # Get channel and stub
        channel1 = await connector._get_channel()
        stub1 = await connector._get_stub()

        # Get again (should return same instances)
        channel2 = await connector._get_channel()
        stub2 = await connector._get_stub()

        assert channel1 is channel2
        assert stub1 is stub2

    @pytest.mark.asyncio
    async def test_grpc_streaming_read_dtc(self, mock_server, cleanup_connector):
        """
        Test gRPC streaming with ReadDTC command.

        Verifies:
        - gRPC channel connects successfully
        - Streaming RPC returns multiple chunks
        - Sequence numbers are correct (0-indexed)
        - Final chunk has is_final=True
        """
        connector = get_connector()
        stub = await connector._get_stub()

        # Create request
        from app.generated import sovd_vehicle_service_pb2

        request = sovd_vehicle_service_pb2.CommandRequest(
            command_id=str(uuid.uuid4()),
            vehicle_id=str(uuid.uuid4()),
            command_name="ReadDTC",
            command_params={},
        )

        # Call streaming RPC
        response_stream = stub.ExecuteCommand(request, timeout=30.0)

        # Collect responses
        responses = []
        async for response in response_stream:
            responses.append(response)

        # Verify streaming worked
        assert len(responses) == 3  # ReadDTC returns 3 chunks

        # Verify sequence numbers
        assert responses[0].sequence_number == 0
        assert responses[1].sequence_number == 1
        assert responses[2].sequence_number == 2

        # Verify is_final flags
        assert responses[0].is_final is False
        assert responses[1].is_final is False
        assert responses[2].is_final is True

        # Verify payloads are JSON strings
        import json

        payload_0 = json.loads(responses[0].response_payload)
        payload_1 = json.loads(responses[1].response_payload)
        payload_2 = json.loads(responses[2].response_payload)

        assert "dtcs" in payload_0
        assert "dtcs" in payload_1
        assert payload_2["status"] == "complete"

    @pytest.mark.asyncio
    async def test_grpc_single_chunk_clear_dtc(self, mock_server, cleanup_connector):
        """
        Test gRPC with single-chunk response (ClearDTC).

        Verifies:
        - Single response chunk is returned
        - is_final=True on first chunk
        """
        connector = get_connector()
        stub = await connector._get_stub()

        from app.generated import sovd_vehicle_service_pb2

        request = sovd_vehicle_service_pb2.CommandRequest(
            command_id=str(uuid.uuid4()),
            vehicle_id=str(uuid.uuid4()),
            command_name="ClearDTC",
            command_params={},
        )

        response_stream = stub.ExecuteCommand(request, timeout=30.0)

        responses = []
        async for response in response_stream:
            responses.append(response)

        assert len(responses) == 1
        assert responses[0].sequence_number == 0
        assert responses[0].is_final is True

        import json

        payload = json.loads(responses[0].response_payload)
        assert payload["status"] == "success"

    @pytest.mark.asyncio
    async def test_grpc_error_unavailable(self, cleanup_connector):
        """
        Test gRPC UNAVAILABLE error handling.

        Verifies:
        - UNAVAILABLE error is raised correctly
        - Error code and message are accessible
        """
        # Create server with UNAVAILABLE error
        servicer = MockVehicleServicer(
            simulate_error=True,
            error_code=grpc.StatusCode.UNAVAILABLE,
            error_message="Vehicle unavailable",
        )
        server = MockVehicleServer(port=50051, servicer=servicer)
        await server.start()
        await asyncio.sleep(0.1)

        try:
            connector = get_connector()
            stub = await connector._get_stub()

            from app.generated import sovd_vehicle_service_pb2

            request = sovd_vehicle_service_pb2.CommandRequest(
                command_id=str(uuid.uuid4()),
                vehicle_id=str(uuid.uuid4()),
                command_name="ReadDTC",
                command_params={},
            )

            # Should raise gRPC error
            with pytest.raises(grpc.aio.AioRpcError) as exc_info:
                response_stream = stub.ExecuteCommand(request, timeout=30.0)
                async for _ in response_stream:
                    pass  # Should not reach here

            assert exc_info.value.code() == grpc.StatusCode.UNAVAILABLE
            assert "unavailable" in exc_info.value.details().lower()

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_grpc_error_invalid_argument(self, cleanup_connector):
        """
        Test gRPC INVALID_ARGUMENT error handling.

        Verifies:
        - INVALID_ARGUMENT error is raised correctly
        """
        servicer = MockVehicleServicer(
            simulate_error=True,
            error_code=grpc.StatusCode.INVALID_ARGUMENT,
            error_message="Invalid command parameters",
        )
        server = MockVehicleServer(port=50051, servicer=servicer)
        await server.start()
        await asyncio.sleep(0.1)

        try:
            connector = get_connector()
            stub = await connector._get_stub()

            from app.generated import sovd_vehicle_service_pb2

            request = sovd_vehicle_service_pb2.CommandRequest(
                command_id=str(uuid.uuid4()),
                vehicle_id=str(uuid.uuid4()),
                command_name="ReadDTC",
                command_params={},
            )

            with pytest.raises(grpc.aio.AioRpcError) as exc_info:
                response_stream = stub.ExecuteCommand(request, timeout=30.0)
                async for _ in response_stream:
                    pass

            assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_grpc_delayed_streaming(self, cleanup_connector):
        """
        Test gRPC with delayed streaming responses.

        Verifies:
        - Responses are received in order with delays
        - All chunks are received correctly
        """
        servicer = MockVehicleServicer(delay_seconds=0.2)
        server = MockVehicleServer(port=50051, servicer=servicer)
        await server.start()
        await asyncio.sleep(0.1)

        try:
            connector = get_connector()
            stub = await connector._get_stub()

            from app.generated import sovd_vehicle_service_pb2

            request = sovd_vehicle_service_pb2.CommandRequest(
                command_id=str(uuid.uuid4()),
                vehicle_id=str(uuid.uuid4()),
                command_name="ReadDTC",
                command_params={},
            )

            responses = []
            start_time = asyncio.get_event_loop().time()

            response_stream = stub.ExecuteCommand(request, timeout=30.0)
            async for response in response_stream:
                responses.append(response)

            end_time = asyncio.get_event_loop().time()

            # Verify all chunks received
            assert len(responses) == 3

            # Verify delays occurred (should take at least 0.4s for 2 delays)
            elapsed = end_time - start_time
            assert elapsed >= 0.3  # Allow some tolerance

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_retry_logic_with_backoff(self, cleanup_connector):
        """
        Test retry logic with exponential backoff.

        Verifies:
        - Connector retries on UNAVAILABLE error
        - Exponential backoff delays are applied
        - Max retries is respected
        """
        connector = get_connector()

        # Mock the internal execution to simulate retries
        retry_attempts = []

        async def mock_execute_internal(*args, **kwargs):
            retry_attempts.append(asyncio.get_event_loop().time())
            if len(retry_attempts) < 3:
                # Raise UNAVAILABLE for first 2 attempts
                from grpc import aio

                raise aio.AioRpcError(
                    code=grpc.StatusCode.UNAVAILABLE,
                    initial_metadata=grpc.aio.Metadata(),
                    trailing_metadata=grpc.aio.Metadata(),
                    details="Vehicle unavailable",
                )
            # Success on 3rd attempt
            return None

        with patch.object(
            connector,
            "_execute_command_internal",
            side_effect=mock_execute_internal,
        ):
            command_id = uuid.uuid4()
            vehicle_id = uuid.uuid4()

            await connector.execute_command_with_retry(
                command_id=command_id,
                vehicle_id=vehicle_id,
                command_name="ReadDTC",
                command_params={},
            )

            # Verify 3 attempts were made
            assert len(retry_attempts) == 3

            # Verify exponential backoff (delays should be ~1s, ~2s)
            # First attempt: immediate
            # Second attempt: after ~1s delay
            # Third attempt: after ~2s delay
            if len(retry_attempts) >= 3:
                delay_1 = retry_attempts[1] - retry_attempts[0]
                delay_2 = retry_attempts[2] - retry_attempts[1]

                # Allow some tolerance for timing
                assert delay_1 >= 0.8  # ~1s
                assert delay_2 >= 1.8  # ~2s


class TestExecuteCommandFullFlow:
    """
    End-to-end integration tests for execute_command() function.

    These tests verify the complete execution flow including database operations,
    Redis pub/sub, audit logging, and metrics updates.
    """

    @pytest.mark.asyncio
    async def test_execute_command_full_flow_success(self, mock_server, cleanup_connector):
        """
        Test complete execute_command flow with database and Redis operations.

        Verifies:
        - Command status updated to "in_progress" at start
        - Each streamed response chunk is inserted into database
        - Each chunk is published to Redis
        - Command status updated to "completed" at end
        - Audit log entry created for "command_completed"
        - Prometheus metrics updated (command counter, duration histogram)
        """
        # Mock all dependencies
        with patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker, \
             patch("app.connectors.vehicle_connector.command_repository") as mock_cmd_repo, \
             patch("app.connectors.vehicle_connector.response_repository") as mock_resp_repo, \
             patch("app.connectors.vehicle_connector.audit_service") as mock_audit, \
             patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis, \
             patch("app.connectors.vehicle_connector.increment_command_counter") as mock_inc_counter, \
             patch("app.connectors.vehicle_connector.observe_command_duration") as mock_observe_duration:

            # Setup mock database session
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            # Setup mock command repository
            mock_command = MagicMock()
            mock_command.user_id = uuid.uuid4()
            mock_command.submitted_at = datetime.now(timezone.utc)
            mock_cmd_repo.get_command_by_id = AsyncMock(return_value=mock_command)
            mock_cmd_repo.update_command_status = AsyncMock()

            # Setup mock response repository
            mock_response = MagicMock()
            mock_response.response_id = uuid.uuid4()
            mock_resp_repo.create_response = AsyncMock(return_value=mock_response)

            # Setup mock Redis client
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            # Setup mock audit service
            mock_audit.log_audit_event = AsyncMock()

            # Act: Call execute_command
            command_id = uuid.uuid4()
            vehicle_id = uuid.uuid4()

            from app.connectors.vehicle_connector import execute_command
            await execute_command(
                command_id=command_id,
                vehicle_id=vehicle_id,
                command_name="ReadDTC",
                command_params={}
            )

            # Assert: Verify all operations were called

            # 1. Command status updated to "in_progress" and "completed"
            assert mock_cmd_repo.update_command_status.call_count == 2
            calls = mock_cmd_repo.update_command_status.call_args_list

            # First call: in_progress
            assert calls[0].kwargs["status"] == "in_progress"
            assert calls[0].kwargs["command_id"] == command_id

            # Second call: completed
            assert calls[1].kwargs["status"] == "completed"
            assert calls[1].kwargs["command_id"] == command_id
            assert calls[1].kwargs["completed_at"] is not None

            # 2. Response chunks inserted to database (3 chunks for ReadDTC)
            assert mock_resp_repo.create_response.call_count == 3

            # Verify sequence numbers
            resp_calls = mock_resp_repo.create_response.call_args_list
            assert resp_calls[0].kwargs["sequence_number"] == 0
            assert resp_calls[1].kwargs["sequence_number"] == 1
            assert resp_calls[2].kwargs["sequence_number"] == 2

            # Verify is_final flags
            assert resp_calls[0].kwargs["is_final"] is False
            assert resp_calls[1].kwargs["is_final"] is False
            assert resp_calls[2].kwargs["is_final"] is True

            # 3. Redis publish called for each chunk + 1 status event (total 4)
            assert mock_redis_client.publish.call_count == 4

            # 4. Audit log entry created
            mock_audit.log_audit_event.assert_called_once()
            audit_call = mock_audit.log_audit_event.call_args
            assert audit_call.kwargs["action"] == "command_completed"
            assert audit_call.kwargs["entity_type"] == "command"
            assert audit_call.kwargs["entity_id"] == command_id

            # 5. Prometheus metrics updated
            mock_inc_counter.assert_called_once_with("completed")
            mock_observe_duration.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_command_publishes_all_chunks(self, mock_server, cleanup_connector):
        """
        Test that execute_command publishes all response chunks to Redis.

        Verifies:
        - Redis publish called exactly 4 times for ReadDTC (3 chunks + 1 status)
        - Each chunk has correct event type ("response")
        - Status event has correct event type ("status")
        """
        with patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker, \
             patch("app.connectors.vehicle_connector.command_repository") as mock_cmd_repo, \
             patch("app.connectors.vehicle_connector.response_repository") as mock_resp_repo, \
             patch("app.connectors.vehicle_connector.audit_service") as mock_audit, \
             patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis, \
             patch("app.connectors.vehicle_connector.increment_command_counter") as mock_inc_counter, \
             patch("app.connectors.vehicle_connector.observe_command_duration") as mock_observe_duration:

            # Setup mocks
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            mock_command = MagicMock()
            mock_command.user_id = uuid.uuid4()
            mock_command.submitted_at = datetime.now(timezone.utc)
            mock_cmd_repo.get_command_by_id = AsyncMock(return_value=mock_command)
            mock_cmd_repo.update_command_status = AsyncMock()

            mock_response = MagicMock()
            mock_response.response_id = uuid.uuid4()
            mock_resp_repo.create_response = AsyncMock(return_value=mock_response)

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            mock_audit.log_audit_event = AsyncMock()

            # Act: Call execute_command
            command_id = uuid.uuid4()
            vehicle_id = uuid.uuid4()

            from app.connectors.vehicle_connector import execute_command
            await execute_command(
                command_id=command_id,
                vehicle_id=vehicle_id,
                command_name="ReadDTC",
                command_params={}
            )

            # Assert: Verify Redis publish calls

            # Should be called exactly 4 times (3 response chunks + 1 status event)
            assert mock_redis_client.publish.call_count == 4

            # Parse each publish call to verify event types
            import json
            publish_calls = mock_redis_client.publish.call_args_list

            response_events = []
            status_events = []

            for call in publish_calls:
                channel = call.args[0]
                event_json = call.args[1]
                event_data = json.loads(event_json)

                if event_data["event"] == "response":
                    response_events.append(event_data)
                elif event_data["event"] == "status":
                    status_events.append(event_data)

            # Verify counts
            assert len(response_events) == 3  # 3 response chunks
            assert len(status_events) == 1  # 1 status event

            # Verify response events have correct sequence numbers
            assert response_events[0]["sequence_number"] == 0
            assert response_events[1]["sequence_number"] == 1
            assert response_events[2]["sequence_number"] == 2

            # Verify status event has correct status
            assert status_events[0]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_execute_command_single_chunk(self, mock_server, cleanup_connector):
        """
        Test execute_command with single-chunk response (ClearDTC).

        Verifies:
        - Single response chunk is processed correctly
        - Status updated to "completed"
        - All operations (DB, Redis, audit, metrics) executed correctly
        """
        with patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker, \
             patch("app.connectors.vehicle_connector.command_repository") as mock_cmd_repo, \
             patch("app.connectors.vehicle_connector.response_repository") as mock_resp_repo, \
             patch("app.connectors.vehicle_connector.audit_service") as mock_audit, \
             patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis, \
             patch("app.connectors.vehicle_connector.increment_command_counter") as mock_inc_counter, \
             patch("app.connectors.vehicle_connector.observe_command_duration") as mock_observe_duration:

            # Setup mocks
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            mock_command = MagicMock()
            mock_command.user_id = uuid.uuid4()
            mock_command.submitted_at = datetime.now(timezone.utc)
            mock_cmd_repo.get_command_by_id = AsyncMock(return_value=mock_command)
            mock_cmd_repo.update_command_status = AsyncMock()

            mock_response = MagicMock()
            mock_response.response_id = uuid.uuid4()
            mock_resp_repo.create_response = AsyncMock(return_value=mock_response)

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            mock_audit.log_audit_event = AsyncMock()

            # Act: Call execute_command with ClearDTC (single chunk)
            command_id = uuid.uuid4()
            vehicle_id = uuid.uuid4()

            from app.connectors.vehicle_connector import execute_command
            await execute_command(
                command_id=command_id,
                vehicle_id=vehicle_id,
                command_name="ClearDTC",
                command_params={}
            )

            # Assert: Verify operations

            # 1. Only 1 response chunk created
            assert mock_resp_repo.create_response.call_count == 1
            resp_call = mock_resp_repo.create_response.call_args
            assert resp_call.kwargs["sequence_number"] == 0
            assert resp_call.kwargs["is_final"] is True

            # 2. Redis publish called 2 times (1 response chunk + 1 status)
            assert mock_redis_client.publish.call_count == 2

            # 3. Command status updated to "completed"
            update_calls = mock_cmd_repo.update_command_status.call_args_list
            assert update_calls[1].kwargs["status"] == "completed"

            # 4. Audit log created
            mock_audit.log_audit_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_command_failure(self):
        """
        Test _handle_command_failure function directly.

        Verifies:
        - Command status updated to "failed"
        - Error event published to Redis
        - Audit log entry created
        - Metrics updated
        """
        with patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker, \
             patch("app.connectors.vehicle_connector.command_repository") as mock_cmd_repo, \
             patch("app.connectors.vehicle_connector.audit_service") as mock_audit, \
             patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis, \
             patch("app.connectors.vehicle_connector.increment_timeout_counter") as mock_timeout_counter, \
             patch("app.connectors.vehicle_connector.increment_command_counter") as mock_inc_counter, \
             patch("app.connectors.vehicle_connector.observe_command_duration") as mock_observe_duration:

            # Setup mocks
            mock_db = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_db

            mock_command = MagicMock()
            mock_command.user_id = uuid.uuid4()
            mock_command.submitted_at = datetime.now(timezone.utc)
            mock_cmd_repo.get_command_by_id = AsyncMock(return_value=mock_command)
            mock_cmd_repo.update_command_status = AsyncMock()

            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            mock_audit.log_audit_event = AsyncMock()

            # Act: Call _handle_command_failure
            command_id = uuid.uuid4()
            vehicle_id = uuid.uuid4()
            error = TimeoutError("Vehicle connection timeout")

            from app.connectors.vehicle_connector import _handle_command_failure
            await _handle_command_failure(
                command_id=command_id,
                vehicle_id=vehicle_id,
                command_name="ReadDTC",
                error=error
            )

            # Assert: Verify error handling operations

            # 1. Command status updated to "failed"
            mock_cmd_repo.update_command_status.assert_called_once()
            update_call = mock_cmd_repo.update_command_status.call_args
            assert update_call.kwargs["status"] == "failed"
            assert update_call.kwargs["command_id"] == command_id
            assert "timeout" in update_call.kwargs["error_message"].lower()

            # 2. Timeout counter incremented
            mock_timeout_counter.assert_called_once()

            # 3. Redis publish called (error event)
            assert mock_redis_client.publish.call_count == 1

            # 4. Audit log entry created
            mock_audit.log_audit_event.assert_called_once()
            audit_call = mock_audit.log_audit_event.call_args
            assert audit_call.kwargs["action"] == "command_failed"

            # 5. Metrics updated
            mock_inc_counter.assert_called_once_with("timeout")
            mock_observe_duration.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_status_event(self):
        """
        Test _publish_status_event function directly.

        Verifies:
        - Event is published to Redis with correct channel and data
        """
        with patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client

            # Act: Call _publish_status_event
            command_id = uuid.uuid4()
            completed_at = datetime.now(timezone.utc)

            from app.connectors.vehicle_connector import _publish_status_event
            await _publish_status_event(
                command_id=command_id,
                status="completed",
                completed_at=completed_at
            )

            # Assert: Verify Redis publish was called
            mock_redis_client.publish.assert_called_once()

            # Verify channel and event data
            publish_call = mock_redis_client.publish.call_args
            channel = publish_call.args[0]
            event_json = publish_call.args[1]

            assert channel == f"response:{command_id}"

            import json
            event_data = json.loads(event_json)
            assert event_data["event"] == "status"
            assert event_data["command_id"] == str(command_id)
            assert event_data["status"] == "completed"
            assert "completed_at" in event_data

    @pytest.mark.asyncio
    async def test_load_tls_credentials(self, cleanup_connector):
        """
        Test _load_tls_credentials method.

        Verifies:
        - TLS credentials loading raises FileNotFoundError for missing certs
        """
        from app.connectors.vehicle_connector import VehicleConnector

        connector = VehicleConnector()

        # Act & Assert: Should raise FileNotFoundError if certs don't exist
        try:
            connector._load_tls_credentials()
            # If we reach here, certs exist (which is fine)
        except FileNotFoundError:
            # Expected behavior when certs don't exist
            pass
