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
