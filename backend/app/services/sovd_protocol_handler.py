"""
SOVD 2.0 protocol handler for command validation and encoding.

This module provides validation, encoding, and decoding functions for SOVD commands.
"""

import json
from pathlib import Path
from typing import Any

import structlog
from jsonschema import ValidationError, validate  # type: ignore[import-untyped]

logger = structlog.get_logger(__name__)

# Load JSON Schema for SOVD commands
SCHEMA_PATH = (
    Path(__file__).parent.parent.parent.parent / "docs" / "api" / "sovd_command_schema.json"
)
with open(SCHEMA_PATH) as f:
    COMMAND_SCHEMA = json.load(f)


def validate_command(command_name: str, command_params: dict[str, Any]) -> str | None:
    """
    Validate a SOVD command against the JSON Schema.

    Args:
        command_name: Name of the SOVD command (e.g., "ReadDTC")
        command_params: Dictionary of command parameters

    Returns:
        None if validation succeeds, error message string if validation fails
    """
    logger.info(
        "sovd_command_validation_started",
        command_name=command_name,
        params=command_params,
    )

    # Check if command is defined in schema
    if command_name not in COMMAND_SCHEMA.get("definitions", {}):
        supported_commands = ", ".join(COMMAND_SCHEMA.get("definitions", {}).keys())
        error_msg = f"Unknown command: {command_name}. Supported commands: {supported_commands}"
        logger.warning(
            "sovd_command_validation_failed_unknown_command",
            command_name=command_name,
            error=error_msg,
        )
        return error_msg

    # Get the schema for this specific command
    command_schema = COMMAND_SCHEMA["definitions"][command_name]

    # Validate parameters against schema
    try:
        validate(instance=command_params, schema=command_schema)
        logger.info(
            "sovd_command_validation_succeeded",
            command_name=command_name,
        )
        return None
    except ValidationError as e:
        error_msg = f"Invalid parameters for command {command_name}: {e.message}"
        logger.warning(
            "sovd_command_validation_failed",
            command_name=command_name,
            error=error_msg,
            validation_path=list(e.path),
        )
        return error_msg


def encode_command(command_name: str, command_params: dict[str, Any]) -> dict[str, Any]:
    """
    Encode a SOVD command for vehicle transmission.

    For mock implementation, returns command as-is. Real implementation would
    convert to protobuf or SOVD XML format for vehicle transmission.

    Args:
        command_name: Name of the SOVD command
        command_params: Dictionary of command parameters

    Returns:
        Encoded command (currently returns original format)
    """
    logger.info(
        "sovd_command_encoding_placeholder",
        command_name=command_name,
        note="Mock implementation - returning as-is. Production requires protobuf/XML encoding",
    )
    return {"command_name": command_name, "command_params": command_params}


def decode_response(response_payload: dict[str, Any]) -> dict[str, Any]:
    """
    Decode a vehicle response from SOVD format.

    For mock implementation, returns response as-is. Real implementation would
    parse from protobuf or SOVD XML format.

    Args:
        response_payload: Raw response data from vehicle

    Returns:
        Decoded response (currently returns original format)
    """
    logger.info(
        "sovd_response_decoding_placeholder",
        note="Mock implementation - returning as-is. Production requires protobuf/XML decoding",
    )
    return response_payload
