"""
gRPC vehicle connector for SOVD command execution.

This module implements real vehicle communication using gRPC streaming RPC.
It replaces the previous mock implementation with actual gRPC client code
that connects to vehicle endpoints and processes streaming responses.
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import grpc
import redis.asyncio as redis
import structlog
from grpc import aio

from app.config import settings
from app.database import async_session_maker
from app.generated import sovd_vehicle_service_pb2, sovd_vehicle_service_pb2_grpc
from app.repositories import command_repository, response_repository
from app.services import audit_service
from app.utils.metrics import (
    increment_command_counter,
    increment_timeout_counter,
    observe_command_duration,
)

logger = structlog.get_logger(__name__)


class VehicleConnector:
    """
    gRPC client for vehicle communication.

    Manages gRPC channel lifecycle, connection pooling, and implements
    retry logic with exponential backoff for transient failures.
    """

    def __init__(self) -> None:
        """Initialize vehicle connector with gRPC channel."""
        self._channel: aio.Channel | None = None
        self._stub: sovd_vehicle_service_pb2_grpc.VehicleServiceStub | None = None

    async def _get_channel(self) -> aio.Channel:
        """
        Get or create gRPC channel.

        Implements connection pooling by reusing a single channel.
        Creates a new channel on first call or if previous channel was closed.

        Returns:
            Async gRPC channel instance
        """
        if self._channel is None:
            # Configure channel options for connection management
            options = [
                ("grpc.keepalive_time_ms", 30000),  # Send keepalive pings every 30s
                ("grpc.keepalive_timeout_ms", 10000),  # Wait 10s for ping ack
                ("grpc.keepalive_permit_without_calls", True),
                ("grpc.http2.max_pings_without_data", 0),
                ("grpc.max_receive_message_length", 10 * 1024 * 1024),  # 10MB
            ]

            # Create channel based on TLS configuration
            if settings.VEHICLE_USE_TLS:
                credentials = self._load_tls_credentials()
                self._channel = aio.secure_channel(
                    settings.VEHICLE_ENDPOINT_URL, credentials, options=options
                )
                logger.info(
                    "grpc_secure_channel_created",
                    endpoint=settings.VEHICLE_ENDPOINT_URL,
                )
            else:
                self._channel = aio.insecure_channel(settings.VEHICLE_ENDPOINT_URL, options=options)
                logger.info(
                    "grpc_insecure_channel_created",
                    endpoint=settings.VEHICLE_ENDPOINT_URL,
                )

        return self._channel

    def _load_tls_credentials(self) -> grpc.ChannelCredentials:
        """
        Load TLS credentials for mutual TLS (mTLS).

        Loads CA certificate, client private key, and client certificate
        from the certs directory.

        Returns:
            gRPC SSL channel credentials

        Raises:
            FileNotFoundError: If certificate files are missing
        """
        cert_dir = Path(__file__).parent.parent.parent / "certs"

        # Load certificates
        try:
            with open(cert_dir / "ca.pem", "rb") as f:
                root_cert = f.read()
            with open(cert_dir / "client-key.pem", "rb") as f:
                client_key = f.read()
            with open(cert_dir / "client-cert.pem", "rb") as f:
                client_cert = f.read()

            logger.info("tls_certificates_loaded", cert_dir=str(cert_dir))

            return grpc.ssl_channel_credentials(
                root_certificates=root_cert,
                private_key=client_key,
                certificate_chain=client_cert,
            )
        except FileNotFoundError as e:
            logger.error(
                "tls_certificates_not_found",
                cert_dir=str(cert_dir),
                error=str(e),
            )
            raise

    async def _get_stub(self) -> sovd_vehicle_service_pb2_grpc.VehicleServiceStub:
        """
        Get or create gRPC stub.

        Returns:
            VehicleServiceStub instance for making RPC calls
        """
        if self._stub is None:
            channel = await self._get_channel()
            self._stub = sovd_vehicle_service_pb2_grpc.VehicleServiceStub(channel)  # type: ignore[no-untyped-call]

        return self._stub

    async def close(self) -> None:
        """Close gRPC channel and clean up resources."""
        if self._channel is not None:
            await self._channel.close()
            self._channel = None
            self._stub = None
            logger.info("grpc_channel_closed")

    async def execute_command_with_retry(
        self,
        command_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        command_name: str,
        command_params: dict[str, Any],
    ) -> None:
        """
        Execute command with retry logic for transient failures.

        Implements exponential backoff for UNAVAILABLE and DEADLINE_EXCEEDED errors.

        Args:
            command_id: UUID of the command to execute
            vehicle_id: UUID of the target vehicle
            command_name: SOVD command identifier (e.g., "ReadDTC")
            command_params: Command-specific parameters

        Raises:
            Exception: If command execution fails after all retries
        """
        max_retries = settings.VEHICLE_MAX_RETRIES
        base_delay = settings.VEHICLE_RETRY_BASE_DELAY

        for attempt in range(max_retries):
            try:
                await self._execute_command_internal(
                    command_id, vehicle_id, command_name, command_params
                )
                return  # Success, exit retry loop

            except aio.AioRpcError as e:
                # Check if error is retryable
                is_retryable = e.code() in (
                    grpc.StatusCode.UNAVAILABLE,
                    grpc.StatusCode.DEADLINE_EXCEEDED,
                )

                if is_retryable and attempt < max_retries - 1:
                    # Calculate exponential backoff delay
                    delay = base_delay * (2**attempt)
                    logger.warning(
                        "grpc_command_retrying",
                        command_id=str(command_id),
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        error_code=e.code().name,
                        delay_seconds=delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    # Not retryable or max retries exceeded, re-raise
                    raise

    async def _execute_command_internal(
        self,
        command_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        command_name: str,
        command_params: dict[str, Any],
    ) -> None:
        """
        Internal command execution logic (single attempt).

        Creates gRPC request, calls ExecuteCommand RPC, iterates over streamed
        responses, inserts each response to database, publishes to Redis,
        and updates command status.

        Args:
            command_id: UUID of the command to execute
            vehicle_id: UUID of the target vehicle
            command_name: SOVD command identifier
            command_params: Command-specific parameters

        Raises:
            grpc.RpcError: If gRPC call fails
            Exception: If database or Redis operations fail
        """
        logger.info(
            "grpc_command_execution_started",
            command_id=str(command_id),
            vehicle_id=str(vehicle_id),
            command_name=command_name,
        )

        try:
            # Update command status to 'in_progress'
            async with async_session_maker() as db_session:
                await command_repository.update_command_status(
                    db=db_session,
                    command_id=command_id,
                    status="in_progress",
                )

            # Create gRPC request
            request = sovd_vehicle_service_pb2.CommandRequest(
                command_id=str(command_id),  # UUID → string
                vehicle_id=str(vehicle_id),
                command_name=command_name,
                command_params=command_params,
            )

            # Get gRPC stub
            stub = await self._get_stub()

            # Call ExecuteCommand RPC with timeout
            timeout = settings.VEHICLE_GRPC_TIMEOUT
            logger.debug(
                "grpc_executing_command",
                command_id=str(command_id),
                endpoint=settings.VEHICLE_ENDPOINT_URL,
                timeout_seconds=timeout,
            )

            response_stream = stub.ExecuteCommand(request, timeout=float(timeout))

            # Iterate over streamed responses
            chunk_count = 0
            async for response in response_stream:
                # Parse response payload (JSON string → dict)
                response_dict = json.loads(response.response_payload)

                # Publish response chunk to database and Redis
                await _publish_response_chunk(
                    command_id=command_id,
                    response_payload=response_dict,
                    sequence_number=response.sequence_number,
                    is_final=response.is_final,
                )

                chunk_count += 1
                logger.debug(
                    "grpc_response_chunk_received",
                    command_id=str(command_id),
                    sequence_number=response.sequence_number,
                    is_final=response.is_final,
                )

                # Break if final chunk (optimization)
                if response.is_final:
                    break

            logger.info(
                "grpc_command_streaming_completed",
                command_id=str(command_id),
                chunk_count=chunk_count,
            )

            # Update command status to 'completed'
            completed_at = datetime.now(timezone.utc)
            async with async_session_maker() as db_session:
                # Get command to extract user_id for audit logging
                command = await command_repository.get_command_by_id(db_session, command_id)

                await command_repository.update_command_status(
                    db=db_session,
                    command_id=command_id,
                    status="completed",
                    completed_at=completed_at,
                )

                # Update Prometheus metrics
                if command:
                    increment_command_counter("completed")
                    duration = (completed_at - command.submitted_at).total_seconds()
                    observe_command_duration(duration)
                    logger.debug(
                        "command_metrics_recorded",
                        command_id=str(command_id),
                        status="completed",
                        duration_seconds=duration,
                    )

            # Publish status event to Redis Pub/Sub
            await _publish_status_event(
                command_id=command_id,
                status="completed",
                completed_at=completed_at,
            )

            # Log audit event for command completion
            async with async_session_maker() as db_session:
                # Get command again for audit logging
                command = await command_repository.get_command_by_id(db_session, command_id)

                if command:
                    await audit_service.log_audit_event(
                        user_id=command.user_id,
                        action="command_completed",
                        entity_type="command",
                        entity_id=command_id,
                        details={
                            "command_name": command_name,
                            "chunk_count": chunk_count,
                        },
                        ip_address=None,  # Not available in background task
                        user_agent=None,
                        db_session=db_session,
                        vehicle_id=vehicle_id,
                        command_id=command_id,
                    )

            logger.info(
                "grpc_command_execution_completed",
                command_id=str(command_id),
                vehicle_id=str(vehicle_id),
                command_name=command_name,
            )

        except aio.AioRpcError as e:
            # Map gRPC errors to Python exceptions and handle
            logger.error(
                "grpc_command_execution_failed",
                command_id=str(command_id),
                error_code=e.code().name,
                error_details=e.details(),
                exc_info=True,
            )

            # Map gRPC status codes to exceptions
            if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                raise TimeoutError("Vehicle connection timeout") from e
            elif e.code() == grpc.StatusCode.NOT_FOUND:
                raise ConnectionError("Vehicle not found") from e
            elif e.code() == grpc.StatusCode.UNAVAILABLE:
                raise ConnectionError("Vehicle unavailable") from e
            elif e.code() == grpc.StatusCode.INVALID_ARGUMENT:
                raise ValueError(f"Invalid command request: {e.details()}") from e
            elif e.code() == grpc.StatusCode.CANCELLED:
                raise ConnectionError("Request cancelled") from e
            else:
                raise RuntimeError(f"gRPC error: {e.code().name}") from e

        except Exception as e:
            # Catch all other exceptions (database, Redis, JSON parsing, etc.)
            logger.error(
                "grpc_command_execution_unexpected_error",
                command_id=str(command_id),
                error=str(e),
                exc_info=True,
            )
            raise


# Global connector instance (singleton pattern)
_connector: VehicleConnector | None = None


def get_connector() -> VehicleConnector:
    """
    Get or create global VehicleConnector instance.

    Returns:
        Singleton VehicleConnector instance
    """
    global _connector
    if _connector is None:
        _connector = VehicleConnector()
    return _connector


async def _publish_response_chunk(
    command_id: uuid.UUID,
    response_payload: dict[str, Any],
    sequence_number: int,
    is_final: bool,
) -> uuid.UUID:
    """
    Publish a single response chunk to database and Redis.

    Creates a response record in the database and publishes the corresponding
    event to Redis Pub/Sub for real-time delivery to WebSocket clients.

    Args:
        command_id: UUID of the command being executed
        response_payload: Response data payload for this chunk
        sequence_number: Sequential number of this chunk (0-indexed)
        is_final: Whether this is the final chunk in the sequence

    Returns:
        UUID of the created response record

    Raises:
        Exception: If database or Redis operations fail
    """
    # Create response record in database
    async with async_session_maker() as db_session:
        response = await response_repository.create_response(
            db=db_session,
            command_id=command_id,
            response_payload=response_payload,
            sequence_number=sequence_number,
            is_final=is_final,
        )

        logger.info(
            "grpc_command_response_chunk_persisted",
            command_id=str(command_id),
            response_id=str(response.response_id),
            sequence_number=sequence_number,
            is_final=is_final,
        )

    # Publish response event to Redis Pub/Sub
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
    try:
        channel = f"response:{command_id}"
        event_data = {
            "event": "response",
            "command_id": str(command_id),
            "response_id": str(response.response_id),
            "response_payload": response_payload,
            "sequence_number": sequence_number,
            "is_final": is_final,
        }

        await redis_client.publish(channel, json.dumps(event_data))

        logger.info(
            "grpc_command_response_chunk_published",
            command_id=str(command_id),
            channel=channel,
            sequence_number=sequence_number,
            is_final=is_final,
        )
    finally:
        await redis_client.aclose()

    return response.response_id


async def _publish_status_event(
    command_id: uuid.UUID,
    status: str,
    completed_at: datetime | None = None,
    error_message: str | None = None,
) -> None:
    """
    Publish command status event to Redis Pub/Sub.

    Args:
        command_id: UUID of the command
        status: Status string ("completed" or "failed")
        completed_at: Timestamp when command completed/failed
        error_message: Optional error message for failed commands
    """
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
    try:
        channel = f"response:{command_id}"
        event_data: dict[str, Any] = {
            "event": "status" if status == "completed" else "error",
            "command_id": str(command_id),
            "status": status,
        }

        if completed_at:
            event_data["completed_at"] = completed_at.isoformat()

        if error_message:
            event_data["error_message"] = error_message

        await redis_client.publish(channel, json.dumps(event_data))

        logger.info(
            "grpc_command_status_event_published",
            command_id=str(command_id),
            channel=channel,
            status=status,
        )
    finally:
        await redis_client.aclose()


async def _handle_command_failure(
    command_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    command_name: str,
    error: Exception,
) -> None:
    """
    Handle command execution failure.

    Updates command status to 'failed', publishes error event to Redis,
    logs audit event, and updates Prometheus metrics.

    Args:
        command_id: UUID of the failed command
        vehicle_id: UUID of the target vehicle
        command_name: SOVD command identifier
        error: Exception that caused the failure
    """
    try:
        failed_at = datetime.now(timezone.utc)

        # Update command status to 'failed'
        async with async_session_maker() as db_session:
            command = await command_repository.get_command_by_id(db_session, command_id)

            # Determine failure status (timeout vs failed)
            failure_status = "timeout" if isinstance(error, TimeoutError) else "failed"

            # Increment timeout counter for timeout errors
            if isinstance(error, TimeoutError):
                increment_timeout_counter()

            await command_repository.update_command_status(
                db=db_session,
                command_id=command_id,
                status="failed",
                error_message=str(error),
                completed_at=failed_at,
            )

            # Update Prometheus metrics
            if command:
                increment_command_counter(failure_status)
                duration = (failed_at - command.submitted_at).total_seconds()
                observe_command_duration(duration)
                logger.debug(
                    "command_metrics_recorded",
                    command_id=str(command_id),
                    status=failure_status,
                    duration_seconds=duration,
                )

        # Publish error event to Redis Pub/Sub
        await _publish_status_event(
            command_id=command_id,
            status="failed",
            completed_at=failed_at,
            error_message=str(error),
        )

        # Log audit event for command failure
        async with async_session_maker() as db_session:
            command = await command_repository.get_command_by_id(db_session, command_id)

            if command:
                await audit_service.log_audit_event(
                    user_id=command.user_id,
                    action="command_failed",
                    entity_type="command",
                    entity_id=command_id,
                    details={
                        "command_name": command_name,
                        "error": str(error),
                    },
                    ip_address=None,
                    user_agent=None,
                    db_session=db_session,
                    vehicle_id=vehicle_id,
                    command_id=command_id,
                )

    except Exception as db_error:
        logger.error(
            "grpc_command_failed_to_update_error_status",
            command_id=str(command_id),
            error=str(db_error),
            exc_info=True,
        )


async def execute_command(
    command_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
) -> None:
    """
    Execute a vehicle command via gRPC.

    Public API for executing SOVD commands on connected vehicles.
    Handles the complete execution flow including retry logic and error handling.

    Args:
        command_id: UUID of the command to execute
        vehicle_id: UUID of the target vehicle
        command_name: SOVD command identifier (e.g., "ReadDTC")
        command_params: Command-specific parameters

    Note:
        This function runs as a background task and creates its own
        database sessions. Errors are logged and command status is updated,
        but exceptions are not propagated to the caller.
    """
    try:
        connector = get_connector()
        await connector.execute_command_with_retry(
            command_id, vehicle_id, command_name, command_params
        )
    except Exception as e:
        # Handle all failures (gRPC errors, database errors, etc.)
        await _handle_command_failure(command_id, vehicle_id, command_name, e)
