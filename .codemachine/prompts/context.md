# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T5",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Implement `backend/app/connectors/vehicle_connector.py` as a **mock** implementation for development and testing. The mock should: accept `execute_command(vehicle_id, command_name, command_params)` async function, simulate network delay (asyncio.sleep 0.5-1.5 seconds), generate fake SOVD response payload (e.g., for command \"ReadDTC\", return `[{\"dtcCode\": \"P0420\", \"description\": \"Catalyst System Efficiency Below Threshold\"}]`), publish response event to Redis Pub/Sub channel `response:{command_id}`, insert response record into database via response_repository, update command status to `completed`. For now, all commands succeed (no error simulation). Create mapping of common SOVD commands (ReadDTC, ClearDTC, ReadDataByID) to mock response generators. Integrate mock connector into `command_service.py` `submit_command` function to trigger async execution. Write unit tests for mock connector in `backend/tests/unit/test_vehicle_connector.py`.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.5 (Vehicle Connector component); Section 3.7 (Communication Patterns - gRPC).",
  "target_files": [
    "backend/app/connectors/vehicle_connector.py",
    "backend/app/services/command_service.py",
    "backend/tests/unit/test_vehicle_connector.py"
  ],
  "input_files": [
    "backend/app/repositories/response_repository.py",
    "backend/app/services/command_service.py"
  ],
  "deliverables": "Mock vehicle connector that simulates command execution and response generation; integration with command service; unit tests.",
  "acceptance_criteria": "`POST /api/v1/commands` triggers mock connector execution asynchronously; After simulated delay, command status updated to `completed` in database; Response record created in database with mock payload; Response event published to Redis channel `response:{command_id}` (verifiable via Redis CLI: `SUBSCRIBE response:*`); Mock connector supports commands: ReadDTC, ClearDTC, ReadDataByID (with distinct mock responses); Unit tests verify: response generation logic, Redis event publishing; No errors in logs during command execution; No linter errors",
  "dependencies": ["I2.T3", "I2.T4"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Vehicle Connector Component (from 03_System_Structure_and_Data.md)

```markdown
### 3.4. Container Diagram (C4 Level 2)

#### Description

This diagram zooms into the SOVD Command WebApp system boundary and shows the major deployable containers (applications and data stores). Key containers include:

- **Web Application (SPA)**: React-based frontend served as static files
- **API Gateway**: Nginx reverse proxy for routing, TLS termination, and load balancing
- **Application Server**: FastAPI-based backend with modular services
- **WebSocket Server**: Handles real-time streaming responses (embedded in FastAPI)
- **Vehicle Connector Service**: Abstraction layer for vehicle communication protocols
- **PostgreSQL Database**: Primary data store for vehicles, commands, responses, and audit logs
- **Redis Cache**: Session storage and response caching for performance

**Key Information about Vehicle Connector:**

The Vehicle Connector is a container with the following responsibilities:
- Abstracts vehicle communication protocols
- Handles retries and connection pooling
- Sends SOVD commands and receives responses via gRPC/WebSocket over TLS
- Publishes response events to Redis Pub/Sub
- Writes responses to PostgreSQL database

**Relationships:**
- Application Server → Vehicle Connector: "Requests command execution" (Internal API)
- Vehicle Connector → Vehicle: "Sends SOVD commands, receives responses" (gRPC/WebSocket over TLS)
- Vehicle Connector → Redis: "Publishes response events" (Redis Pub/Sub)
- Vehicle Connector → PostgreSQL: "Writes responses" (SQL asyncpg)
```

### Context: Communication Patterns - Event-Driven (from 04_Behavior_and_Communication.md)

```markdown
**3. Event-Driven (Internal via Redis Pub/Sub)**

Used internally between backend components:
- Vehicle Connector publishes response events → WebSocket Server consumes
- Decouples command execution from response delivery
- Enables horizontal scaling of both components

**Flow:**
1. Vehicle Connector receives response from vehicle
2. Publishes event to Redis channel: `response:{command_id}`
3. WebSocket Server (subscribed to channel) receives event
4. Pushes to connected WebSocket clients

**Key Pattern:** The Vehicle Connector acts as a publisher in the Redis Pub/Sub pattern. After receiving a response from the vehicle (or in this case, after generating a mock response), it must:
1. Insert the response into the database via `response_repository.create_response()`
2. Publish an event to the Redis channel `response:{command_id}` containing the response data
3. Update the command status to 'completed' when the final response is received
```

### Context: Communication Patterns - Synchronous Request/Response (from 04_Behavior_and_Communication.md)

```markdown
**1. Synchronous Request/Response (REST)**

Used for:
- Authentication (login, token refresh)
- Vehicle listing and status queries
- Command submission (initial request)
- Historical command/response retrieval

**Flow:**
1. Client sends HTTP request (JSON payload)
2. Server processes synchronously
3. Server returns HTTP response (JSON payload)
4. Client receives complete response

**Example:** `POST /api/v1/auth/login` → returns JWT tokens

**Command Submission Flow:**
`POST /api/v1/commands`
Request:  {
  "vehicle_id": "uuid",
  "command_name": "ReadDTC",
  "command_params": { "ecuAddress": "0x10", "format": "UDS" }
}
Response: {
  "command_id": "uuid",
  "status": "pending",
  "submitted_at": "2025-10-28T10:00:00Z",
  "stream_url": "wss://api.sovd.example.com/ws/responses/{command_id}"
}
```

### Context: Mock Implementation Requirements (from 02_Iteration_I2.md - Plan)

```markdown
**Task 2.5: Implement Mock Vehicle Connector**

**Core Requirements:**
1. Create `backend/app/connectors/vehicle_connector.py` as a **mock** implementation
2. Implement async function: `execute_command(vehicle_id, command_name, command_params)`
3. Simulate network delay: use `asyncio.sleep()` with random delay between 0.5-1.5 seconds
4. Generate mock SOVD response payloads for common commands:
   - **ReadDTC**: Return list of diagnostic trouble codes (DTCs)
   - **ClearDTC**: Return confirmation of DTC clearing
   - **ReadDataByID**: Return vehicle data based on data identifier

**Response Generation Pattern:**
- Each command type should have a dedicated mock response generator function
- Responses should be realistic and structured according to SOVD patterns
- All commands should succeed (no error simulation in this task)

**Integration Points:**
1. Database: Use `response_repository.create_response()` to insert response records
2. Redis Pub/Sub: Publish events to `response:{command_id}` channel
3. Command Status: Use `command_repository.update_command_status()` to mark as 'completed'
4. Command Service: Integrate into `command_service.submit_command()` to trigger async execution

**Testing Requirements:**
- Write unit tests in `backend/tests/unit/test_vehicle_connector.py`
- Test response generation for each command type (ReadDTC, ClearDTC, ReadDataByID)
- Test Redis event publishing (can be verified via Redis CLI: `SUBSCRIBE response:*`)
- Ensure all tests pass and coverage ≥ 80%
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/app/services/command_service.py`
**Summary:** This file contains the business logic for command management. The `submit_command()` function currently creates a command record and immediately marks it as 'in_progress', but does NOT yet trigger actual vehicle communication (as noted in the comment on line 29: "Actual vehicle communication is stubbed for now").

**Recommendation:** You MUST modify the `submit_command()` function in this file to:
1. Import and use your new `vehicle_connector` module
2. After creating the command, trigger async execution by calling `vehicle_connector.execute_command()` as a background task
3. Pass the `command_id`, `vehicle_id`, `command_name`, and `command_params` to the connector
4. Remove or update the stub status update to 'in_progress' since the connector will handle status updates

**Key Code Section (lines 58-89):**
- The command is created with status='pending' (line 59-65)
- Status is then immediately updated to 'in_progress' (lines 74-76) - this is the stub that needs to be replaced
- The function uses structured logging via `structlog` - you SHOULD follow this pattern in your connector

#### File: `backend/app/repositories/response_repository.py`
**Summary:** This repository provides database operations for command responses. It has two key functions:
- `create_response()`: Inserts a new response record (lines 12-45)
- `get_responses_by_command_id()`: Retrieves all responses for a command, ordered by sequence_number (lines 48-69)

**Recommendation:** You MUST use `response_repository.create_response()` in your vehicle connector to persist response data. The function signature is:
```python
async def create_response(
    db: AsyncSession,
    command_id: uuid.UUID,
    response_payload: dict[str, Any],
    sequence_number: int,
    is_final: bool,
) -> Response
```

**Important Notes:**
- `response_payload` is a `dict[str, Any]` that maps to JSONB in PostgreSQL - you can put any JSON-serializable data here
- `sequence_number` should be 1 for the first (and only, in this task) response chunk
- `is_final` should be `True` for the last response in a sequence (always `True` in this task since we're sending single responses)
- You MUST commit the response to the database before publishing to Redis

#### File: `backend/app/repositories/command_repository.py`
**Summary:** This repository provides database operations for commands. Key function for you:
- `update_command_status()`: Updates command status and related fields (lines 67-99)

**Recommendation:** You MUST call `command_repository.update_command_status()` to mark the command as 'completed' after successfully inserting the response. The function signature is:
```python
async def update_command_status(
    db: AsyncSession,
    command_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
    completed_at: datetime | None = None,
) -> Command | None
```

**Important:** Pass `status="completed"` and optionally `completed_at=datetime.now(timezone.utc)` to mark completion timestamp.

#### File: `backend/app/config.py`
**Summary:** Application configuration using Pydantic Settings. Provides access to environment variables including `REDIS_URL`.

**Recommendation:** You MUST import `settings` from this file to get the Redis connection URL:
```python
from app.config import settings
# Use: settings.REDIS_URL
```

**Configuration Available:**
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string (format: `redis://hostname:port/db`)
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRATION_MINUTES`: For auth (not needed in connector)

#### File: `backend/app/database.py`
**Summary:** Database session management with async SQLAlchemy. Provides `get_db()` dependency injection function.

**Recommendation:** You will need a database session in your connector to write responses. However, since the connector will run as a background task, you CANNOT use the `get_db()` dependency. Instead, you SHOULD:
1. Create your own async session using the same pattern from this file
2. Import `async_session_maker` or create a new session from the engine
3. Use a proper async context manager to ensure the session is closed

**Critical Pattern to Follow:**
```python
from app.database import async_session_maker

async def execute_command(...):
    async with async_session_maker() as db_session:
        # Your database operations here
        await db_session.commit()
```

#### File: `backend/app/models/command.py` and `backend/app/models/response.py`
**Summary:** SQLAlchemy ORM models defining database schema.

**Recommendation:** You do NOT need to directly interact with these models in your connector. Use the repository functions instead. However, understanding the data structure is helpful:

**Command model key fields:**
- `command_id`: UUID (primary key)
- `vehicle_id`: UUID (foreign key to vehicles)
- `command_name`: String (e.g., "ReadDTC")
- `command_params`: JSONB dict
- `status`: String ('pending', 'in_progress', 'completed', 'failed')
- `error_message`: Optional string for failures

**Response model key fields:**
- `response_id`: UUID (primary key)
- `command_id`: UUID (foreign key to commands)
- `response_payload`: JSONB dict (your mock data goes here)
- `sequence_number`: Integer (use 1 for single responses)
- `is_final`: Boolean (set to True for last response)

#### File: `backend/tests/conftest.py`
**Summary:** Pytest configuration with fixtures for database sessions and async HTTP clients.

**Recommendation:** For unit tests of your vehicle connector, you SHOULD:
1. Create mock database sessions using pytest fixtures
2. Use `AsyncMock` from `unittest.mock` to mock repository functions
3. Use `pytest.mark.asyncio` decorator for async test functions
4. Follow the existing test patterns (see integration tests for examples)

**Key Patterns:**
- Use `@pytest.fixture` for reusable test data
- Use `@pytest_asyncio.fixture` for async fixtures
- Use `AsyncMock()` to mock async repository functions
- Test Redis publishing by mocking the Redis client

#### File: `backend/tests/integration/test_command_api.py`
**Summary:** Integration tests for command API showing patterns for authentication, fixtures, and mocking.

**Recommendation:** While you're writing unit tests (not integration tests), you SHOULD follow similar patterns:
- Use fixtures for test users and auth tokens
- Use `AsyncMock` with `patch()` for mocking external dependencies
- Test both success and error scenarios
- Verify function calls using `assert_called_once_with()` or similar

### Implementation Tips & Notes

#### Tip 1: Redis Client Setup
You will need to create a Redis client to publish events. The `redis` library (v5.0.0+) is already in `requirements.txt`. Here's the recommended pattern:

```python
import redis.asyncio as redis
from app.config import settings

# Create async Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Publish event
await redis_client.publish(
    f"response:{command_id}",
    json.dumps({"event": "response", "command_id": str(command_id), "response": response_data})
)
```

**Important:** Use `redis.asyncio` (not just `redis`) to get the async client. Set `decode_responses=True` to automatically decode bytes to strings.

#### Tip 2: Simulating Network Delay
Use `asyncio.sleep()` with `random.uniform()` to simulate realistic network delays:

```python
import asyncio
import random

# Simulate network delay between 0.5 and 1.5 seconds
await asyncio.sleep(random.uniform(0.5, 1.5))
```

#### Tip 3: Mock Response Generators
Create a mapping dictionary that maps command names to generator functions:

```python
def _generate_read_dtc_response() -> dict[str, Any]:
    """Generate mock response for ReadDTC command."""
    return {
        "dtcs": [
            {"dtcCode": "P0420", "description": "Catalyst System Efficiency Below Threshold"},
            {"dtcCode": "P0171", "description": "System Too Lean (Bank 1)"}
        ]
    }

MOCK_RESPONSE_GENERATORS = {
    "ReadDTC": _generate_read_dtc_response,
    "ClearDTC": _generate_clear_dtc_response,
    "ReadDataByID": _generate_read_data_by_id_response,
}
```

#### Tip 4: Background Task Execution
In `command_service.py`, you need to trigger the connector asynchronously without blocking the API response. Use FastAPI's `BackgroundTasks`:

```python
from fastapi import BackgroundTasks

# In submit_command function signature, add background_tasks parameter
async def submit_command(
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
    user_id: uuid.UUID,
    db_session: AsyncSession,
    background_tasks: BackgroundTasks,  # Add this parameter
) -> Command | None:
    # ... existing code to create command ...

    # Trigger async execution
    background_tasks.add_task(
        vehicle_connector.execute_command,
        command.command_id,
        vehicle_id,
        command_name,
        command_params,
    )

    return command
```

**Warning:** This will require updating the API endpoint in `backend/app/api/v1/commands.py` to include `BackgroundTasks` as a dependency.

#### Tip 5: Structured Logging
The project uses `structlog` for structured JSON logging. You SHOULD use the same pattern in your vehicle connector:

```python
import structlog

logger = structlog.get_logger(__name__)

# In your functions:
logger.info(
    "mock_command_execution_started",
    command_id=str(command_id),
    vehicle_id=str(vehicle_id),
    command_name=command_name,
)
```

This ensures consistency with the rest of the codebase and makes logs searchable.

#### Tip 6: Error Handling
While this task specifies "all commands succeed (no error simulation)", you SHOULD still wrap your code in try-except blocks to handle unexpected errors gracefully:

```python
try:
    # Your mock execution logic
    pass
except Exception as e:
    logger.error(
        "mock_command_execution_failed",
        command_id=str(command_id),
        error=str(e),
        exc_info=True,
    )
    # Update command status to 'failed'
    # (This is for unexpected errors, not part of the mock simulation)
```

#### Note 1: Docker Compose Environment
The project uses Docker Compose for local development. Redis is available at:
- Inside containers: `redis://redis:6379/0` (using service name)
- From host: `redis://localhost:6379/0`

The `REDIS_URL` environment variable in `docker-compose.yml` is already configured correctly as `redis://redis:6379/0`.

#### Note 2: Project Structure Convention
The project follows a clear separation of concerns:
- `connectors/`: External system communication (your new module goes here)
- `services/`: Business logic
- `repositories/`: Database access
- `api/`: HTTP endpoints
- `models/`: ORM models
- `schemas/`: Pydantic models for validation

Your connector belongs in the `connectors/` package as it abstracts vehicle communication.

#### Note 3: Linting and Type Checking
The project uses:
- **ruff**: For linting (configured in `pyproject.toml`)
- **black**: For code formatting (line-length=100)
- **mypy**: For static type checking (strict mode)

You MUST ensure your code passes all these checks. Use type hints for all function parameters and return values:

```python
async def execute_command(
    command_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any],
) -> None:
    """Execute a mock vehicle command."""
    ...
```

#### Warning: Database Session Management
**CRITICAL:** Since your connector runs as a background task, you CANNOT reuse the request's database session. You MUST create a new session using `async_session_maker`. Failing to do this will cause database connection errors.

**Correct Pattern:**
```python
from app.database import async_session_maker

async def execute_command(...):
    async with async_session_maker() as db:
        # Use db session here
        await response_repository.create_response(db, ...)
        await command_repository.update_command_status(db, ...)
```

**Incorrect Pattern (DO NOT DO THIS):**
```python
# This will fail because the request session is closed
await response_repository.create_response(db_session, ...)  # db_session from request
```

#### Warning: Import Circular Dependencies
Be careful about circular imports. Your connector will be imported by `command_service.py`, which is imported by the API layer. Keep imports minimal and use `TYPE_CHECKING` if you need type hints for models:

```python
from typing import TYPE_CHECKING, Any
import uuid

if TYPE_CHECKING:
    # Only for type hints, not runtime
    from app.models.command import Command
```

---

## Summary of Action Items

Your task is to:

1. **Create** `backend/app/connectors/vehicle_connector.py` with:
   - Async function `execute_command(command_id, vehicle_id, command_name, command_params)`
   - Mock response generators for ReadDTC, ClearDTC, ReadDataByID
   - Network delay simulation (0.5-1.5 seconds)
   - Redis Pub/Sub event publishing to `response:{command_id}`
   - Database persistence via `response_repository` and `command_repository`
   - Structured logging using `structlog`

2. **Modify** `backend/app/services/command_service.py` to:
   - Import your vehicle connector module
   - Add `BackgroundTasks` parameter to `submit_command()`
   - Trigger `execute_command()` as a background task
   - Remove the stub status update to 'in_progress' (connector handles this)

3. **Modify** `backend/app/api/v1/commands.py` to:
   - Add `BackgroundTasks` as a FastAPI dependency in the POST endpoint
   - Pass `background_tasks` to `command_service.submit_command()`

4. **Create** `backend/tests/unit/test_vehicle_connector.py` with:
   - Unit tests for each command type (ReadDTC, ClearDTC, ReadDataByID)
   - Tests for Redis event publishing (using mocks)
   - Tests for database operations (using mocks)
   - Achieve ≥80% test coverage

5. **Verify** acceptance criteria:
   - `POST /api/v1/commands` triggers async execution
   - Command status updates to 'completed' after delay
   - Response records created in database
   - Redis events published (verify with `SUBSCRIBE response:*`)
   - No errors in logs
   - All linters pass (ruff, black, mypy)

Good luck! Follow the existing code patterns closely, and refer to this briefing package whenever you need clarification on architecture decisions or implementation details.
