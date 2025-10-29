# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T4",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Implement `backend/app/repositories/response_repository.py` with async functions: `create_response(command_id, response_payload, sequence_number, is_final, db_session)`, `get_responses_by_command_id(command_id, db_session)`. Add function to `command_service.py`: `get_command_responses(command_id, db_session)` (retrieves all responses for a command, ordered by sequence_number). Create `backend/app/schemas/response.py` Pydantic model: `ResponseDetail`. Add endpoint to `backend/app/api/v1/commands.py`: `GET /api/v1/commands/{command_id}/responses` (returns list of responses). Write integration tests in `backend/tests/integration/test_command_api.py` covering response retrieval.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.7 (API Endpoints - Command Endpoints); Data Model (responses table).",
  "target_files": [
    "backend/app/repositories/response_repository.py",
    "backend/app/schemas/response.py",
    "backend/app/api/v1/commands.py",
    "backend/app/services/command_service.py",
    "backend/tests/integration/test_command_api.py"
  ],
  "input_files": [
    "backend/app/models/response.py",
    "backend/app/services/command_service.py"
  ],
  "deliverables": "Response repository with create/retrieve functions; API endpoint to fetch command responses; tests.",
  "acceptance_criteria": "`GET /api/v1/commands/{command_id}/responses` returns empty list if no responses; Manually inserted response (via database or test fixture) is returned correctly; Responses ordered by sequence_number (ascending); Response payload (JSONB) correctly serialized to JSON in API response; Integration tests cover: fetching responses for command with 0, 1, and multiple responses; Test coverage ≥ 80%; No linter errors",
  "dependencies": [
    "I2.T3"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Command Response Pattern (from Architecture Blueprint Section 3.7)

**Streaming Responses:**
The SOVD command execution system supports streaming responses from vehicles. When a command is executed:
- The vehicle may send multiple response chunks (e.g., diagnostic data streaming)
- Each response chunk is stored as a separate record in the `responses` table
- Each chunk has a `sequence_number` to maintain proper ordering
- The final chunk is marked with `is_final=true` to indicate completion
- The `response_payload` is stored as JSONB to allow flexible schema

**API Endpoint:**
- `GET /api/v1/commands/{command_id}/responses` - Retrieve all response chunks for a command
  - Returns list of responses ordered by sequence_number (ascending)
  - Requires JWT authentication
  - Returns empty list if no responses exist (not 404)
  - Each response includes: response_id, response_payload, sequence_number, is_final, received_at

### Context: Data Model - Responses Table

Based on the Response model in `backend/app/models/response.py`, the responses table structure is:

**Fields:**
- `response_id`: UUID (Primary Key)
- `command_id`: UUID (Foreign Key to commands, CASCADE on delete)
- `response_payload`: JSONB - Flexible JSON data from vehicle
- `sequence_number`: Integer - Order of response chunks (starts at 1)
- `is_final`: Boolean (default false) - Marks the last response chunk
- `received_at`: DateTime (timezone-aware, auto-generated)

**Key Constraints:**
- UNIQUE constraint on (command_id, sequence_number) - Prevents duplicate sequence numbers
- NOT NULL on command_id, response_payload, sequence_number
- CASCADE DELETE - Responses deleted when parent command is deleted

**Indexes:**
- Primary index on response_id
- Index on command_id for efficient lookups
- Index on received_at for time-based queries

### Context: JSONB Serialization

PostgreSQL JSONB fields are automatically handled by SQLAlchemy and Pydantic:
- SQLAlchemy's `JSON` type (mapped to JSONB in PostgreSQL) stores Python dicts/lists
- When reading from database, JSONB is converted to Python dict automatically
- Pydantic schemas serialize dicts to JSON in API responses
- No special conversion logic needed - use `dict[str, Any]` type hint

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/app/models/response.py` (READ IN FULL)

```python
class Response(Base):
    """Streaming command responses with sequence tracking."""

    __tablename__ = "responses"

    response_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    command_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("commands.command_id", ondelete="CASCADE"), nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSONB(astext_type=Text()), nullable=False)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    command: Mapped["Command"] = relationship("Command", back_populates="responses")
```

**Analysis:**
- The model is complete and production-ready
- Uses JSONB with Text() astext_type for PostgreSQL compatibility
- Has server_default for is_final (false) and received_at (CURRENT_TIMESTAMP)
- Bidirectional relationship with Command model via back_populates
- You MUST import this model exactly as-is in response_repository.py

#### File: `backend/app/services/command_service.py` (READ IN FULL)

**Key Functions:**
- `submit_command()` - Creates and submits commands
- `get_command_by_id()` - Retrieves single command
- `get_command_history()` - Lists commands with filtering

**Pattern Observed:**
```python
async def get_command_by_id(command_id: uuid.UUID, db_session: AsyncSession) -> Command | None:
    logger.info("command_retrieval", command_id=str(command_id))
    command = await command_repository.get_command_by_id(db_session, command_id)

    if command:
        logger.info("command_found", command_id=str(command_id))
    else:
        logger.warning("command_not_found", command_id=str(command_id))

    return command
```

**Recommendation:**
- You MUST add `get_command_responses()` function to this file
- Follow the existing pattern: log at entry, call repository, log result, return
- Function signature: `async def get_command_responses(command_id: uuid.UUID, db_session: AsyncSession) -> list[Response]`
- Import Response model from app.models.response
- Import response_repository (you'll create this)
- Return empty list (not None) if no responses found

#### File: `backend/app/api/v1/commands.py` (READ IN FULL - 191 lines)

**Existing Endpoints:**
1. `POST /api/v1/commands` - Submit command (lines 25-80)
2. `GET /api/v1/commands/{command_id}` - Get command details (lines 82-130)
3. `GET /api/v1/commands` - List commands (lines 132-191)

**Pattern for GET endpoints:**
```python
@router.get("/commands/{command_id}", response_model=CommandResponse)
async def get_command(
    command_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommandResponse:
    logger.info("api_get_command", command_id=str(command_id), user_id=str(current_user.user_id))

    command = await command_service.get_command_by_id(command_id=command_id, db_session=db)

    if command is None:
        logger.warning("api_get_command_not_found", command_id=str(command_id))
        raise HTTPException(status_code=404, detail="Command not found")

    logger.info("api_get_command_success", command_id=str(command_id))
    return CommandResponse.model_validate(command)
```

**Recommendation:**
- You MUST add the new endpoint to this file: `GET /api/v1/commands/{command_id}/responses`
- Place it after the existing `get_command()` endpoint (around line 131)
- Follow the exact pattern: logging, service call, error handling
- IMPORTANT: Do NOT return 404 if command has no responses - return empty list with 200 OK
- Response model: `list[ResponseDetail]` (you'll create ResponseDetail schema)
- You will need to add import for ResponseDetail schema

#### File: `backend/app/repositories/command_repository.py` (READ IN FULL - 137 lines)

**Pattern Analysis:**

```python
async def create_command(db: AsyncSession, user_id: uuid.UUID, vehicle_id: uuid.UUID,
                         command_name: str, command_params: dict[str, Any]) -> Command:
    command = Command(
        command_id=uuid.uuid4(),
        user_id=user_id,
        vehicle_id=vehicle_id,
        command_name=command_name,
        command_params=command_params,
    )
    db.add(command)
    await db.commit()
    await db.refresh(command)
    return command

async def get_command_by_id(db: AsyncSession, command_id: uuid.UUID) -> Command | None:
    result = await db.execute(select(Command).where(Command.command_id == command_id))
    return result.scalar_one_or_none()

async def get_commands(db: AsyncSession, vehicle_id: uuid.UUID | None = None,
                       user_id: uuid.UUID | None = None, status: str | None = None,
                       limit: int = 50, offset: int = 0) -> list[Command]:
    query = select(Command)

    if vehicle_id is not None:
        query = query.where(Command.vehicle_id == vehicle_id)
    if user_id is not None:
        query = query.where(Command.user_id == user_id)
    if status is not None:
        query = query.where(Command.status == status)

    query = query.order_by(Command.submitted_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())
```

**Key Patterns:**
- **Create pattern:** Create object → db.add() → await db.commit() → await db.refresh() → return
- **Get single:** select() → where() → await db.execute() → result.scalar_one_or_none()
- **Get multiple:** select() → where() → order_by() → limit/offset → await db.execute() → result.scalars().all() → convert to list
- **Type hints:** Always use proper return types (Model, Model | None, list[Model])
- **Parameter order:** db is always first parameter

**Recommendation for response_repository.py:**
- You MUST follow these exact patterns
- For `create_response()`: Use the create pattern (construct → add → commit → refresh → return)
- For `get_responses_by_command_id()`: Use the get multiple pattern with order_by(Response.sequence_number)

#### File: `backend/tests/integration/test_command_api.py` (READ IN FULL - 537 lines)

**Test Structure:**
- Organized into test classes (TestSubmitCommandEndpoint, TestGetCommandEndpoint, TestListCommandsEndpoint)
- Uses pytest fixtures: async_client, engineer_auth_headers, test_engineer, db_session
- Uses mocking with `@patch` and `AsyncMock` for service layer
- Comprehensive test coverage: success cases, error cases, auth failures, validation errors

**Example Test:**
```python
@pytest.mark.asyncio
async def test_get_command_success(
    self,
    async_client: AsyncClient,
    engineer_auth_headers: dict[str, str],
    test_commands: list,
):
    """Test getting a command by ID."""
    command = test_commands[0]

    with patch("app.api.v1.commands.command_service") as mock_service:
        mock_service.get_command_by_id = AsyncMock(return_value=command)

        response = await async_client.get(
            f"/api/v1/commands/{command.command_id}",
            headers=engineer_auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["command_id"] == str(command.command_id)
```

**Recommendation:**
- You MUST add new test class `TestGetCommandResponsesEndpoint` to this file
- Use the same fixtures and patterns as existing tests
- Create mock Response objects similar to mock Command objects
- Test scenarios: 0 responses, 1 response, multiple responses (verify ordering), command not found
- Verify JSON structure includes all Response fields

---

### Implementation Tips & Notes

**Tip #1 - Response Repository Creation Pattern:**
```python
async def create_response(
    db: AsyncSession,
    command_id: uuid.UUID,
    response_payload: dict[str, Any],
    sequence_number: int,
    is_final: bool,
) -> Response:
    response = Response(
        response_id=uuid.uuid4(),
        command_id=command_id,
        response_payload=response_payload,
        sequence_number=sequence_number,
        is_final=is_final,
    )
    db.add(response)
    await db.commit()
    await db.refresh(response)
    return response
```

**Tip #2 - Ordering by Sequence Number:**
When retrieving responses, you MUST order by sequence_number in ascending order:
```python
query = select(Response).where(Response.command_id == command_id).order_by(Response.sequence_number.asc())
```
Or simply: `.order_by(Response.sequence_number)` (ascending is default)

**Tip #3 - Empty List vs 404:**
The acceptance criteria explicitly states: "returns empty list if no responses". This means:
- Do NOT check if command exists first
- Do NOT raise HTTPException(404) if no responses
- Simply return `[]` from service and endpoint
- This is different from get_command_by_id which returns 404 if command not found

**Tip #4 - ResponseDetail Schema:**
Create a Pydantic schema following the existing pattern in `backend/app/schemas/command.py`:
```python
from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import BaseModel, field_serializer

class ResponseDetail(BaseModel):
    response_id: UUID
    command_id: UUID
    response_payload: dict[str, Any]
    sequence_number: int
    is_final: bool
    received_at: datetime

    @field_serializer("response_id", "command_id")
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    model_config = {"from_attributes": True}
```

**Tip #5 - Adding to command_service.py:**
```python
from app.models.response import Response
from app.repositories import response_repository

async def get_command_responses(
    command_id: uuid.UUID, db_session: AsyncSession
) -> list[Response]:
    """
    Retrieve all responses for a command, ordered by sequence number.

    Args:
        command_id: Command UUID
        db_session: Database session

    Returns:
        List of Response objects (empty if no responses)
    """
    logger.info("command_responses_retrieval", command_id=str(command_id))

    responses = await response_repository.get_responses_by_command_id(db_session, command_id)

    logger.info("command_responses_retrieved", command_id=str(command_id), count=len(responses))

    return responses
```

**Tip #6 - Adding Endpoint to commands.py:**
```python
from app.schemas.response import ResponseDetail

@router.get("/commands/{command_id}/responses", response_model=list[ResponseDetail])
async def get_command_responses(
    command_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ResponseDetail]:
    """
    Retrieve all responses for a specific command.

    Returns responses ordered by sequence_number (ascending).
    Returns empty list if no responses exist.

    Args:
        command_id: Command UUID
        current_user: Authenticated user (injected)
        db: Database session (injected)

    Returns:
        List of ResponseDetail objects

    Raises:
        HTTPException 401: Not authenticated
    """
    logger.info(
        "api_get_command_responses",
        command_id=str(command_id),
        user_id=str(current_user.user_id),
    )

    responses = await command_service.get_command_responses(
        command_id=command_id, db_session=db
    )

    logger.info(
        "api_get_command_responses_success",
        command_id=str(command_id),
        count=len(responses),
    )

    return [ResponseDetail.model_validate(r) for r in responses]
```

**Tip #7 - Integration Test Structure:**
```python
class TestGetCommandResponsesEndpoint:
    """Test GET /api/v1/commands/{command_id}/responses endpoint."""

    @pytest.mark.asyncio
    async def test_get_responses_empty(
        self,
        async_client: AsyncClient,
        engineer_auth_headers: dict[str, str],
    ):
        """Test getting responses for command with no responses."""
        command_id = uuid.uuid4()

        with patch("app.api.v1.commands.command_service") as mock_service:
            mock_service.get_command_responses = AsyncMock(return_value=[])

            response = await async_client.get(
                f"/api/v1/commands/{command_id}/responses",
                headers=engineer_auth_headers,
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data == []

    # Add more tests for 1 response, multiple responses, unauthorized, etc.
```

**Warning #1 - JSONB Type Mapping:**
The Response model uses `JSONB(astext_type=Text())` which is PostgreSQL-specific. This may cause issues in SQLite tests (from conftest.py). However, since integration tests mock the service layer, this shouldn't be a problem. The model works correctly with PostgreSQL.

**Warning #2 - Cascade Delete:**
The Response model has `ondelete="CASCADE"` on the command_id foreign key. This means:
- If a command is deleted, all its responses are automatically deleted
- You don't need to manually delete responses when deleting commands
- Be aware of this behavior when writing tests

**Warning #3 - Sequence Number Uniqueness:**
The database has a UNIQUE constraint on (command_id, sequence_number). If you try to create two responses with the same sequence_number for the same command, you'll get an IntegrityError. Handle this appropriately (though it shouldn't happen in normal operation).

**Note #1 - No Command Existence Check:**
Unlike submit_command which validates vehicle existence, this endpoint does NOT need to check if the command exists. Simply query responses by command_id and return whatever is found (even if empty).

**Note #2 - Import Organization:**
Remember to follow the import order pattern:
1. Standard library: `import uuid`, `from datetime import datetime`, `from typing import Any`
2. Third-party: `from sqlalchemy import select`, `from pydantic import BaseModel`
3. Local: `from app.models.response import Response`

**Note #3 - Test Coverage:**
The acceptance criteria requires ≥80% coverage. Your integration tests MUST cover:
1. Empty responses list (command exists but no responses)
2. Single response returned correctly
3. Multiple responses returned in correct order (ascending sequence_number)
4. Unauthorized access (no JWT) returns 403
5. Response payload JSONB correctly serialized to JSON

---

## 4. Files to Create/Modify

### Create Files:
1. **`backend/app/repositories/response_repository.py`** - New file
2. **`backend/app/schemas/response.py`** - New file

### Modify Files:
1. **`backend/app/services/command_service.py`** - Add `get_command_responses()` function
2. **`backend/app/api/v1/commands.py`** - Add `GET /commands/{command_id}/responses` endpoint
3. **`backend/tests/integration/test_command_api.py`** - Add `TestGetCommandResponsesEndpoint` class

---

## 5. Recommended Implementation Order

To minimize errors and enable incremental testing:

1. **Create `backend/app/schemas/response.py`**
   - Pure Pydantic, no dependencies
   - Define ResponseDetail schema
   - Add @field_serializer for UUIDs

2. **Create `backend/app/repositories/response_repository.py`**
   - Import Response model
   - Implement create_response()
   - Implement get_responses_by_command_id() with ordering

3. **Modify `backend/app/services/command_service.py`**
   - Import Response model and response_repository
   - Add get_command_responses() function
   - Follow existing logging pattern

4. **Modify `backend/app/api/v1/commands.py`**
   - Import ResponseDetail schema
   - Add get_command_responses() endpoint
   - Use existing get_current_user dependency

5. **Modify `backend/tests/integration/test_command_api.py`**
   - Add TestGetCommandResponsesEndpoint class
   - Create mock Response objects
   - Test all scenarios from acceptance criteria

6. **Run tests and verify coverage:**
   ```bash
   pytest backend/tests/integration/test_command_api.py::TestGetCommandResponsesEndpoint -v
   pytest --cov=app --cov-report=term
   ```

---

## End of Task Briefing Package

You now have all the information needed to implement I2.T4. This task builds on the existing command infrastructure and adds the ability to retrieve streaming response data. Follow the established patterns, and ensure proper ordering and JSONB serialization.

Good luck, Coder Agent! 🚀
