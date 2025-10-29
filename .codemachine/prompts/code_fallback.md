# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Implement `backend/app/services/sovd_protocol_handler.py` module for SOVD 2.0 command validation and encoding. Create JSON Schema file `docs/api/sovd_command_schema.json` defining structure for SOVD commands (fields: command_name, command_params with types). Implement functions: `validate_command(command_name, command_params)` (validates against JSON Schema, returns validation errors or None), `encode_command(command_name, command_params)` (formats command for vehicle transmission - for now, return as-is since using mock; real implementation would convert to protobuf or SOVD XML), `decode_response(response_payload)` (parses vehicle response - for now, return as-is). Integrate `validate_command` into `command_service.py` `submit_command` function (reject invalid commands with 400 Bad Request). Write unit tests in `backend/tests/unit/test_sovd_protocol_handler.py` covering validation success and failure cases.

---

## Issues Detected

*   **Missing Implementation:** The task has NOT been implemented at all. None of the required files exist:
    - `backend/app/services/sovd_protocol_handler.py` - DOES NOT EXIST
    - `docs/api/sovd_command_schema.json` - DOES NOT EXIST
    - `backend/tests/unit/test_sovd_protocol_handler.py` - DOES NOT EXIST
*   **Missing Integration:** The `command_service.py` has NOT been modified to integrate SOVD validation
*   **Missing Dependency:** The `jsonschema` package has NOT been added to `backend/requirements.txt`

---

## Best Approach to Fix

You MUST implement the complete SOVD protocol handler module from scratch. Follow these steps EXACTLY:

### Step 1: Add jsonschema Dependency

Add `jsonschema>=4.20.0` to `backend/requirements.txt`

### Step 2: Create JSON Schema File

Create `docs/api/sovd_command_schema.json` with the following structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SOVD Command Schema",
  "description": "JSON Schema for SOVD 2.0 command validation",
  "definitions": {
    "ReadDTC": {
      "type": "object",
      "required": ["ecuAddress"],
      "properties": {
        "ecuAddress": {
          "type": "string",
          "pattern": "^0x[0-9A-Fa-f]{2}$",
          "description": "ECU address in hexadecimal format (0x00 to 0xFF)"
        }
      },
      "additionalProperties": false
    },
    "ClearDTC": {
      "type": "object",
      "required": ["ecuAddress"],
      "properties": {
        "ecuAddress": {
          "type": "string",
          "pattern": "^0x[0-9A-Fa-f]{2}$",
          "description": "ECU address in hexadecimal format"
        },
        "dtcCode": {
          "type": "string",
          "pattern": "^P[0-9A-F]{4}$",
          "description": "Optional specific DTC code to clear (e.g., P0420)"
        }
      },
      "additionalProperties": false
    },
    "ReadDataByID": {
      "type": "object",
      "required": ["ecuAddress", "dataId"],
      "properties": {
        "ecuAddress": {
          "type": "string",
          "pattern": "^0x[0-9A-Fa-f]{2}$",
          "description": "ECU address in hexadecimal format"
        },
        "dataId": {
          "type": "string",
          "pattern": "^0x[0-9A-Fa-f]{4}$",
          "description": "Data identifier in hexadecimal format (0x0000 to 0xFFFF)"
        }
      },
      "additionalProperties": false
    }
  }
}
```

### Step 3: Create SOVD Protocol Handler Module

Create `backend/app/services/sovd_protocol_handler.py` with the following implementation:

```python
"""
SOVD 2.0 protocol handler for command validation and encoding.

This module provides validation, encoding, and decoding functions for SOVD commands.
"""

import json
from pathlib import Path
from typing import Any

import structlog
from jsonschema import ValidationError, validate

logger = structlog.get_logger(__name__)

# Load JSON Schema for SOVD commands
SCHEMA_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "api" / "sovd_command_schema.json"
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
        error_msg = f"Unknown command: {command_name}. Supported commands: {', '.join(COMMAND_SCHEMA.get('definitions', {}).keys())}"
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
```

### Step 4: Integrate Validation into Command Service

Modify `backend/app/services/command_service.py`:

1. Add import at the top (around line 15):
```python
from app.services import sovd_protocol_handler
```

2. Insert validation logic AFTER vehicle validation (between lines 60-62), BEFORE creating the command:
```python
    # Validate SOVD command
    validation_error = sovd_protocol_handler.validate_command(command_name, command_params)
    if validation_error:
        logger.warning(
            "command_submission_failed_invalid_sovd_command",
            command_name=command_name,
            validation_error=validation_error,
            user_id=str(user_id),
        )
        return None
```

### Step 5: Add Error Handling in API Endpoint

Modify `backend/app/api/v1/commands.py` to handle validation failures with 400 Bad Request.

Find the submit_command endpoint and update it to check if the service returns None and raise HTTPException:

```python
# After calling command_service.submit_command
if command is None:
    raise HTTPException(
        status_code=400,
        detail="Invalid command: vehicle not found or command validation failed"
    )
```

### Step 6: Create Comprehensive Unit Tests

Create `backend/tests/unit/test_sovd_protocol_handler.py`:

```python
"""
Unit tests for SOVD protocol handler module.
"""

import pytest

from app.services import sovd_protocol_handler


class TestValidateCommand:
    """Test cases for validate_command function."""

    def test_validate_read_dtc_valid(self):
        """Test validation succeeds for valid ReadDTC command."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "0x10"}
        )
        assert result is None

    def test_validate_read_dtc_missing_ecu_address(self):
        """Test validation fails when ecuAddress is missing."""
        result = sovd_protocol_handler.validate_command("ReadDTC", {})
        assert result is not None
        assert "ecuAddress" in result or "required" in result.lower()

    def test_validate_read_dtc_invalid_ecu_format(self):
        """Test validation fails for invalid ECU address format."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "10"}
        )
        assert result is not None

    def test_validate_clear_dtc_valid_required_only(self):
        """Test validation succeeds for ClearDTC with required params only."""
        result = sovd_protocol_handler.validate_command(
            "ClearDTC", {"ecuAddress": "0xFF"}
        )
        assert result is None

    def test_validate_clear_dtc_valid_with_optional(self):
        """Test validation succeeds for ClearDTC with optional dtcCode."""
        result = sovd_protocol_handler.validate_command(
            "ClearDTC", {"ecuAddress": "0x10", "dtcCode": "P0420"}
        )
        assert result is None

    def test_validate_read_data_by_id_valid(self):
        """Test validation succeeds for valid ReadDataByID command."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10", "dataId": "0x010C"}
        )
        assert result is None

    def test_validate_read_data_by_id_missing_data_id(self):
        """Test validation fails when dataId is missing."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10"}
        )
        assert result is not None
        assert "dataId" in result or "required" in result.lower()

    def test_validate_read_data_by_id_invalid_data_id_format(self):
        """Test validation fails for invalid dataId format."""
        result = sovd_protocol_handler.validate_command(
            "ReadDataByID", {"ecuAddress": "0x10", "dataId": "010C"}
        )
        assert result is not None

    def test_validate_unknown_command(self):
        """Test validation fails for unknown command."""
        result = sovd_protocol_handler.validate_command("InvalidCommand", {})
        assert result is not None
        assert "unknown command" in result.lower() or "invalidcommand" in result.lower()

    def test_validate_additional_properties_rejected(self):
        """Test validation fails when additional properties are provided."""
        result = sovd_protocol_handler.validate_command(
            "ReadDTC", {"ecuAddress": "0x10", "extraParam": "value"}
        )
        assert result is not None


class TestEncodeCommand:
    """Test cases for encode_command function."""

    def test_encode_command_returns_dict(self):
        """Test encode_command returns a dictionary."""
        result = sovd_protocol_handler.encode_command(
            "ReadDTC", {"ecuAddress": "0x10"}
        )
        assert isinstance(result, dict)
        assert result["command_name"] == "ReadDTC"
        assert result["command_params"] == {"ecuAddress": "0x10"}


class TestDecodeResponse:
    """Test cases for decode_response function."""

    def test_decode_response_returns_dict(self):
        """Test decode_response returns a dictionary."""
        payload = {"status": "success", "data": []}
        result = sovd_protocol_handler.decode_response(payload)
        assert isinstance(result, dict)
        assert result == payload
```

### Step 7: Run Tests and Linters

After implementation, run:
1. `python -m pytest backend/tests/unit/test_sovd_protocol_handler.py -v --cov=app.services.sovd_protocol_handler --cov-report=term-missing` - ensure ≥80% coverage
2. `python -m ruff check backend/app/services/sovd_protocol_handler.py` - ensure no linting errors
3. `python -m mypy backend/app/services/sovd_protocol_handler.py` - ensure no type errors
4. Test the API integration by running the full test suite

### Critical Notes

- The JSON schema MUST use exact property names matching the vehicle_connector.py expectations: `ecuAddress`, `dataId`, `dtcCode`
- Validation MUST be stricter than the vehicle connector - reject unknown commands before they reach the connector
- The API endpoint MUST return 400 Bad Request when validation fails (not 404 or 500)
- Test coverage MUST be ≥80% for the protocol handler module
- All structured logging MUST use `structlog.get_logger(__name__)` pattern
