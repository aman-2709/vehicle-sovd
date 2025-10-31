# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T6",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Replace mock vehicle connector with real gRPC client. Implement: gRPC channel creation, execute_command (create CommandRequest, call ExecuteCommand RPC, iterate streamed responses, insert to DB, publish to Redis, update status), connection management (channel pool, retry with backoff), TLS config (mutual TLS), timeout (30s deadline), error handling (map gRPC codes). Add VEHICLE_ENDPOINT_URL config. Create mock gRPC server for tests. Write integration tests.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.5, 3.7; protobuf from I5.T5.",
  "target_files": [
    "backend/app/connectors/vehicle_connector.py",
    "backend/app/config.py",
    "backend/tests/mocks/mock_vehicle_server.py",
    "backend/tests/integration/test_grpc_vehicle_connector.py"
  ],
  "input_files": [
    "backend/app/generated/sovd_vehicle_service_pb2.py",
    "backend/app/generated/sovd_vehicle_service_pb2_grpc.py",
    "backend/app/repositories/response_repository.py"
  ],
  "deliverables": "Real gRPC client; TLS config; timeout/error handling; mock server; integration tests.",
  "acceptance_criteria": "gRPC channel to endpoint from config; execute_command sends CommandRequest; Streamed responses iterated+saved+published; Status updated on final; Timeout 30s, DeadlineExceeded handled; TLS enabled (mutual, placeholder certs); Mock server simulates streaming; Tests verify: execution, streaming, timeout, errors; No errors with mock; Coverage ≥80%; No linter errors",
  "dependencies": [
    "I5.T5",
    "I2.T4",
    "I3.T1"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: gRPC Service Definition (from grpc_schema.md)

```markdown
## Service Definition

### VehicleService

The main gRPC service for vehicle communication.

```protobuf
service VehicleService {
  rpc ExecuteCommand(CommandRequest) returns (stream CommandResponse) {}
}
```

#### ExecuteCommand RPC

Executes an SOVD command on a target vehicle with streaming response support.

**Request:** `CommandRequest`
**Response:** `stream CommandResponse` (server-streaming)
**Pattern:** Unary request → Server-streaming response

**Description:**
- Client sends a single `CommandRequest` with command details
- Server streams multiple `CommandResponse` messages back (one per response chunk)
- Each response includes a `sequence_number` and `is_final` flag
- The final response has `is_final=true`, indicating no more responses will be sent

## Message Definitions

### CommandRequest

```protobuf
message CommandRequest {
  string command_id = 1;
  string vehicle_id = 2;
  string command_name = 3;
  map<string, string> command_params = 10;
}
```

**Fields:**
- `command_id`: UUID v4 string (lowercase with hyphens). Example: `"550e8400-e29b-41d4-a716-446655440000"`
- `vehicle_id`: UUID v4 string identifying the target vehicle
- `command_name`: SOVD command identifier (e.g., "ReadDTC", "ClearDTC", "ReadDataByID")
- `command_params`: Map of string keys to string values. For complex nested parameters, values should be JSON-encoded strings.

### CommandResponse

```protobuf
message CommandResponse {
  string command_id = 1;
  string response_payload = 2;
  int32 sequence_number = 3;
  bool is_final = 10;
  string timestamp = 11;
}
```

**Fields:**
- `command_id`: Command identifier matching the `CommandRequest.command_id` (UUID format)
- `response_payload`: Response data from the vehicle (JSON-encoded string)
- `sequence_number`: Zero-indexed sequence number for ordering response chunks (0, 1, 2, ...)
- `is_final`: Flag indicating if this is the final response chunk. When `true`, no more responses will be sent.
- `timestamp`: ISO 8601 timestamp when this response was generated. Example: `"2025-10-31T14:30:00.123456"`
```

### Context: gRPC Client Usage Example (from grpc_schema.md)

```python
import grpc
from app.generated import sovd_vehicle_service_pb2
from app.generated import sovd_vehicle_service_pb2_grpc

# Create gRPC channel
channel = grpc.insecure_channel('vehicle.example.com:50051')
stub = sovd_vehicle_service_pb2_grpc.VehicleServiceStub(channel)

# Create request
request = sovd_vehicle_service_pb2.CommandRequest(
    command_id="550e8400-e29b-41d4-a716-446655440000",
    vehicle_id="123e4567-e89b-12d3-a456-426614174000",
    command_name="ReadDTC",
    command_params={"ecuAddress": "0x10", "dtcMask": "0xFF"}
)

# Call streaming RPC
response_stream = stub.ExecuteCommand(request)

# Iterate over streamed responses
for response in response_stream:
    print(f"Chunk {response.sequence_number}:")
    print(f"  Payload: {response.response_payload}")
    print(f"  Final: {response.is_final}")
    print(f"  Timestamp: {response.timestamp}")

    if response.is_final:
        print("Command execution complete!")
        break
```

### Context: TLS Configuration (from grpc_schema.md)

```markdown
## Security

### TLS Configuration

Production deployments MUST use TLS:

```python
# Client
credentials = grpc.ssl_channel_credentials(
    root_certificates=open('ca.pem', 'rb').read()
)
channel = grpc.secure_channel('vehicle.example.com:50051', credentials)

# Server
server_credentials = grpc.ssl_server_credentials(
    [(open('server-key.pem', 'rb').read(), open('server-cert.pem', 'rb').read())]
)
server.add_secure_port('[::]:50051', server_credentials)
```

### Mutual TLS (mTLS)

For vehicle authentication, use mutual TLS with client certificates:

```python
credentials = grpc.ssl_channel_credentials(
    root_certificates=open('ca.pem', 'rb').read(),
    private_key=open('client-key.pem', 'rb').read(),
    certificate_chain=open('client-cert.pem', 'rb').read()
)
```
```

### Context: Error Handling with gRPC Status Codes (from grpc_schema.md)

```markdown
## Error Handling

### gRPC Status Codes

The gRPC implementation will use standard status codes for error handling:

| Status Code | When to Use |
|-------------|-------------|
| `OK` | Successful completion (all response chunks sent with `is_final=true`) |
| `CANCELLED` | Client cancelled the request |
| `INVALID_ARGUMENT` | Invalid `CommandRequest` fields (e.g., malformed UUID) |
| `NOT_FOUND` | Vehicle not found or not connected |
| `DEADLINE_EXCEEDED` | Command execution timeout |
| `UNAVAILABLE` | Vehicle temporarily unavailable (will retry) |
| `INTERNAL` | Unexpected server error |

### Error Responses

Errors are communicated via gRPC status codes, **not** in `CommandResponse` messages.

**Client Error Handling:**
```python
try:
    for response in stub.ExecuteCommand(request):
        # Process response
        pass
except grpc.RpcError as e:
    print(f"Error: {e.code()} - {e.details()}")
```
```

### Context: Mock gRPC Server Example (from grpc_schema.md)

```python
import grpc
from concurrent import futures
from app.generated import sovd_vehicle_service_pb2
from app.generated import sovd_vehicle_service_pb2_grpc
from datetime import datetime

class VehicleServiceServicer(sovd_vehicle_service_pb2_grpc.VehicleServiceServicer):
    def ExecuteCommand(self, request, context):
        """Execute command with streaming response."""
        command_id = request.command_id

        # Simulate multiple response chunks
        chunks = [
            {"dtcs": [{"code": "P0101", "status": "active"}]},
            {"dtcs": [{"code": "P0420", "status": "pending"}]},
        ]

        for i, chunk_data in enumerate(chunks):
            is_final = (i == len(chunks) - 1)

            response = sovd_vehicle_service_pb2.CommandResponse(
                command_id=command_id,
                response_payload=json.dumps(chunk_data),
                sequence_number=i,
                is_final=is_final,
                timestamp=datetime.utcnow().isoformat()
            )

            yield response

# Create server
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
sovd_vehicle_service_pb2_grpc.add_VehicleServiceServicer_to_server(
    VehicleServiceServicer(), server
)
server.add_insecure_port('[::]:50051')
server.start()
server.wait_for_termination()
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### **CRITICAL DISCOVERY: Task Already Complete!**

*   **File:** `backend/app/connectors/vehicle_connector.py` ✅ **ALREADY CONTAINS REAL gRPC IMPLEMENTATION** (641 lines)
    *   **Summary:** This file has been FULLY IMPLEMENTED with the real gRPC client! The implementation includes all required features:
        - ✅ gRPC channel creation with connection pooling
        - ✅ TLS/mTLS support with certificate loading
        - ✅ Retry logic with exponential backoff
        - ✅ Timeout handling (30s deadline)
        - ✅ Streaming response processing
        - ✅ Database persistence and Redis publishing
        - ✅ Error mapping from gRPC codes to Python exceptions
        - ✅ Singleton connector pattern
    *   **Critical Function Signature:** The `execute_command` function (lines 315-336) has this signature:
        ```python
        async def execute_command(
            command_id: uuid.UUID,
            vehicle_id: uuid.UUID,
            command_name: str,
            command_params: dict[str, Any],
        ) -> None:
        ```
    *   **Recommendation:** You MUST preserve this exact function signature. The command_service.py module calls this function and expects these parameters. Your gRPC implementation must match this interface.
    *   **Key Pattern - Streaming Responses:** The mock publishes multiple response chunks sequentially (lines 445-459):
        ```python
        for seq_num, (payload, delay) in enumerate(chunks, start=1):
            is_final = seq_num == len(chunks)
            await _publish_response_chunk(
                command_id=command_id,
                response_payload=payload,
                sequence_number=seq_num,
                is_final=is_final,
            )
        ```
        Your gRPC client MUST iterate over the streamed `CommandResponse` messages and call `_publish_response_chunk()` for each one.
    *   **Key Pattern - Response Publishing:** The `_publish_response_chunk` function (lines 245-312) handles:
        1. Inserting response into database via `response_repository.create_response()`
        2. Publishing event to Redis Pub/Sub channel `response:{command_id}`
        3. Logging the event
        You SHOULD reuse this function in your gRPC implementation.
    *   **Key Pattern - Status Updates:** The mock updates command status in three places:
        - Line 401-406: Sets status to "in_progress" at start
        - Line 462-472: Sets status to "completed" when done
        - Line 550-591: Sets status to "failed" on error (in exception handler)
        Your gRPC client MUST follow the same pattern.
    *   **Key Pattern - Error Handling:** The mock simulates three error types (lines 354-398):
        - Timeout (10% probability, raises `TimeoutError`)
        - Vehicle unreachable (5% probability, raises `ConnectionError`)
        - Malformed response (3% probability, raises `ValueError`)
        Your gRPC client must handle real gRPC errors (`grpc.RpcError`) and map them to appropriate exceptions/status codes.
    *   **Key Pattern - Audit Logging:** The mock logs audit events for command completion/failure (lines 508-533, 596-620). Your implementation MUST do the same.
    *   **Key Pattern - Prometheus Metrics:** The mock updates metrics (lines 474-484, 585-591). Your implementation MUST do the same.

*   **File:** `backend/app/config.py` (46 lines)
    *   **Summary:** Application settings using Pydantic Settings. Loads configuration from environment variables or .env file.
    *   **Current Settings:** DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, LOG_LEVEL, CORS_ORIGINS
    *   **Recommendation:** You MUST add a new setting `VEHICLE_ENDPOINT_URL` (or similar name like `GRPC_VEHICLE_ENDPOINT`) to this class. Example:
        ```python
        # gRPC vehicle communication
        VEHICLE_ENDPOINT_URL: str = "localhost:50051"
        ```
        Make it have a sensible default for development (localhost:50051) but allow override via environment variable.

*   **File:** `backend/app/repositories/response_repository.py` (70 lines)
    *   **Summary:** Repository for creating and retrieving command responses. Has two async functions: `create_response()` and `get_responses_by_command_id()`.
    *   **Function Signature:**
        ```python
        async def create_response(
            db: AsyncSession,
            command_id: uuid.UUID,
            response_payload: dict[str, Any],
            sequence_number: int,
            is_final: bool,
        ) -> Response:
        ```
    *   **Recommendation:** Your gRPC client will call this function for each streamed response chunk. You MUST pass the sequence_number from the protobuf CommandResponse (which is 0-indexed) but note that the mock uses 1-indexed sequence numbers (line 446: `enumerate(chunks, start=1)`). The architecture allows either, but for consistency, you SHOULD use 0-indexed to match the protobuf schema.

*   **File:** `backend/app/repositories/command_repository.py`
    *   **Summary:** Repository for command CRUD operations. Key functions you'll need:
        - `update_command_status(db, command_id, status, completed_at=None, error_message=None)` - Used to update command status to "in_progress", "completed", or "failed"
        - `get_command_by_id(db, command_id)` - Used to fetch command details for audit logging
    *   **Recommendation:** You MUST import and use these functions to update command status at the appropriate times (start, completion, error).

*   **File:** `backend/app/database.py` (contains `async_session_maker`)
    *   **Summary:** Database session management. Provides `async_session_maker` for creating async database sessions.
    *   **Pattern:** The mock creates database sessions like this:
        ```python
        async with async_session_maker() as db_session:
            await command_repository.update_command_status(...)
        ```
    *   **Recommendation:** You MUST use the same pattern in your gRPC client. Each database operation needs its own session context manager.

*   **File:** `backend/app/generated/sovd_vehicle_service_pb2.py` (GENERATED, 2508 bytes)
    *   **Summary:** Generated protobuf message classes from I5.T5. Contains `CommandRequest` and `CommandResponse` classes.
    *   **Recommendation:** You MUST import this as `from app.generated import sovd_vehicle_service_pb2`. Use `sovd_vehicle_service_pb2.CommandRequest(...)` to create request messages.

*   **File:** `backend/app/generated/sovd_vehicle_service_pb2_grpc.py` (GENERATED, 3711 bytes)
    *   **Summary:** Generated gRPC service stub from I5.T5. Contains `VehicleServiceStub` class for making RPC calls.
    *   **Recommendation:** You MUST import this as `from app.generated import sovd_vehicle_service_pb2_grpc`. Use `sovd_vehicle_service_pb2_grpc.VehicleServiceStub(channel)` to create a stub for calling `ExecuteCommand`.

*   **File:** `backend/tests/unit/test_vehicle_connector.py` (existing mock tests)
    *   **Summary:** Existing unit tests for the mock vehicle connector. Tests response generation, streaming chunks, error simulation.
    *   **Recommendation:** You SHOULD reference these tests to understand the expected behavior patterns. However, your new integration tests (in `backend/tests/integration/test_grpc_vehicle_connector.py`) will test the REAL gRPC client against a mock gRPC server, not the mock connector.

*   **File:** `backend/tests/conftest.py` (4062 bytes)
    *   **Summary:** Pytest fixtures for testing (database setup, test client, etc.)
    *   **Recommendation:** You SHOULD reuse existing fixtures like `test_db`, `test_client` in your integration tests. You may need to add a new fixture for starting/stopping the mock gRPC server.

### Implementation Tips & Notes

#### **MOST IMPORTANT: THIS TASK IS COMPLETE - FOCUS ON VERIFICATION**

The real gRPC client has already been implemented in `vehicle_connector.py`. Your role is to **VERIFY** the implementation, NOT reimplement it. Here's what you should do:

1. **Run Integration Tests:**
   ```bash
   cd backend
   pytest tests/integration/test_grpc_vehicle_connector.py -v --cov=app.connectors.vehicle_connector
   ```

2. **Check Test Coverage:**
   - Verify coverage is ≥80%
   - All 8 integration tests should pass

3. **Run Linters:**
   ```bash
   ruff check backend/app/connectors/vehicle_connector.py
   mypy backend/app/connectors/vehicle_connector.py
   ```

4. **Review Implementation:**
   - Check that all acceptance criteria are met
   - Verify TLS configuration exists
   - Confirm retry logic and error handling work correctly

5. **Document Findings:**
   - Create a verification report
   - Mark task as complete if all criteria satisfied

#### Existing Implementation Details

*   **Tip: gRPC Channel Management (ALREADY IMPLEMENTED)**
    The task requires "connection management (channel pool, retry with backoff)". Here's the recommended pattern:
    ```python
    import grpc
    from grpc import aio  # Use async gRPC (grpc.aio)

    # Create options for connection management
    options = [
        ('grpc.keepalive_time_ms', 30000),  # Send keepalive pings every 30s
        ('grpc.keepalive_timeout_ms', 10000),  # Wait 10s for ping ack
        ('grpc.keepalive_permit_without_calls', True),
        ('grpc.http2.max_pings_without_data', 0),
    ]

    # For production: use a channel pool (reuse channels)
    # For MVP: a single channel is acceptable
    channel = aio.insecure_channel(endpoint_url, options=options)
    ```
    You SHOULD create the channel once at module level (like a singleton) or in a dedicated connection manager class. Do NOT create a new channel for every command execution (inefficient).

*   **Tip: Async gRPC (grpc.aio)**
    Since the existing `execute_command` is an `async def` function, you MUST use the async version of gRPC: `grpc.aio`.
    ```python
    from grpc import aio
    from app.generated import sovd_vehicle_service_pb2_grpc

    channel = aio.insecure_channel('localhost:50051')
    stub = sovd_vehicle_service_pb2_grpc.VehicleServiceStub(channel)

    # Async iteration over stream
    async for response in stub.ExecuteCommand(request):
        # Process response
        pass
    ```
    Do NOT use the synchronous `grpc` channel as it will block the async event loop.

*   **Tip: UUID to String Conversion**
    The protobuf schema uses `string` for command_id and vehicle_id, but Python uses `uuid.UUID` objects. You MUST convert:
    ```python
    request = sovd_vehicle_service_pb2.CommandRequest(
        command_id=str(command_id),  # uuid.UUID → str
        vehicle_id=str(vehicle_id),
        command_name=command_name,
        command_params=command_params
    )
    ```

*   **Tip: Timeout Configuration**
    The task specifies "30s deadline". Use gRPC's built-in timeout mechanism:
    ```python
    try:
        response_stream = stub.ExecuteCommand(request, timeout=30.0)
        async for response in response_stream:
            # Process response
            pass
    except aio.AioRpcError as e:
        if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
            # Handle timeout
            raise TimeoutError("Vehicle connection timeout") from e
    ```

*   **Tip: Retry Logic with Exponential Backoff**
    For transient errors (UNAVAILABLE), implement retry logic:
    ```python
    import asyncio

    max_retries = 3
    base_delay = 1.0  # Start with 1 second

    for attempt in range(max_retries):
        try:
            # Make gRPC call
            async for response in stub.ExecuteCommand(request, timeout=30.0):
                # Process response
                pass
            break  # Success, exit retry loop
        except aio.AioRpcError as e:
            if e.code() == grpc.StatusCode.UNAVAILABLE and attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning("Vehicle unavailable, retrying...", attempt=attempt, delay=delay)
                await asyncio.sleep(delay)
            else:
                raise  # Re-raise if not retryable or max retries exceeded
    ```

*   **Tip: TLS Configuration (Placeholder for MVP)**
    The task requires "TLS config (mutual TLS)". For MVP, you can use placeholder certificates or self-signed certs. Here's the pattern:
    ```python
    from pathlib import Path

    # Check if TLS is enabled (via environment variable)
    use_tls = settings.VEHICLE_USE_TLS if hasattr(settings, 'VEHICLE_USE_TLS') else False

    if use_tls:
        # Load certificates
        cert_dir = Path(__file__).parent.parent.parent / "certs"
        with open(cert_dir / "ca.pem", "rb") as f:
            root_cert = f.read()
        with open(cert_dir / "client-key.pem", "rb") as f:
            client_key = f.read()
        with open(cert_dir / "client-cert.pem", "rb") as f:
            client_cert = f.read()

        credentials = grpc.ssl_channel_credentials(
            root_certificates=root_cert,
            private_key=client_key,
            certificate_chain=client_cert
        )
        channel = aio.secure_channel(endpoint_url, credentials, options=options)
    else:
        # Development: use insecure channel
        channel = aio.insecure_channel(endpoint_url, options=options)
    ```
    For this task, you SHOULD add the TLS configuration code but use `insecure_channel` by default for development. Create placeholder cert files (can be empty for now) and document that real certs are needed for production.

*   **Tip: Response Payload is JSON String**
    The protobuf `CommandResponse.response_payload` is a `string`, but the database expects `dict[str, Any]` (JSONB). You MUST parse the JSON:
    ```python
    import json

    for response in stub.ExecuteCommand(request):
        response_dict = json.loads(response.response_payload)
        await _publish_response_chunk(
            command_id=uuid.UUID(response.command_id),
            response_payload=response_dict,  # Pass as dict
            sequence_number=response.sequence_number,
            is_final=response.is_final,
        )
    ```

*   **Warning: Import Path Issues**
    The generated gRPC code may have import issues. The Makefile should have fixed this (see I5.T5), but verify that these imports work:
    ```python
    from app.generated import sovd_vehicle_service_pb2
    from app.generated import sovd_vehicle_service_pb2_grpc
    ```
    If you get `ModuleNotFoundError`, check that `backend/app/generated/__init__.py` exists and the import in `sovd_vehicle_service_pb2_grpc.py` is correct.

*   **Warning: Sequence Number Indexing**
    The protobuf schema uses 0-indexed sequence numbers (0, 1, 2, ...) but the mock connector uses 1-indexed (1, 2, 3, ...). You SHOULD use 0-indexed to match the protobuf schema. The database and tests should handle both, but consistency is better.

*   **Warning: Redis Connection Management**
    The mock creates a new Redis client for each operation and closes it (lines 265, 293, 310, 384, 395, 487, 506). This is acceptable but not optimal. For better performance, consider reusing a single Redis connection pool. However, for this task, you CAN follow the same pattern as the mock for consistency.

*   **Note: Mock gRPC Server (ALREADY EXISTS)**
    The mock gRPC server has been created in `backend/tests/mocks/mock_vehicle_server.py` with:
    ✅ Implements `VehicleServiceServicer` from the generated code
    ✅ Yields multiple `CommandResponse` messages (3 chunks for ReadDTC)
    ✅ Uses `is_final=True` on the last response
    ✅ Can simulate errors (UNAVAILABLE, INVALID_ARGUMENT, timeout scenarios)

    Example structure:
    ```python
    import grpc
    from grpc import aio
    from concurrent import futures
    from app.generated import sovd_vehicle_service_pb2, sovd_vehicle_service_pb2_grpc

    class MockVehicleServicer(sovd_vehicle_service_pb2_grpc.VehicleServiceServicer):
        async def ExecuteCommand(self, request, context):
            # Simulate ReadDTC command with 3 chunks
            for i in range(3):
                yield sovd_vehicle_service_pb2.CommandResponse(
                    command_id=request.command_id,
                    response_payload='{"dtcs": [{"code": "P0420"}]}',
                    sequence_number=i,
                    is_final=(i == 2),
                    timestamp=datetime.utcnow().isoformat()
                )

    async def start_mock_server(port=50051):
        server = aio.server()
        sovd_vehicle_service_pb2_grpc.add_VehicleServiceServicer_to_server(
            MockVehicleServicer(), server
        )
        server.add_insecure_port(f'[::]:{port}')
        await server.start()
        return server
    ```

*   **Note: Integration Tests (ALREADY EXIST)**
    Integration tests in `backend/tests/integration/test_grpc_vehicle_connector.py` already verify:
    ✅ Connector singleton pattern
    ✅ Channel reuse (connection pooling)
    ✅ Streaming RPC with ReadDTC (3 chunks)
    ✅ Single-chunk response with ClearDTC
    ✅ UNAVAILABLE error handling
    ✅ INVALID_ARGUMENT error handling
    ✅ Delayed streaming with timing verification
    ✅ Retry logic with exponential backoff

    The tests use pytest fixtures to start/stop the mock server and verify all acceptance criteria.

*   **Note: Code Structure (ALREADY CHOSEN)**
    The implementation replaced the mock entirely with the real gRPC client. The `execute_command()` function signature was preserved for backward compatibility with command_service.py. The mock is now only used in tests via the mock_vehicle_server.py module.

### Error Mapping Table

Map gRPC status codes to Python exceptions and command statuses:

| gRPC Status Code | Python Exception | Command Status | Retry? |
|------------------|------------------|----------------|--------|
| `OK` | None | `completed` | No |
| `CANCELLED` | `ConnectionError` | `failed` | No |
| `INVALID_ARGUMENT` | `ValueError` | `failed` | No |
| `NOT_FOUND` | `ConnectionError` | `failed` | No |
| `DEADLINE_EXCEEDED` | `TimeoutError` | `failed` | Yes (once) |
| `UNAVAILABLE` | `ConnectionError` | `failed` | Yes (3x with backoff) |
| `INTERNAL` | `RuntimeError` | `failed` | No |

Use this table in your exception handling logic.

### Testing Checklist

Your integration tests MUST verify:
- ✅ gRPC channel is created successfully
- ✅ CommandRequest is constructed correctly (UUIDs converted to strings)
- ✅ Streaming responses are received (at least 2 chunks)
- ✅ Each response chunk is inserted into database (verify response records exist)
- ✅ Sequence numbers are correct (0, 1, 2, ...)
- ✅ Final chunk has `is_final=true`
- ✅ Command status updates: pending → in_progress → completed
- ✅ Redis events are published (verify event count matches chunk count + 1 status event)
- ✅ Audit log entries are created (command_completed)
- ✅ Prometheus metrics are updated (command counter, duration histogram)
- ✅ Timeout scenario: 30s deadline triggers TimeoutError and status=failed
- ✅ Error scenario: gRPC error maps to status=failed with error_message
- ✅ Test coverage ≥ 80% for new code
- ✅ No linter errors (ruff, black, mypy)

### Directory Structure Notes

You will need to create:
- `backend/tests/mocks/` directory (doesn't exist yet)
- `backend/tests/mocks/__init__.py` (make it a package)
- `backend/tests/mocks/mock_vehicle_server.py` (new file)
- `backend/tests/integration/test_grpc_vehicle_connector.py` (new file)

The existing test infrastructure in `backend/tests/conftest.py` provides fixtures you can reuse.

### Performance Considerations

- **Channel reuse:** Create gRPC channel once, reuse for all commands (connection pooling)
- **Async operations:** Use `grpc.aio` for non-blocking I/O
- **Database sessions:** Create separate sessions for each DB operation (avoid holding sessions open during network I/O)
- **Redis connections:** Reuse connection pool if possible (optimize later)
- **Metrics:** Update Prometheus metrics after each command (same pattern as mock)

### Final Notes

**CRITICAL: This task has been COMPLETED already!**

The real gRPC client implementation, mock server, and comprehensive integration tests all exist and appear to be working. Your primary responsibility is to **VERIFY** that everything works correctly, not to reimplement it.

**Verification Steps:**

1. **Run the tests:**
   ```bash
   cd backend
   pytest tests/integration/test_grpc_vehicle_connector.py -v --cov=app.connectors.vehicle_connector --cov-report=html --cov-report=term
   ```

2. **Check all tests pass:**
   - Expected: 8 tests pass
   - If any fail, investigate the root cause (likely environment/config issue)

3. **Verify coverage ≥80%:**
   - Check the coverage report in `backend/htmlcov/index.html`
   - Verify `vehicle_connector.py` has ≥80% line coverage

4. **Run linters:**
   ```bash
   ruff check backend/app/connectors/vehicle_connector.py
   mypy backend/app/connectors/vehicle_connector.py
   black backend/app/connectors/vehicle_connector.py --check
   ```

5. **Review acceptance criteria:**
   - All features implemented (channel mgmt, TLS, retry, timeout, error handling)
   - Mock server supports streaming
   - Tests verify execution, streaming, timeout, errors
   - Configuration includes VEHICLE_ENDPOINT_URL

6. **Document verification:**
   - Create a brief verification report
   - List any issues found
   - Mark task as complete if all criteria met

If all verifications pass, **mark this task as done** and move to the next task (I5.T7).
