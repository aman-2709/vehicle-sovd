"""
Mock vehicle connector for development and testing.

This module simulates SOVD command execution and response generation
without actual vehicle communication. It is used for development and testing
purposes until the real gRPC/WebSocket vehicle connector is implemented.
"""

import asyncio
import json
import random
import uuid
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as redis
import structlog

from app.config import settings
from app.database import async_session_maker
from app.repositories import command_repository, response_repository
from app.services import audit_service
from app.utils.metrics import increment_command_counter, observe_command_duration

logger = structlog.get_logger(__name__)


# Error simulation probabilities (configurable)
ERROR_PROBABILITY_TIMEOUT = 0.10  # 10% of commands timeout
ERROR_PROBABILITY_UNREACHABLE = 0.05  # 5% of commands fail immediately
ERROR_PROBABILITY_MALFORMED = 0.03  # 3% of commands send invalid data
COMMAND_TIMEOUT_SECONDS = 30  # Timeout threshold


def _generate_read_dtc_response() -> dict[str, Any]:
    """
    Generate mock response for ReadDTC command.

    Returns:
        Mock DTC data with diagnostic trouble codes.
    """
    return {
        "dtcs": [
            {
                "dtcCode": "P0420",
                "description": "Catalyst System Efficiency Below Threshold",
                "status": "confirmed",
                "ecuAddress": "0x10",
            },
            {
                "dtcCode": "P0171",
                "description": "System Too Lean (Bank 1)",
                "status": "pending",
                "ecuAddress": "0x10",
            },
            {
                "dtcCode": "P0300",
                "description": "Random/Multiple Cylinder Misfire Detected",
                "status": "confirmed",
                "ecuAddress": "0x11",
            },
        ],
        "ecuAddress": "0x10",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _generate_clear_dtc_response() -> dict[str, Any]:
    """
    Generate mock response for ClearDTC command.

    Returns:
        Mock confirmation of DTC clearing.
    """
    return {
        "status": "success",
        "message": "DTCs cleared successfully",
        "clearedCount": 3,
        "ecuAddress": "0x10",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _generate_read_data_by_id_response(data_id: str | None = None) -> dict[str, Any]:
    """
    Generate mock response for ReadDataByID command.

    Args:
        data_id: Optional data identifier to customize response.

    Returns:
        Mock vehicle data based on data identifier.
    """
    # Default data_id if not provided
    if data_id is None:
        data_id = "0x010C"

    # Map common data IDs to mock responses
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
        "0x0105": {  # Engine Coolant Temperature
            "dataId": "0x0105",
            "description": "Engine Coolant Temperature",
            "value": 88,
            "unit": "°C",
        },
    }

    # Return specific data if available, otherwise generic response
    data = data_responses.get(
        data_id,
        {
            "dataId": data_id,
            "description": "Unknown Data Identifier",
            "value": "N/A",
            "unit": "",
        },
    )

    return {
        "data": data,
        "ecuAddress": "0x10",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _generate_read_dtc_streaming_chunks() -> list[tuple[dict[str, Any], float]]:
    """
    Generate streaming response chunks for ReadDTC command.

    Simulates progressive DTC reading with multiple response chunks,
    each containing one DTC followed by a final status chunk.

    Returns:
        List of tuples containing (response_payload, delay_seconds).
        Each tuple represents a chunk to be sent with the specified delay
        before the next chunk.
    """
    chunks: list[tuple[dict[str, Any], float]] = []

    # Chunk 1: First DTC (P0420)
    chunk_1 = {
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
    chunks.append((chunk_1, 0.5))

    # Chunk 2: Second DTC (P0171)
    chunk_2 = {
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
    chunks.append((chunk_2, 0.5))

    # Chunk 3: Final status chunk
    chunk_3 = {
        "status": "complete",
        "totalDtcs": 2,
        "ecuAddress": "0x10",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    chunks.append((chunk_3, 0.0))  # No delay after final chunk

    return chunks


def _generate_read_data_by_id_streaming_chunks(
    data_id: str | None = None,
) -> list[tuple[dict[str, Any], float]]:
    """
    Generate streaming response chunks for ReadDataByID command.

    Simulates progressive data reading with multiple response chunks,
    showing data acquisition stages.

    Args:
        data_id: Optional data identifier to customize response.

    Returns:
        List of tuples containing (response_payload, delay_seconds).
        Each tuple represents a chunk to be sent with the specified delay
        before the next chunk.
    """
    # Default data_id if not provided
    if data_id is None:
        data_id = "0x010C"

    chunks: list[tuple[dict[str, Any], float]] = []

    # Chunk 1: Request acknowledgment
    chunk_1 = {
        "status": "reading",
        "dataId": data_id,
        "ecuAddress": "0x10",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    chunks.append((chunk_1, 0.5))

    # Chunk 2: Final data value (reuse existing generator logic)
    chunk_2 = _generate_read_data_by_id_response(data_id)
    chunks.append((chunk_2, 0.0))  # No delay after final chunk

    return chunks


# Mapping of command names to response generator functions
MOCK_RESPONSE_GENERATORS: dict[str, Any] = {
    "ReadDTC": _generate_read_dtc_response,
    "ClearDTC": _generate_clear_dtc_response,
    "ReadDataByID": _generate_read_data_by_id_response,
}


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
        sequence_number: Sequential number of this chunk (starts at 1)
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
            "mock_command_response_chunk_persisted",
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
            "mock_command_response_chunk_published",
            command_id=str(command_id),
            channel=channel,
            sequence_number=sequence_number,
            is_final=is_final,
        )
    finally:
        await redis_client.aclose()

    return response.response_id


async def execute_command(
    command_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
) -> None:
    """
    Execute a mock vehicle command asynchronously.

    Simulates network delay, generates mock SOVD response payload,
    publishes response event to Redis Pub/Sub, and updates database.

    Args:
        command_id: UUID of the command to execute
        vehicle_id: UUID of the target vehicle
        command_name: SOVD command identifier (e.g., "ReadDTC")
        command_params: Command-specific parameters

    Note:
        This function runs as a background task and creates its own
        database session. All commands succeed (no error simulation).
    """
    logger.info(
        "mock_command_execution_started",
        command_id=str(command_id),
        vehicle_id=str(vehicle_id),
        command_name=command_name,
    )

    try:
        # Simulate network delay (0.5-1.5 seconds)
        delay = random.uniform(0.5, 1.5)
        logger.debug(
            "mock_command_simulating_network_delay",
            command_id=str(command_id),
            delay_seconds=delay,
        )
        await asyncio.sleep(delay)

        # Simulate error scenarios based on configured probabilities
        error_roll = random.random()

        if error_roll < ERROR_PROBABILITY_TIMEOUT:
            # Timeout scenario (10% probability)
            logger.warning(
                "mock_command_simulating_timeout",
                command_id=str(command_id),
                timeout_seconds=COMMAND_TIMEOUT_SECONDS,
            )
            await asyncio.sleep(COMMAND_TIMEOUT_SECONDS + 1)
            raise TimeoutError("Vehicle connection timeout")

        elif error_roll < ERROR_PROBABILITY_TIMEOUT + ERROR_PROBABILITY_UNREACHABLE:
            # Vehicle unreachable scenario (5% probability)
            logger.warning(
                "mock_command_simulating_unreachable",
                command_id=str(command_id),
            )
            raise ConnectionError("Vehicle unreachable")

        elif error_roll < (
            ERROR_PROBABILITY_TIMEOUT + ERROR_PROBABILITY_UNREACHABLE + ERROR_PROBABILITY_MALFORMED
        ):
            # Malformed response scenario (3% probability)
            logger.warning(
                "mock_command_simulating_malformed_response",
                command_id=str(command_id),
            )
            # First publish a malformed chunk
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
            try:
                channel = f"response:{command_id}"
                malformed_data = '{"incomplete": "json", "missing_closing_brace"'
                await redis_client.publish(channel, malformed_data)
                logger.debug(
                    "mock_command_malformed_chunk_published",
                    command_id=str(command_id),
                    channel=channel,
                )
            finally:
                await redis_client.aclose()

            # Then raise error
            raise ValueError("Invalid response format from vehicle")

        # Update command status to 'in_progress'
        async with async_session_maker() as db_session:
            await command_repository.update_command_status(
                db=db_session,
                command_id=command_id,
                status="in_progress",
            )

        # Generate streaming response chunks
        chunks: list[tuple[dict[str, Any], float]] = []

        # Determine if command supports streaming
        if command_name == "ReadDTC":
            chunks = _generate_read_dtc_streaming_chunks()
        elif command_name == "ReadDataByID":
            data_id = command_params.get("dataId")
            chunks = _generate_read_data_by_id_streaming_chunks(data_id)
        else:
            # For other commands (ClearDTC, unknown commands), use single-chunk response
            response_generator = MOCK_RESPONSE_GENERATORS.get(command_name)
            if response_generator is None:
                logger.warning(
                    "mock_command_unknown_command_type",
                    command_id=str(command_id),
                    command_name=command_name,
                )
                # Generate generic success response for unknown commands
                response_payload = {
                    "status": "success",
                    "message": f"Command {command_name} executed successfully (mock)",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            else:
                response_payload = response_generator()

            # Single chunk with no delay
            chunks = [(response_payload, 0.0)]

        logger.info(
            "mock_command_streaming_chunks_generated",
            command_id=str(command_id),
            command_name=command_name,
            chunk_count=len(chunks),
        )

        # Publish each chunk sequentially with delays
        for seq_num, (payload, delay) in enumerate(chunks, start=1):
            is_final = seq_num == len(chunks)

            # Publish chunk to database and Redis
            await _publish_response_chunk(
                command_id=command_id,
                response_payload=payload,
                sequence_number=seq_num,
                is_final=is_final,
            )

            # Wait before next chunk (if not final)
            if delay > 0:
                await asyncio.sleep(delay)

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
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
        try:
            channel = f"response:{command_id}"
            status_event = {
                "event": "status",
                "command_id": str(command_id),
                "status": "completed",
                "completed_at": completed_at.isoformat(),
            }

            await redis_client.publish(channel, json.dumps(status_event))

            logger.info(
                "mock_command_status_event_published",
                command_id=str(command_id),
                channel=channel,
                status="completed",
            )
        finally:
            await redis_client.aclose()

        # Log audit event for command completion
        async with async_session_maker() as db_session:
            # Get command again for audit logging
            command = await command_repository.get_command_by_id(db_session, command_id)

            # Log audit event for command completion
            if command:
                # Use final chunk payload for audit logging
                final_payload = chunks[-1][0] if chunks else {}

                await audit_service.log_audit_event(
                    user_id=command.user_id,
                    action="command_completed",
                    entity_type="command",
                    entity_id=command_id,
                    details={
                        "command_name": command_name,
                        "response_payload": final_payload,
                        "chunk_count": len(chunks),
                    },
                    ip_address=None,  # Not available in background task
                    user_agent=None,  # Not available in background task
                    db_session=db_session,
                    vehicle_id=vehicle_id,
                    command_id=command_id,
                )

        logger.info(
            "mock_command_execution_completed",
            command_id=str(command_id),
            vehicle_id=str(vehicle_id),
            command_name=command_name,
        )

    except Exception as e:
        logger.error(
            "mock_command_execution_failed",
            command_id=str(command_id),
            error=str(e),
            exc_info=True,
        )

        # Update command status to 'failed' on unexpected errors
        try:
            failed_at = datetime.now(timezone.utc)
            async with async_session_maker() as db_session:
                # Get command to extract user_id for audit logging
                command = await command_repository.get_command_by_id(db_session, command_id)

                # Determine failure status (timeout vs failed)
                failure_status = "timeout" if isinstance(e, TimeoutError) else "failed"

                await command_repository.update_command_status(
                    db=db_session,
                    command_id=command_id,
                    status="failed",
                    error_message=str(e),
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
            redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)  # type: ignore[no-untyped-call]
            try:
                channel = f"response:{command_id}"
                error_event = {
                    "event": "error",
                    "command_id": str(command_id),
                    "error_message": str(e),
                    "failed_at": failed_at.isoformat(),
                }

                await redis_client.publish(channel, json.dumps(error_event))

                logger.info(
                    "mock_command_error_event_published",
                    command_id=str(command_id),
                    channel=channel,
                )
            finally:
                await redis_client.aclose()

            # Log audit event for command failure
            async with async_session_maker() as db_session:
                # Get command again for audit logging
                command = await command_repository.get_command_by_id(db_session, command_id)

                # Log audit event for command failure
                if command:
                    await audit_service.log_audit_event(
                        user_id=command.user_id,
                        action="command_failed",
                        entity_type="command",
                        entity_id=command_id,
                        details={
                            "command_name": command_name,
                            "error": str(e),
                        },
                        ip_address=None,  # Not available in background task
                        user_agent=None,  # Not available in background task
                        db_session=db_session,
                        vehicle_id=vehicle_id,
                        command_id=command_id,
                    )
        except Exception as db_error:
            logger.error(
                "mock_command_failed_to_update_error_status",
                command_id=str(command_id),
                error=str(db_error),
                exc_info=True,
            )
