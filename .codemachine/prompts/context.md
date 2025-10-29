# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T6",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Implement `backend/app/services/sovd_protocol_handler.py` module for SOVD 2.0 command validation and encoding. Create JSON Schema file `docs/api/sovd_command_schema.json` defining structure for SOVD commands (fields: command_name, command_params with types). Implement functions: `validate_command(command_name, command_params)` (validates against JSON Schema, returns validation errors or None), `encode_command(command_name, command_params)` (formats command for vehicle transmission - for now, return as-is since using mock; real implementation would convert to protobuf or SOVD XML), `decode_response(response_payload)` (parses vehicle response - for now, return as-is). Integrate `validate_command` into `command_service.py` `submit_command` function (reject invalid commands with 400 Bad Request). Write unit tests in `backend/tests/unit/test_sovd_protocol_handler.py` covering validation success and failure cases.",
  "agent_type_hint": "BackendAgent",
  "inputs": "SOVD 2.0 specification (assumed knowledge or simplified subset); JSON Schema documentation.",
  "target_files": [
    "backend/app/services/sovd_protocol_handler.py",
    "docs/api/sovd_command_schema.json",
    "backend/app/services/command_service.py",
    "backend/tests/unit/test_sovd_protocol_handler.py"
  ],
  "input_files": [],
  "deliverables": "SOVD protocol validation module with JSON Schema; command validation integrated into API; unit tests.",
  "acceptance_criteria": "JSON Schema defines at least 3 commands: ReadDTC, ClearDTC, ReadDataByID with required parameters; `validate_command(\"ReadDTC\", {\"ecuAddress\": \"0x10\"})` returns None (valid); `validate_command(\"ReadDTC\", {})` returns validation error (missing ecuAddress); `validate_command(\"InvalidCommand\", {})` returns error (unknown command); `POST /api/v1/commands` with invalid command returns 400 with error details; Unit tests cover: valid commands, invalid params, unknown commands; Test coverage ≥ 80%; No linter errors",
  "dependencies": ["I2.T3"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: SOVD Protocol (from Architecture Blueprint)

SOVD (Service-Oriented Vehicle Diagnostics) 2.0 is the communication protocol standard for vehicle diagnostics. The protocol defines:

**Key SOVD Commands:**
- **ReadDTC**: Read Diagnostic Trouble Codes from ECU
  - Required parameters: `ecuAddress` (string, format "0xNN")
  - Returns: List of DTCs with codes, descriptions, and status

- **ClearDTC**: Clear Diagnostic Trouble Codes from ECU
  - Required parameters: `ecuAddress` (string, format "0xNN")
  - Optional parameters: `dtcCode` (string, if specified clears specific DTC)
  - Returns: Confirmation with cleared count

- **ReadDataByID**: Read specific data parameter from ECU
  - Required parameters: `ecuAddress` (string, format "0xNN"), `dataId` (string, format "0xNNNN")
  - Returns: Data value with description and unit

**Protocol Requirements:**
- All commands must validate parameters before transmission
- Invalid commands must be rejected with detailed error messages
- ECU addresses must be in hexadecimal format (0x00 to 0xFF)
- Data IDs must be in hexadecimal format (0x0000 to 0xFFFF)

### Context: Communication Patterns (from Architecture Blueprint Section 3.7)

The SOVD Protocol Handler is a critical component that sits between the Command Service and the Vehicle Connector:

```
User → API → Command Service → [SOVD Protocol Handler] → Vehicle Connector → Vehicle
```

**Responsibilities:**
1. **Validation**: Validate commands against SOVD 2.0 specification before execution
2. **Encoding**: Transform command objects into vehicle-compatible format (protobuf/XML)
3. **Decoding**: Parse vehicle responses into standardized response objects
4. **Error Handling**: Provide detailed validation errors for debugging

### Context: Technology Stack (from Plan Section 2)

- **Validation Library**: jsonschema (Python) for schema-based validation
- **Testing Framework**: pytest with coverage ≥80%
- **Logging**: structlog for structured error logging

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/services/command_service.py`
    *   **Summary:** This file contains the command submission business logic. The `submit_command` function creates command records and triggers async execution via the vehicle connector.
    *   **Recommendation:** You MUST integrate `validate_command` into this file's `submit_command` function. The validation should occur BEFORE creating the command record in the database (line 63). If validation fails, return None and log the validation errors.
    *   **Integration Point:** Add validation between lines 52-63 (after vehicle validation, before command creation).

*   **File:** `backend/app/connectors/vehicle_connector.py`
    *   **Summary:** This file implements the mock vehicle connector with support for ReadDTC, ClearDTC, and ReadDataByID commands. It uses the `MOCK_RESPONSE_GENERATORS` dictionary to map command names to response generator functions.
    *   **Recommendation:** Your JSON schema MUST define the same three commands (ReadDTC, ClearDTC, ReadDataByID) that are supported by this connector. Review the mock response generators (lines 26-127) to understand expected parameter formats.
    *   **Tip:** The connector already expects specific parameter formats (e.g., `ecuAddress` for ReadDTC, `dataId` for ReadDataByID). Your schema validation should enforce these exact parameter names.

*   **File:** `backend/app/repositories/command_repository.py`
    *   **Summary:** This repository handles database operations for commands, including creating command records with the `command_params` JSONB field.
    *   **Note:** The `command_params` field accepts any dictionary structure. Your validation layer ensures only valid SOVD commands reach this repository.

*   **File:** `backend/app/api/v1/commands.py`
    *   **Summary:** This file defines the REST API endpoint `POST /api/v1/commands` that accepts command submissions.
    *   **Recommendation:** When validation fails in the command service, you SHOULD raise an HTTPException with status_code 400 in the API layer. Check if this endpoint currently handles None returns from `submit_command` - you may need to add error handling.

### Implementation Tips & Notes

*   **Tip:** The task specifies creating a JSON Schema file. I recommend structuring it as:
    ```json
    {
      "$schema": "http://json-schema.org/draft-07/schema#",
      "definitions": {
        "ReadDTC": { ... },
        "ClearDTC": { ... },
        "ReadDataByID": { ... }
      }
    }
    ```
    Each command definition should be in the "definitions" section and referenced by the validator.

*   **Note:** Python's `jsonschema` library usage pattern:
    ```python
    from jsonschema import validate, ValidationError

    try:
        validate(instance=command_params, schema=command_schema)
        return None  # No errors
    except ValidationError as e:
        return str(e)  # Return error message
    ```

*   **Warning:** The task says "return as-is" for `encode_command` and `decode_response` since we're using the mock connector. However, you SHOULD add structured logging to these functions indicating they are placeholder implementations. This will help future developers understand they need real implementation for production.

*   **Tip:** For unit tests, I found the project uses AsyncMock for mocking async functions (see `backend/tests/unit/test_vehicle_connector.py`). You can use standard unittest.mock for the SOVD handler since validation functions will likely be synchronous.

*   **Warning:** The acceptance criteria requires "POST /api/v1/commands with invalid command returns 400". Currently, the command service returns None on invalid vehicle. You MUST ensure the API endpoint converts validation failures to HTTP 400 responses. Check the current API implementation and add appropriate error handling if missing.

*   **Tip:** ECU address validation pattern: `^0x[0-9A-Fa-f]{2}$` (matches "0x10", "0xFF", etc.)
    Data ID validation pattern: `^0x[0-9A-Fa-f]{4}$` (matches "0x010C", "0xFFFF", etc.)

*   **Note:** The vehicle connector already handles unknown commands gracefully (lines 186-197 in vehicle_connector.py) by generating a generic success response. Your validator should be STRICTER and reject unknown commands before they reach the connector.

### Project Structure Notes

*   The project uses `app/` as the application root, not `src/`
*   Service modules go in `backend/app/services/`
*   Unit tests mirror the app structure: `backend/tests/unit/test_{module_name}.py`
*   The docs directory exists at project root: `/docs/api/` for API specifications

### Testing Strategy

Based on the test coverage output I reviewed:
- Current connector tests achieve 98% coverage
- Current command service has only 37% coverage (needs improvement from I2.T10)
- Your SOVD handler tests should aim for ≥90% coverage to contribute to the overall 80% target
- Test both synchronous validation functions and integration with the async command service

### Dependencies Already Installed

From `requirements.txt`:
- `pydantic>=2.4.0` - Can use for schema validation if preferred over jsonschema
- `structlog>=23.2.0` - For logging validation errors
- `python-jose[cryptography]>=3.3.0` - Already available (for JWT)

**You NEED to add:** `jsonschema` to `requirements.txt` (not currently installed)

---

## End of Briefing Package

You now have:
1. ✅ Complete task specification (I2.T6)
2. ✅ Architectural context about SOVD protocol and communication patterns
3. ✅ Direct analysis of 4 critical existing files
4. ✅ Specific integration points and recommendations
5. ✅ Testing strategy and dependency information

**CRITICAL NEXT STEPS:**
1. Add `jsonschema` dependency to `requirements.txt`
2. Create the JSON Schema file with 3 command definitions
3. Implement the 3 functions in `sovd_protocol_handler.py`
4. Integrate validation into `command_service.py` (between lines 52-63)
5. Add 400 error handling to `commands.py` API endpoint
6. Write comprehensive unit tests achieving ≥80% coverage
7. Run linters (ruff, mypy) and fix any errors

Remember: This is a CRITICAL component. All invalid commands MUST be blocked before database persistence or vehicle transmission.
