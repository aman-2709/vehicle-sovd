"""
Mock gRPC server for testing vehicle connector.

This module provides a mock VehicleService implementation that simulates
real vehicle responses for integration testing without requiring actual
vehicle hardware or network connectivity.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import grpc
from grpc import aio

from app.generated import sovd_vehicle_service_pb2, sovd_vehicle_service_pb2_grpc


class MockVehicleServicer(sovd_vehicle_service_pb2_grpc.VehicleServiceServicer):
    """
    Mock implementation of VehicleService for testing.

    Simulates realistic vehicle command responses with streaming support.
    Can be configured to simulate various scenarios including errors and timeouts.
    """

    def __init__(
        self,
        simulate_error: bool = False,
        error_code: grpc.StatusCode = grpc.StatusCode.INTERNAL,
        error_message: str = "Simulated error",
        delay_seconds: float = 0.0,
        timeout_seconds: float | None = None,
    ):
        """
        Initialize mock vehicle servicer.

        Args:
            simulate_error: If True, raise gRPC error instead of returning responses
            error_code: gRPC status code to return when simulating errors
            error_message: Error message for simulated errors
            delay_seconds: Delay between response chunks (simulates network latency)
            timeout_seconds: If set, delay before first response to simulate timeout
        """
        self.simulate_error = simulate_error
        self.error_code = error_code
        self.error_message = error_message
        self.delay_seconds = delay_seconds
        self.timeout_seconds = timeout_seconds

    async def ExecuteCommand(  # noqa: N802
        self,
        request: sovd_vehicle_service_pb2.CommandRequest,
        context: grpc.aio.ServicerContext,
    ) -> Any:
        """
        Execute command with streaming response.

        Yields multiple CommandResponse messages based on the command type.

        Args:
            request: CommandRequest from client
            context: gRPC context

        Yields:
            CommandResponse messages (streaming)

        Raises:
            grpc.RpcError: If simulate_error is True
        """
        # Simulate timeout if configured
        if self.timeout_seconds:
            await asyncio.sleep(self.timeout_seconds)

        # Simulate error if configured
        if self.simulate_error:
            await context.abort(self.error_code, self.error_message)

        # Generate responses based on command name
        command_name = request.command_name
        command_id = request.command_id

        if command_name == "ReadDTC":
            chunks = self._generate_read_dtc_chunks(command_id)
        elif command_name == "ReadDataByID":
            chunks = self._generate_read_data_by_id_chunks(command_id, request.command_params)
        elif command_name == "ClearDTC":
            chunks = self._generate_clear_dtc_chunks(command_id)
        else:
            # Generic success response for unknown commands
            chunks = [
                sovd_vehicle_service_pb2.CommandResponse(
                    command_id=command_id,
                    response_payload=json.dumps(
                        {
                            "status": "success",
                            "message": f"Command {command_name} executed successfully",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    ),
                    sequence_number=0,
                    is_final=True,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            ]

        # Stream responses with delays
        for i, chunk in enumerate(chunks):
            if i > 0 and self.delay_seconds > 0:
                await asyncio.sleep(self.delay_seconds)
            yield chunk

    def _generate_read_dtc_chunks(
        self, command_id: str
    ) -> list[sovd_vehicle_service_pb2.CommandResponse]:
        """
        Generate streaming response chunks for ReadDTC command.

        Returns:
            List of CommandResponse messages (3 chunks: 2 DTCs + final status)
        """
        chunks = []

        # Chunk 0: First DTC (P0420)
        chunks.append(
            sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(
                    {
                        "dtcs": [
                            {
                                "dtcCode": "P0420",
                                "description": "Catalyst System Efficiency Below Threshold",
                                "status": "confirmed",
                                "ecuAddress": "0x10",
                            }
                        ],
                        "ecuAddress": "0x10",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                sequence_number=0,
                is_final=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # Chunk 1: Second DTC (P0171)
        chunks.append(
            sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(
                    {
                        "dtcs": [
                            {
                                "dtcCode": "P0171",
                                "description": "System Too Lean (Bank 1)",
                                "status": "pending",
                                "ecuAddress": "0x10",
                            }
                        ],
                        "ecuAddress": "0x10",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                sequence_number=1,
                is_final=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # Chunk 2: Final status
        chunks.append(
            sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(
                    {
                        "status": "complete",
                        "totalDtcs": 2,
                        "ecuAddress": "0x10",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                sequence_number=2,
                is_final=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        return chunks

    def _generate_read_data_by_id_chunks(
        self, command_id: str, params: dict[str, str]
    ) -> list[sovd_vehicle_service_pb2.CommandResponse]:
        """
        Generate streaming response chunks for ReadDataByID command.

        Args:
            command_id: Command ID
            params: Command parameters (should contain "dataId")

        Returns:
            List of CommandResponse messages (2 chunks: reading + data)
        """
        data_id = params.get("dataId", "0x010C")
        chunks = []

        # Chunk 0: Request acknowledgment
        chunks.append(
            sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(
                    {
                        "status": "reading",
                        "dataId": data_id,
                        "ecuAddress": "0x10",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                sequence_number=0,
                is_final=False,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        # Chunk 1: Final data value
        data_responses = {
            "0x010C": {  # Engine RPM
                "dataId": "0x010C",
                "description": "Engine RPM",
                "value": 2450,
                "unit": "rpm",
            },
            "0x010D": {  # Vehicle Speed
                "dataId": "0x010D",
                "description": "Vehicle Speed",
                "value": 65,
                "unit": "km/h",
            },
        }

        data = data_responses.get(
            data_id,
            {
                "dataId": data_id,
                "description": "Unknown Data Identifier",
                "value": "N/A",
                "unit": "",
            },
        )

        chunks.append(
            sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(
                    {
                        "data": data,
                        "ecuAddress": "0x10",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                sequence_number=1,
                is_final=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        )

        return chunks

    def _generate_clear_dtc_chunks(
        self, command_id: str
    ) -> list[sovd_vehicle_service_pb2.CommandResponse]:
        """
        Generate single response chunk for ClearDTC command.

        Returns:
            List with one CommandResponse message
        """
        return [
            sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(
                    {
                        "status": "success",
                        "message": "DTCs cleared successfully",
                        "clearedCount": 3,
                        "ecuAddress": "0x10",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                sequence_number=0,
                is_final=True,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
        ]


class MockVehicleServer:
    """
    Mock gRPC server for testing.

    Manages server lifecycle (start/stop) and provides access to the servicer
    for configuration.
    """

    def __init__(self, port: int = 50051, servicer: MockVehicleServicer | None = None):
        """
        Initialize mock server.

        Args:
            port: Port to listen on (default: 50051)
            servicer: Custom servicer instance (default: create new MockVehicleServicer)
        """
        self.port = port
        self.servicer = servicer or MockVehicleServicer()
        self.server: aio.Server | None = None

    async def start(self) -> None:
        """Start the mock gRPC server."""
        self.server = aio.server()
        sovd_vehicle_service_pb2_grpc.add_VehicleServiceServicer_to_server(  # type: ignore[no-untyped-call]
            self.servicer, self.server
        )
        self.server.add_insecure_port(f"[::]:{self.port}")
        await self.server.start()

    async def stop(self) -> None:
        """Stop the mock gRPC server."""
        if self.server:
            await self.server.stop(grace=1.0)
            self.server = None

    async def __aenter__(self) -> "MockVehicleServer":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.stop()


async def start_mock_server(
    port: int = 50051,
    simulate_error: bool = False,
    error_code: grpc.StatusCode = grpc.StatusCode.INTERNAL,
    error_message: str = "Simulated error",
    delay_seconds: float = 0.0,
    timeout_seconds: float | None = None,
) -> MockVehicleServer:
    """
    Start a mock gRPC server (convenience function for tests).

    Args:
        port: Port to listen on
        simulate_error: If True, server will return errors
        error_code: gRPC status code for errors
        error_message: Error message
        delay_seconds: Delay between response chunks
        timeout_seconds: Delay before first response

    Returns:
        Started MockVehicleServer instance

    Example:
        ```python
        server = await start_mock_server(port=50051)
        # ... run tests ...
        await server.stop()
        ```
    """
    servicer = MockVehicleServicer(
        simulate_error=simulate_error,
        error_code=error_code,
        error_message=error_message,
        delay_seconds=delay_seconds,
        timeout_seconds=timeout_seconds,
    )
    server = MockVehicleServer(port=port, servicer=servicer)
    await server.start()
    return server
