# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T3",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Implement `backend/app/services/command_service.py` with functions: `submit_command(vehicle_id, command_name, command_params, user_id, db_session)` (validates command, inserts command record with status=pending, triggers async execution via Vehicle Connector - stub for now), `get_command_by_id(command_id, db_session)`, `get_command_history(filters, db_session)` (supports filtering by vehicle_id, user_id, status, pagination). Create `backend/app/schemas/command.py` Pydantic models: `CommandSubmitRequest`, `CommandResponse`, `CommandListResponse`. Implement `backend/app/api/v1/commands.py` FastAPI router with endpoints: `POST /api/v1/commands` (requires `engineer` or `admin` role), `GET /api/v1/commands/{command_id}`, `GET /api/v1/commands` (query params: vehicle_id, status, limit, offset). Implement `backend/app/repositories/command_repository.py` with async functions: `create_command()`, `get_command_by_id()`, `update_command_status()`, `get_commands()`. For now, `submit_command` should create command record and immediately mark it as `in_progress` (actual vehicle communication in I2.T5). Write unit tests in `backend/tests/unit/test_command_service.py` and integration tests in `backend/tests/integration/test_command_api.py`.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.7 (API Endpoints - Command Endpoints); Data Model (commands table).",
  "target_files": [
    "backend/app/services/command_service.py",
    "backend/app/schemas/command.py",
    "backend/app/api/v1/commands.py",
    "backend/app/repositories/command_repository.py",
    "backend/tests/unit/test_command_service.py",
    "backend/tests/integration/test_command_api.py"
  ],
  "input_files": [
    "backend/app/models/command.py",
    "backend/app/database.py",
    "backend/app/dependencies.py"
  ],
  "deliverables": "Functional command submission and retrieval API; basic command service logic (without vehicle communication yet); unit and integration tests.",
  "acceptance_criteria": "`POST /api/v1/commands` with valid payload creates command record (status=pending or in_progress); `POST /api/v1/commands` requires authentication (401 if no JWT); `POST /api/v1/commands` requires `engineer` or `admin` role (403 for other roles); `POST /api/v1/commands` validates vehicle_id exists (400 if invalid); `POST /api/v1/commands` returns command_id and status; `GET /api/v1/commands/{command_id}` returns command details (name, params, status, timestamps); `GET /api/v1/commands` returns paginated list of commands; `GET /api/v1/commands?vehicle_id={id}` filters by vehicle; `GET /api/v1/commands?status=completed` filters by status; Unit tests cover: command validation, status transitions; Integration tests cover: all endpoints with success and error cases; Test coverage ≥ 80%; No linter errors",
  "dependencies": ["I2.T1", "I2.T2"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Command Endpoints (from Architecture Blueprint Section 3.7)

Based on the task inputs referencing "Architecture Blueprint Section 3.7 (API Endpoints - Command Endpoints)", the command API should follow REST conventions and support the following operations:

**Command Submission:**
- `POST /api/v1/commands` - Submit a new command to a vehicle
  - Request body: command_name, vehicle_id, command_params (JSONB)
  - Response: command_id, status, submitted_at
  - Requires JWT authentication
  - Requires RBAC: `engineer` or `admin` role

**Command Retrieval:**
- `GET /api/v1/commands/{command_id}` - Get details of a specific command
  - Returns: command_id, command_name, vehicle_id, user_id, status, command_params, error_message, submitted_at, completed_at

**Command History:**
- `GET /api/v1/commands` - List commands with filtering and pagination
  - Query parameters: vehicle_id, status, limit, offset
  - Supports filtering by vehicle and status
  - Pagination with limit/offset pattern

### Context: Data Model - Commands Table (from ERD and Database Schema)

The `commands` table structure (as defined in `backend/app/models/command.py`):

**Fields:**
- `command_id`: UUID (Primary Key)
- `user_id`: UUID (Foreign Key to users, CASCADE on delete)
- `vehicle_id`: UUID (Foreign Key to vehicles, CASCADE on delete)
- `command_name`: String(100) - SOVD command identifier
- `command_params`: JSONB - Command-specific parameters
- `status`: String(20) - Lifecycle status ('pending', 'in_progress', 'completed', 'failed')
- `error_message`: Text (nullable) - Error message if failed
- `submitted_at`: DateTime (timezone-aware, auto-generated)
- `completed_at`: DateTime (timezone-aware, nullable)

**Relationships:**
- `user`: Many-to-one relationship with User
- `vehicle`: Many-to-one relationship with Vehicle
- `responses`: One-to-many relationship with Response (cascade delete)
- `audit_logs`: One-to-many relationship with AuditLog

**Status Lifecycle:**
1. `pending` - Initial state when command is submitted
2. `in_progress` - Command is being executed by vehicle connector
3. `completed` - Command executed successfully
4. `failed` - Command execution failed (error_message populated)

### Context: RBAC Requirements (from Architecture Blueprint Section 3.8)

**Role-Based Access Control:**
- Two primary roles: `engineer` and `admin`
- Command submission requires either `engineer` or `admin` role
- Use the existing `require_role()` dependency from `backend/app/dependencies.py`
- Example usage: `Depends(require_role(["engineer", "admin"]))`

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/app/models/command.py`
- **Summary:** This file contains the complete Command SQLAlchemy model with all fields, relationships, and constraints already defined.
- **Recommendation:** You MUST import the `Command` class from this file in your repository and service modules. The model is production-ready and should NOT be modified.
- **Key Attributes:**
  - Primary key: `command_id` (UUID)
  - Foreign keys: `user_id`, `vehicle_id` (both with CASCADE delete)
  - JSONB field: `command_params` with server default `'{}'`
  - Status field has server default `'pending'`
  - Relationships are bidirectional with proper back_populates

#### File: `backend/app/dependencies.py`
- **Summary:** This file provides authentication and authorization dependencies for FastAPI routes.
- **Recommendation:** You MUST use the following dependencies in your API endpoints:
  - `get_current_user` - Validates JWT and returns authenticated User object (use with Depends())
  - `require_role(["engineer", "admin"])` - Factory function that creates role-checking dependency
- **Example Usage Pattern:**
  ```python
  @router.post("/commands")
  async def submit_command(
      current_user: User = Depends(require_role(["engineer", "admin"])),
      db: AsyncSession = Depends(get_db)
  ):
  ```

#### File: `backend/app/database.py`
- **Summary:** This file provides the database session management and async engine configuration.
- **Recommendation:** You MUST import `get_db` from this module and use it as a dependency for database access.
- **Key Features:**
  - Returns AsyncSession via dependency injection
  - Configured with connection pooling (pool_size=20, max_overflow=10)
  - Automatic session cleanup in finally block
  - Structured logging with structlog

#### File: `backend/app/repositories/vehicle_repository.py`
- **Summary:** This is the reference implementation showing the repository pattern used in this project.
- **Recommendation:** You SHOULD follow the exact same pattern for `command_repository.py`:
  - Use async functions with `AsyncSession` as first parameter
  - Return `Model | None` for single record retrieval
  - Return `list[Model]` for multiple records
  - Use SQLAlchemy 2.0 select() syntax: `await db.execute(select(Model).where(...))`
  - Extract results with `.scalar_one_or_none()` (single) or `.scalars().all()` (multiple)
  - For updates: modify object, `await db.commit()`, `await db.refresh(obj)`
- **Pattern Example:**
  ```python
  async def get_command_by_id(db: AsyncSession, command_id: uuid.UUID) -> Command | None:
      result = await db.execute(select(Command).where(Command.command_id == command_id))
      return result.scalar_one_or_none()
  ```

#### File: `backend/app/services/vehicle_service.py`
- **Summary:** This is the reference implementation showing the service layer pattern.
- **Recommendation:** You SHOULD follow this pattern for `command_service.py`:
  - Import structlog and get logger: `logger = structlog.get_logger(__name__)`
  - Service functions orchestrate business logic and call repository functions
  - Use structured logging for all operations: `logger.info("event_name", field1=value1, ...)`
  - Services receive `db: AsyncSession` as parameter and pass to repositories
  - Return domain objects (models) or processed data (dicts)
- **Logging Pattern:**
  ```python
  logger.info("command_submitted", command_id=str(command_id), user_id=str(user_id))
  ```

#### File: `backend/app/api/v1/vehicles.py`
- **Summary:** This is the reference implementation for FastAPI router structure.
- **Recommendation:** You MUST follow this exact pattern for `backend/app/api/v1/commands.py`:
  - Create `router = APIRouter()` at module level
  - Use type hints for all parameters and return types
  - Use Query() for query parameters with validation (ge, le, description)
  - Use UUID type from uuid module for path parameters
  - Use Depends() for dependency injection (get_current_user, get_db)
  - Call service layer functions (not repositories directly)
  - Convert SQLAlchemy models to Pydantic with `.model_validate()`
  - Raise HTTPException(status_code=404, detail="...") for not found
  - Log all requests with user_id and relevant identifiers
- **Endpoint Pattern:**
  ```python
  @router.post("/commands", response_model=CommandResponse)
  async def submit_command(
      request: CommandSubmitRequest,
      current_user: User = Depends(require_role(["engineer", "admin"])),
      db: AsyncSession = Depends(get_db)
  ) -> CommandResponse:
  ```

#### File: `backend/app/schemas/vehicle.py`
- **Summary:** This is the reference implementation for Pydantic schema patterns.
- **Recommendation:** You MUST follow this pattern for `backend/app/schemas/command.py`:
  - Use Pydantic v2 syntax with proper imports from pydantic
  - Inherit from `BaseModel`
  - Use `model_config = {"from_attributes": True}` for ORM compatibility
  - Use `@field_serializer` for custom serialization (e.g., UUID to string)
  - Use `Field()` for defaults and aliases
  - Use proper type hints: `UUID`, `datetime | None`, `dict[str, Any]`
- **Schema Pattern:**
  ```python
  class CommandResponse(BaseModel):
      command_id: UUID
      command_name: str
      status: str

      @field_serializer("command_id")
      def serialize_command_id(self, value: UUID) -> str:
          return str(value)

      model_config = {"from_attributes": True}
  ```

### Implementation Tips & Notes

**Tip #1 - FastAPI Router Registration:**
After creating `backend/app/api/v1/commands.py`, you MUST register the router in `backend/app/main.py`. Check how the auth and vehicles routers are registered and follow the same pattern:
```python
from app.api.v1 import commands
app.include_router(commands.router, prefix="/api/v1", tags=["commands"])
```

**Tip #2 - Vehicle Validation:**
For `POST /api/v1/commands`, you MUST validate that the `vehicle_id` exists before creating the command. Import and use `vehicle_repository.get_vehicle_by_id()`:
```python
vehicle = await vehicle_repository.get_vehicle_by_id(db, request.vehicle_id)
if not vehicle:
    raise HTTPException(status_code=400, detail="Vehicle not found")
```

**Tip #3 - Stub Implementation for Vehicle Connector:**
The task specifies: "For now, `submit_command` should create command record and immediately mark it as `in_progress`". This means:
1. Create command with status='pending' (default from model)
2. Immediately update status to 'in_progress'
3. Do NOT actually communicate with vehicles yet (that's I2.T5)
4. The command will remain in 'in_progress' state indefinitely (acceptable for this iteration)

**Tip #4 - Async Database Operations:**
ALL database operations MUST be awaited:
- `await db.execute(query)` - Execute query
- `await db.commit()` - Commit transaction
- `await db.refresh(obj)` - Refresh object from database
- `db.add(obj)` - Add to session (NOT async, no await needed)

**Tip #5 - Testing Pattern:**
Based on existing test files in `backend/tests/`:
- Use `conftest.py` fixtures for database setup (already exists)
- Import `AsyncSession` and use async test functions
- Use `@pytest.mark.asyncio` decorator for async tests
- Integration tests should use TestClient from httpx or FastAPI
- Mock authentication by overriding `get_current_user` dependency
- Verify HTTP status codes, response schemas, and database state

**Tip #6 - Query Parameter Filtering:**
For `GET /api/v1/commands` with filters, build the query dynamically:
```python
query = select(Command)
if vehicle_id:
    query = query.where(Command.vehicle_id == vehicle_id)
if status:
    query = query.where(Command.status == status)
query = query.limit(limit).offset(offset)
result = await db.execute(query)
commands = result.scalars().all()
```

**Tip #7 - Pagination Response:**
The task specifies `CommandListResponse` schema. This should include pagination metadata like the `VehicleListResponse` pattern (total, limit, offset). However, calculating total count requires a separate COUNT query.

**Tip #8 - Import Organization:**
Follow the import order pattern seen in existing files:
1. Standard library (uuid, datetime)
2. Third-party libraries (structlog, fastapi, sqlalchemy, pydantic)
3. Local app imports (app.models, app.schemas, app.services, app.repositories)

**Warning #1 - Type Hints:**
The codebase uses strict type checking with mypy. You MUST provide type hints for:
- All function parameters
- All function return types
- Pydantic model fields
Use `| None` for optional types (Python 3.10+ syntax, not Optional[])

**Warning #2 - UUID Handling:**
UUIDs are stored as UUID objects in the database but serialized to strings in JSON responses. You MUST:
- Use `uuid.UUID` type for function parameters expecting UUIDs
- Use `@field_serializer` in Pydantic schemas to convert UUID to string
- Parse UUID from strings with `uuid.UUID(string_value)` with try/except for validation

**Warning #3 - Linting Configuration:**
The project uses strict linting (ruff, black, mypy). Before submitting:
- Run `ruff check backend/` - Should pass with no errors
- Run `mypy backend/` - Should pass with no errors
- All code MUST conform to existing style (line length=100 from pyproject.toml)

**Note #1 - Structlog Configuration:**
Structlog is already configured in `backend/app/database.py`. All logging should use structured format:
```python
logger.info("event_name", key1=value1, key2=value2)
# NOT: logger.info(f"Event with {value1}")
```

**Note #2 - RBAC Implementation:**
The `require_role()` function returns a dependency that automatically checks authorization. When a user without required role accesses the endpoint, it returns 403 Forbidden automatically. You do NOT need to manually check roles in endpoint logic.

**Note #3 - Test Coverage:**
The acceptance criteria requires ≥80% test coverage. Use pytest-cov:
```bash
pytest --cov=app --cov-report=html --cov-report=term
```
Focus on testing:
- All API endpoints (success and error cases)
- Command validation logic
- Status transitions
- RBAC enforcement
- Vehicle existence validation

---

## 4. Additional Strategic Guidance

### File Creation Order (Recommended)

To minimize errors and enable incremental testing, create files in this order:

1. **`backend/app/schemas/command.py`** - No dependencies, pure Pydantic
2. **`backend/app/repositories/command_repository.py`** - Depends on: models, database
3. **`backend/app/services/command_service.py`** - Depends on: repositories, schemas
4. **`backend/app/api/v1/commands.py`** - Depends on: all above + dependencies
5. **Register router in `backend/app/main.py`**
6. **`backend/tests/unit/test_command_service.py`** - Unit tests
7. **`backend/tests/integration/test_command_api.py`** - Integration tests

### Schema Definitions Required

Based on task requirements, create these Pydantic schemas:

**CommandSubmitRequest:**
- command_name: str
- vehicle_id: UUID
- command_params: dict[str, Any] (default={})

**CommandResponse:**
- command_id: UUID (serialize to string)
- user_id: UUID (serialize to string)
- vehicle_id: UUID (serialize to string)
- command_name: str
- command_params: dict[str, Any]
- status: str
- error_message: str | None
- submitted_at: datetime
- completed_at: datetime | None

**CommandListResponse:**
- commands: list[CommandResponse]
- total: int (optional for this iteration)
- limit: int
- offset: int

### Repository Functions Required

**create_command():**
```python
async def create_command(
    db: AsyncSession,
    user_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    command_name: str,
    command_params: dict[str, Any]
) -> Command
```

**get_command_by_id():**
```python
async def get_command_by_id(
    db: AsyncSession,
    command_id: uuid.UUID
) -> Command | None
```

**update_command_status():**
```python
async def update_command_status(
    db: AsyncSession,
    command_id: uuid.UUID,
    status: str,
    error_message: str | None = None,
    completed_at: datetime | None = None
) -> Command | None
```

**get_commands():**
```python
async def get_commands(
    db: AsyncSession,
    vehicle_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0
) -> list[Command]
```

### Service Functions Required

**submit_command():**
- Validate vehicle exists (call vehicle_repository)
- Create command with status='pending'
- Update status to 'in_progress' (stub for vehicle communication)
- Return command object

**get_command_by_id():**
- Call repository
- Return command or None

**get_command_history():**
- Call repository with filters
- Return list of commands

### Endpoint Specifications

**POST /api/v1/commands:**
- Request: CommandSubmitRequest body
- Response: CommandResponse (201 Created)
- Auth: require_role(["engineer", "admin"])
- Validate: vehicle_id exists
- Logic: Call submit_command service

**GET /api/v1/commands/{command_id}:**
- Path: command_id UUID
- Response: CommandResponse (200 OK) or 404
- Auth: get_current_user
- Logic: Call get_command_by_id service

**GET /api/v1/commands:**
- Query: vehicle_id, status, limit (default 50), offset (default 0)
- Response: list[CommandResponse] or CommandListResponse (200 OK)
- Auth: get_current_user
- Logic: Call get_command_history service

### Testing Strategy

**Unit Tests (test_command_service.py):**
- Test submit_command with valid/invalid vehicle_id
- Test get_command_by_id with existing/non-existing id
- Test get_command_history with various filters
- Mock repository layer

**Integration Tests (test_command_api.py):**
- Test POST /api/v1/commands success (201)
- Test POST /api/v1/commands without auth (401)
- Test POST /api/v1/commands without required role (403)
- Test POST /api/v1/commands with invalid vehicle_id (400)
- Test GET /api/v1/commands/{command_id} success (200)
- Test GET /api/v1/commands/{command_id} not found (404)
- Test GET /api/v1/commands with filters
- Test GET /api/v1/commands pagination
- Verify database state after each operation

---

## End of Task Briefing Package

You now have all the information needed to implement I2.T3. Follow the patterns established in the codebase, use the existing utilities and dependencies, and ensure all acceptance criteria are met.

Good luck, Coder Agent! 🚀
