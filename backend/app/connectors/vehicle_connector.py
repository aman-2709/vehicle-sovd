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

logger = structlog.get_logger(__name__)


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


# Mapping of command names to response generator functions
MOCK_RESPONSE_GENERATORS: dict[str, Any] = {
    "ReadDTC": _generate_read_dtc_response,
    "ClearDTC": _generate_clear_dtc_response,
    "ReadDataByID": _generate_read_data_by_id_response,
}


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

        # Update command status to 'in_progress'
        async with async_session_maker() as db_session:
            await command_repository.update_command_status(
                db=db_session,
                command_id=command_id,
                status="in_progress",
            )

        # Generate mock response payload
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
            # Call generator with params if it accepts them (e.g., ReadDataByID)
            if command_name == "ReadDataByID":
                data_id = command_params.get("dataId")
                response_payload = response_generator(data_id)
            else:
                response_payload = response_generator()

        logger.info(
            "mock_command_response_generated",
            command_id=str(command_id),
            command_name=command_name,
        )

        # Create new database session for response insertion
        async with async_session_maker() as db_session:
            # Insert response record into database
            response = await response_repository.create_response(
                db=db_session,
                command_id=command_id,
                response_payload=response_payload,
                sequence_number=1,  # First and only response chunk
                is_final=True,  # This is the final response
            )

            logger.info(
                "mock_command_response_persisted",
                command_id=str(command_id),
                response_id=str(response.response_id),
            )

        # Publish response event to Redis Pub/Sub
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            channel = f"response:{command_id}"
            event_data = {
                "event": "response",
                "command_id": str(command_id),
                "response_id": str(response.response_id),
                "response_payload": response_payload,
                "sequence_number": 1,
                "is_final": True,
            }

            await redis_client.publish(channel, json.dumps(event_data))

            logger.info(
                "mock_command_event_published",
                command_id=str(command_id),
                channel=channel,
            )
        finally:
            await redis_client.aclose()

        # Update command status to 'completed'
        async with async_session_maker() as db_session:
            await command_repository.update_command_status(
                db=db_session,
                command_id=command_id,
                status="completed",
                completed_at=datetime.now(timezone.utc),
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
            async with async_session_maker() as db_session:
                await command_repository.update_command_status(
                    db=db_session,
                    command_id=command_id,
                    status="failed",
                    error_message=str(e),
                    completed_at=datetime.now(timezone.utc),
                )
        except Exception as db_error:
            logger.error(
                "mock_command_failed_to_update_error_status",
                command_id=str(command_id),
                error=str(db_error),
                exc_info=True,
            )
