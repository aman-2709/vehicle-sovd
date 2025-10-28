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
  "dependencies": [
    "I2.T1",
    "I2.T2"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: API Design - Command Endpoints (from Architecture Blueprint)

Based on the task inputs referencing "Architecture Blueprint Section 3.7 (API Endpoints - Command Endpoints)", the command API should follow RESTful conventions and support:

**Command Submission Endpoint:**
- `POST /api/v1/commands` - Submit a new SOVD command to a vehicle
- Request body: `{ "vehicle_id": "uuid", "command_name": "string", "command_params": { ... } }`
- Response: `{ "command_id": "uuid", "status": "pending|in_progress", "submitted_at": "timestamp" }`
- Authentication: Required (JWT Bearer token)
- Authorization: Requires `engineer` or `admin` role

**Command Retrieval Endpoints:**
- `GET /api/v1/commands/{command_id}` - Get details of a specific command
- `GET /api/v1/commands` - List commands with pagination and filtering
  - Query parameters: `vehicle_id`, `status`, `limit`, `offset`, `user_id`
- Response format: Standard pagination with `items`, `total`, `limit`, `offset`

**Status Values:**
The command lifecycle includes these status values:
- `pending` - Command submitted but not yet sent to vehicle
- `in_progress` - Command is being executed on the vehicle
- `completed` - Command execution finished successfully
- `failed` - Command execution failed

### Context: Data Model - Commands Table (from Database Schema)

The Command model includes:
- `command_id` (UUID, primary key)
- `user_id` (UUID, foreign key to users table, CASCADE on delete)
- `vehicle_id` (UUID, foreign key to vehicles table, CASCADE on delete)
- `command_name` (VARCHAR(100), required)
- `command_params` (JSONB, required, default '{}')
- `status` (VARCHAR(20), required, default 'pending')
- `error_message` (TEXT, nullable)
- `submitted_at` (TIMESTAMP, auto-generated)
- `completed_at` (TIMESTAMP, nullable)

**Relationships:**
- Many-to-one with User (command.user_id → user.user_id)
- Many-to-one with Vehicle (command.vehicle_id → vehicle.vehicle_id)
- One-to-many with Response (command.command_id ← response.command_id)
- One-to-many with AuditLog (command.command_id ← audit_log.command_id)

**Database Indexes:**
Critical indexes for query performance:
- `idx_commands_user_id` on `user_id`
- `idx_commands_vehicle_id` on `vehicle_id`
- `idx_commands_status` on `status`
- `idx_commands_submitted_at` on `submitted_at DESC`

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/app/models/command.py`
**Summary:** This file defines the complete Command ORM model with all required fields and relationships. It uses SQLAlchemy 2.0 async style with proper type hints.

**Critical Details:**
- The Command model is already fully implemented with:
  - UUID primary key with auto-generation
  - Foreign keys to users and vehicles with CASCADE delete
  - JSONB field for command_params with server default '{}'
  - Status field with server default 'pending'
  - Proper relationships to User, Vehicle, Response, and AuditLog models
  - Type hints using `Mapped[]` syntax

**Recommendation:** You MUST import `Command` from this file. DO NOT create a new model. Use this exact model for all database operations.

---

#### File: `backend/app/models/response.py`
**Summary:** Defines the Response model for storing ordered response chunks from vehicle command execution.

**Critical Details:**
- Response model includes `sequence_number` for ordering streaming responses
- Has `is_final` boolean flag to identify the last chunk
- Uses JSONB for `response_payload`
- Foreign key to commands with CASCADE delete

**Note:** This is for future use in I2.T4. You won't interact with this model in I2.T3, but be aware it exists for the complete architecture.

---

#### File: `backend/app/dependencies.py`
**Summary:** Provides FastAPI dependency injection functions for authentication and authorization, including RBAC enforcement.

**Critical Functions:**
1. `get_current_user(credentials, db)` - Validates JWT and returns authenticated User object
   - Raises 401 if token invalid or user not found/inactive
   - Returns User model instance

2. `require_role(allowed_roles)` - Factory function for role-based access control
   - Returns dependency function that checks user role
   - Raises 403 if user doesn't have required role
   - Depends on `get_current_user`

**MANDATORY Usage:**
- For `POST /api/v1/commands`: Use `user: User = Depends(require_role(["engineer", "admin"]))`
- For `GET /api/v1/commands/*`: Use `current_user: User = Depends(get_current_user)`
- This pattern is already proven in `backend/app/api/v1/auth.py` and `backend/app/api/v1/vehicles.py`

**Example Pattern (from vehicles.py):**
```python
@router.get("/vehicles", response_model=VehicleListResponse)
async def get_vehicles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ...
```

---

#### File: `backend/app/database.py`
**Summary:** Database connection and session management module with async SQLAlchemy support.

**Critical Details:**
- Exports `get_db()` async generator for dependency injection
- Uses async SQLAlchemy 2.0 with asyncpg driver
- Session configured with `expire_on_commit=False` (prevents lazy loading errors)
- Connection pooling: pool_size=20, max_overflow=10
- Structured logging configured with structlog (JSON output)

**MANDATORY Usage:**
- Always use `db: AsyncSession = Depends(get_db)` in FastAPI route parameters
- Use `await db.execute()` for queries
- Use `await db.commit()` to persist changes
- Use `await db.flush()` if you need IDs before commit

---

#### File: `backend/app/services/auth_service.py`
**Summary:** Complete authentication service with JWT token management, password hashing, and user authentication.

**Key Functions:**
- `hash_password(password)` - Bcrypt hashing
- `verify_password(plain, hashed)` - Password verification
- `create_access_token(user_id, username, role)` - JWT generation (15 min expiry)
- `authenticate_user(db, username, password)` - Database authentication

**Pattern to Follow:**
- This service file shows the exact pattern you should follow for `command_service.py`
- Uses structlog for logging with structured fields
- All functions have complete docstrings with Args, Returns sections
- Async functions use `AsyncSession` type hint
- Returns None on failure, data on success

---

#### File: `backend/app/repositories/vehicle_repository.py`
**Summary:** Data access layer for vehicle operations showing the repository pattern used in this project.

**Critical Pattern (example from this file):**
```python
async def get_vehicle_by_id(db: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle | None:
    """Get vehicle by ID."""
    result = await db.execute(
        select(Vehicle).where(Vehicle.vehicle_id == vehicle_id)
    )
    return result.scalar_one_or_none()
```

**Recommendation:** You MUST follow this exact pattern in `command_repository.py`:
- Use `select()` from sqlalchemy
- Use `await db.execute()`
- Use `.scalar_one_or_none()` for single results
- Use `.scalars().all()` for multiple results
- Return `None` for not found, raise no exceptions

---

#### File: `backend/tests/conftest.py`
**Summary:** Pytest configuration with fixtures for database sessions and async HTTP client.

**Critical Details:**
- Uses SQLite (file-based: `test.db`) for testing
- Creates fresh session for each test function
- Only creates User and Session tables (other tables use PostgreSQL-specific JSONB)
- Provides `db_session` fixture for database tests
- Provides `async_client` fixture with dependency override

**IMPORTANT LIMITATION:**
The test fixtures currently only support User and Session tables. For testing Commands, you have TWO options:

**Option 1 (Recommended):** Update conftest.py to include Command and Vehicle tables
- Import Command and Vehicle models
- Add `Command.__table__.create()` and `Vehicle.__table__.create()`
- Add corresponding drops in teardown
- This allows full integration testing

**Option 2:** Use integration tests against PostgreSQL via docker-compose
- Tests run slower but use real database
- No SQLite compatibility issues with JSONB

---

#### File: `backend/tests/integration/test_auth_api.py`
**Summary:** Comprehensive integration tests showing the exact testing pattern to follow.

**Key Testing Patterns Demonstrated:**

1. **Test Organization:**
   - Classes group related tests (e.g., `TestLoginEndpoint`)
   - Each test method has clear, descriptive name
   - Tests cover: success cases, validation errors, auth failures, edge cases

2. **Test Structure:**
   ```python
   @pytest.mark.asyncio
   async def test_<scenario>(self, async_client, db_session):
       # 1. Setup: Create test data
       # 2. Execute: Call API endpoint
       # 3. Assert: Verify response status and data
       # 4. Verify: Check database state if needed
   ```

3. **Database Setup Pattern:**
   ```python
   user = User(username="test", password_hash=hash_password("pass"), ...)
   db_session.add(user)
   await db_session.commit()  # or flush() if need ID immediately
   ```

4. **API Call Pattern:**
   ```python
   response = await async_client.post(
       "/api/v1/commands",
       json={"vehicle_id": str(vehicle_id), "command_name": "ReadDTC", ...},
       headers={"Authorization": f"Bearer {access_token}"}
   )
   ```

5. **Assertion Pattern:**
   ```python
   assert response.status_code == status.HTTP_200_OK
   data = response.json()
   assert "command_id" in data
   assert data["status"] in ["pending", "in_progress"]
   ```

6. **End-to-End Test Example:**
   See `test_complete_auth_flow()` - shows how to chain multiple operations

**MANDATORY for I2.T3:**
You MUST create similar test classes:
- `TestSubmitCommandEndpoint` - test POST /api/v1/commands
- `TestGetCommandEndpoint` - test GET /api/v1/commands/{id}
- `TestListCommandsEndpoint` - test GET /api/v1/commands with filters
- Cover ALL acceptance criteria scenarios

---

### Implementation Tips & Notes

#### Tip #1: Project Code Style Conventions
After reviewing multiple files, the project follows these strict conventions:
- **Imports:** Group into stdlib, third-party, local (with blank lines between)
- **Type Hints:** ALWAYS use type hints (SQLAlchemy 2.0 `Mapped[]` in models, standard hints elsewhere)
- **Docstrings:** Google-style docstrings for all functions with Args, Returns, Raises sections
- **Async:** All database operations are async (use `async def` and `await`)
- **Logging:** Use structlog with structured fields (key=value format)
- **Error Handling:** Use FastAPI `HTTPException` with appropriate status codes

#### Tip #2: FastAPI Router Pattern
Based on `auth.py` and `vehicles.py`, follow this exact structure for `commands.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, require_role, get_db
from app.schemas.command import CommandSubmitRequest, CommandResponse, CommandListResponse
from app.services import command_service

router = APIRouter(prefix="/api/v1/commands", tags=["commands"])

@router.post("", response_model=CommandResponse, status_code=status.HTTP_201_CREATED)
async def submit_command(
    request: CommandSubmitRequest,
    current_user: User = Depends(require_role(["engineer", "admin"])),
    db: AsyncSession = Depends(get_db)
):
    """Submit a new SOVD command to a vehicle."""
    ...
```

#### Tip #3: Pydantic Schema Pattern
Based on existing schemas, use this pattern:
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

class CommandSubmitRequest(BaseModel):
    vehicle_id: uuid.UUID
    command_name: str = Field(..., min_length=1, max_length=100)
    command_params: dict = Field(default_factory=dict)

class CommandResponse(BaseModel):
    command_id: uuid.UUID
    vehicle_id: uuid.UUID
    command_name: str
    command_params: dict
    status: str
    submitted_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # Enables ORM mode for SQLAlchemy models
```

#### Tip #4: Status Transition Logic
For I2.T3, the task says "immediately mark it as in_progress". Implement this in `submit_command`:
1. Create Command with status='pending'
2. Flush to get command_id
3. Update status to 'in_progress'
4. Commit
5. Log status change

This prepares for I2.T5 where actual vehicle communication will be triggered.

#### Tip #5: Pagination Pattern
For `get_command_history()`, implement standard pagination:
- Accept `limit` (default 50, max 100) and `offset` (default 0)
- Return total count + items
- Use SQLAlchemy `limit()` and `offset()` methods
- Return format: `{"items": [...], "total": N, "limit": L, "offset": O}`

#### Warning #1: JSONB Compatibility
The `command_params` field is JSONB in PostgreSQL. In integration tests:
- If using SQLite (current conftest.py), JSONB becomes TEXT
- SQLite doesn't support JSON operators (no `command_params->>'key'` queries)
- For I2.T3, basic CRUD is fine with SQLite
- For advanced filtering (future tasks), you'll need PostgreSQL tests

#### Warning #2: Vehicle Validation
`POST /api/v1/commands` MUST validate that `vehicle_id` exists:
```python
vehicle = await vehicle_repository.get_vehicle_by_id(db, request.vehicle_id)
if not vehicle:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Vehicle with ID {request.vehicle_id} not found"
    )
```

#### Warning #3: Test Coverage Requirement
The task requires ≥80% coverage. Make sure you test:
- ✅ Success case (valid command submission)
- ✅ Auth failure (no token → 401)
- ✅ Auth failure (invalid token → 401)
- ✅ Authorization failure (wrong role → 403)
- ✅ Validation error (missing fields → 422)
- ✅ Validation error (invalid vehicle_id → 400)
- ✅ Get command by ID (found → 200)
- ✅ Get command by ID (not found → 404)
- ✅ List commands with no filters
- ✅ List commands filtered by vehicle_id
- ✅ List commands filtered by status
- ✅ List commands with pagination (limit/offset)

#### Note #1: Logging Best Practices
Follow the structured logging pattern from auth_service.py:
```python
logger.info(
    "command_submitted",
    command_id=str(command_id),
    user_id=str(user_id),
    vehicle_id=str(vehicle_id),
    command_name=command_name
)
```

#### Note #2: Error Response Format
All error responses should be consistent:
```python
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Clear, user-friendly error message"
)
```

#### Note #3: Linting Requirements
The project uses:
- `ruff` for linting (configured in pyproject.toml)
- `black` for formatting (line length 100)
- `mypy` for type checking (strict mode)

Before committing, all code must pass:
```bash
ruff check backend/
black backend/
mypy backend/
```

---

## 4. Execution Checklist

Use this checklist to ensure all acceptance criteria are met:

### Core Functionality
- [ ] `POST /api/v1/commands` creates command with status=pending, then in_progress
- [ ] `POST /api/v1/commands` requires authentication (JWT)
- [ ] `POST /api/v1/commands` requires engineer or admin role
- [ ] `POST /api/v1/commands` validates vehicle_id exists
- [ ] `POST /api/v1/commands` returns command_id and status
- [ ] `GET /api/v1/commands/{command_id}` returns full command details
- [ ] `GET /api/v1/commands` returns paginated list
- [ ] `GET /api/v1/commands?vehicle_id={id}` filters by vehicle
- [ ] `GET /api/v1/commands?status={status}` filters by status
- [ ] `GET /api/v1/commands?limit=X&offset=Y` supports pagination

### Code Quality
- [ ] All functions have complete docstrings
- [ ] All functions have type hints
- [ ] Structured logging in all service functions
- [ ] No linter errors (ruff, black, mypy)
- [ ] Code follows existing patterns (auth_service, vehicle_service)

### Testing
- [ ] Unit tests for command_service.py functions
- [ ] Integration tests for all API endpoints
- [ ] Test coverage ≥ 80%
- [ ] All acceptance criteria scenarios tested
- [ ] Tests pass consistently

### Files Created
- [ ] backend/app/services/command_service.py
- [ ] backend/app/schemas/command.py
- [ ] backend/app/api/v1/commands.py
- [ ] backend/app/repositories/command_repository.py
- [ ] backend/tests/unit/test_command_service.py
- [ ] backend/tests/integration/test_command_api.py

---

## 5. Key Architectural Decisions

### Why Status Transitions: pending → in_progress?
The task specifies creating the command with status=pending, then immediately updating to in_progress. This design:
1. Provides a clear audit trail of command lifecycle
2. Prepares for I2.T5 where async vehicle communication is added
3. Allows monitoring of commands that are "stuck" in pending state
4. Separates command creation from execution trigger

### Why Repository Pattern?
The codebase uses the repository pattern to:
1. Separate data access logic from business logic
2. Make testing easier (can mock repositories)
3. Provide single source of truth for database queries
4. Follow Domain-Driven Design principles

### Why Separate Service and Repository?
- **Repository:** Pure data access (CRUD operations)
- **Service:** Business logic (validation, orchestration, status transitions)
- **API Router:** HTTP handling (request/response formatting, auth checks)

This three-layer architecture is consistent across auth and vehicles modules.

---

## 6. Related Future Tasks

After I2.T3 is complete, the next related tasks are:

- **I2.T4:** Response repository and retrieval API (GET /api/v1/commands/{id}/responses)
- **I2.T5:** Mock vehicle connector that actually triggers async command execution
- **I2.T6:** SOVD protocol handler for command validation

Your implementation in I2.T3 should be designed to integrate cleanly with these future additions. Specifically:
- Leave room in `submit_command` for triggering vehicle connector (I2.T5)
- Design command_params validation to be replaceable with SOVD handler (I2.T6)
- Ensure command status tracking supports the full lifecycle

---

**END OF BRIEFING PACKAGE**

```json
{
  "task_id": "I2.T1",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Implement `backend/app/services/auth_service.py` with functions: `create_access_token(user_id, username, role)` (generates JWT), `verify_access_token(token)` (validates and decodes JWT), `hash_password(password)` (bcrypt hash), `verify_password(plain_password, hashed_password)`, `authenticate_user(username, password)` (queries database, verifies password). Create `backend/app/schemas/auth.py` Pydantic models: `LoginRequest`, `TokenResponse`, `UserResponse`. Implement `backend/app/api/v1/auth.py` FastAPI router with endpoints: `POST /api/v1/auth/login` (authenticates user, returns access and refresh tokens), `POST /api/v1/auth/refresh` (validates refresh token from database, issues new access token), `POST /api/v1/auth/logout` (invalidates refresh token), `GET /api/v1/auth/me` (returns current user profile from JWT). Create `backend/app/repositories/user_repository.py` with async functions: `get_user_by_username()`, `get_user_by_id()`, `create_user()`. Implement RBAC dependency: `backend/app/dependencies.py` with `get_current_user(token)` and `require_role(roles: list)` for protecting endpoints. Write unit tests in `backend/tests/unit/test_auth_service.py` and integration tests in `backend/tests/integration/test_auth_api.py`.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Authentication & Authorization); Plan Section 2 (Technology Stack - JWT, passlib); Data Model (users table).",
  "target_files": [
    "backend/app/services/auth_service.py",
    "backend/app/schemas/auth.py",
    "backend/app/api/v1/auth.py",
    "backend/app/repositories/user_repository.py",
    "backend/app/dependencies.py",
    "backend/tests/unit/test_auth_service.py",
    "backend/tests/integration/test_auth_api.py"
  ],
  "input_files": [
    "backend/app/models/user.py",
    "backend/app/models/session.py",
    "backend/app/database.py",
    "backend/app/config.py"
  ],
  "deliverables": "Functional authentication API with JWT generation/validation; RBAC dependency injection; unit and integration tests with 80%+ coverage.",
  "acceptance_criteria": "`POST /api/v1/auth/login` with valid credentials returns access_token and refresh_token; `POST /api/v1/auth/login` with invalid credentials returns 401 Unauthorized; `POST /api/v1/auth/refresh` with valid refresh token returns new access_token; `POST /api/v1/auth/logout` invalidates refresh token (subsequent refresh attempts fail); `GET /api/v1/auth/me` with valid JWT returns user profile (user_id, username, role); `GET /api/v1/auth/me` with missing/invalid JWT returns 401 Unauthorized; `require_role([\"admin\"])` dependency blocks non-admin users (returns 403 Forbidden); Unit tests cover: token generation, token validation, password hashing/verification; Integration tests cover: all auth endpoints with success and error cases; Test coverage ≥ 80% for auth modules; No linter errors (`ruff check`, `mypy`)",
  "dependencies": ["I1.T9", "I1.T10"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Authentication & Authorization Strategy (from 05_Operational_Architecture.md)

```markdown
#### Authentication & Authorization

**Authentication Strategy: JWT-Based with Refresh Tokens**

**Implementation:**
- **Access Tokens**: Short-lived (15 minutes), stateless JWT tokens
  - Contains: `user_id`, `username`, `role`, `exp` (expiration), `iat` (issued at)
  - Signed with HS256 algorithm (HMAC with SHA-256)
  - Validated on every API request via middleware
- **Refresh Tokens**: Long-lived (7 days), stored in database
  - Used to obtain new access tokens without re-authentication
  - Supports token revocation (logout invalidates refresh token)
  - Rotated on each refresh for security

**Authentication Flow:**
1. User submits credentials to `/api/v1/auth/login`
2. Backend validates against database (password hashed with bcrypt)
3. On success, generates access + refresh tokens
4. Client stores access token in memory, refresh token in httpOnly cookie (or local storage with XSS mitigations)
5. Client includes access token in `Authorization: Bearer {token}` header
6. On access token expiration, client calls `/api/v1/auth/refresh` with refresh token
7. Backend validates refresh token, issues new access token

**Authorization Strategy: Role-Based Access Control (RBAC)**

**Roles:**
- **Engineer**: Can view vehicles, execute commands, view command history (own commands)
- **Admin**: Full access (user management, system configuration, all command history)

**Implementation:**
- Role stored in `users.role` field
- Access token JWT includes `role` claim
- FastAPI dependencies enforce authorization:
  ```python
  @router.post("/commands")
  async def execute_command(
      user: User = Depends(require_role(["engineer", "admin"])),
      ...
  ):
  ```
- Unauthorized access returns HTTP 403 Forbidden
```

### Context: Authentication API Endpoints (from 04_Behavior_and_Communication.md)

```markdown
**Authentication Endpoints**

POST   /api/v1/auth/login
Request:  { "username": "string", "password": "string" }
Response: { "access_token": "string", "refresh_token": "string", "expires_in": 900 }

POST   /api/v1/auth/refresh
Request:  { "refresh_token": "string" }
Response: { "access_token": "string", "expires_in": 900 }

POST   /api/v1/auth/logout
Headers:  Authorization: Bearer {token}
Response: { "message": "Logged out successfully" }

GET    /api/v1/auth/me
Headers:  Authorization: Bearer {token}
Response: { "user_id": "uuid", "username": "string", "role": "string" }
```

### Context: Task Requirements (from 02_Iteration_I2.md)

```markdown
**Task 2.1: Implement Authentication Service and API Endpoints**

**Acceptance Criteria:**
- `POST /api/v1/auth/login` with valid credentials returns access_token and refresh_token
- `POST /api/v1/auth/login` with invalid credentials returns 401 Unauthorized
- `POST /api/v1/auth/refresh` with valid refresh token returns new access_token
- `POST /api/v1/auth/logout` invalidates refresh token (subsequent refresh attempts fail)
- `GET /api/v1/auth/me` with valid JWT returns user profile (user_id, username, role)
- `GET /api/v1/auth/me` with missing/invalid JWT returns 401 Unauthorized
- `require_role(["admin"])` dependency blocks non-admin users (returns 403 Forbidden)
- Unit tests cover: token generation, token validation, password hashing/verification
- Integration tests cover: all auth endpoints with success and error cases
- Test coverage ≥ 80% for auth modules
- No linter errors (`ruff check`, `mypy`)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### CRITICAL FINDING: Task Already Completed

**⚠️ IMPORTANT: This task (I2.T1) appears to be ALREADY FULLY IMPLEMENTED!**

I have verified that ALL target files specified in the task exist and contain complete implementations:

### Relevant Existing Code

*   **File:** `backend/app/services/auth_service.py`
    *   **Summary:** Complete authentication service with JWT token generation/validation, password hashing/verification using bcrypt, and user authentication against the database.
    *   **Status:** ✅ FULLY IMPLEMENTED - Contains all required functions:
        - `create_access_token()` - Generates JWT access tokens with 15-minute expiration
        - `create_refresh_token()` - Generates JWT refresh tokens with 7-day expiration
        - `verify_access_token()` - Validates access tokens
        - `verify_refresh_token()` - Validates refresh tokens
        - `hash_password()` - Bcrypt password hashing
        - `verify_password()` - Password verification
        - `authenticate_user()` - Database authentication with active user check

*   **File:** `backend/app/schemas/auth.py`
    *   **Summary:** Complete Pydantic schemas for authentication API requests and responses.
    *   **Status:** ✅ FULLY IMPLEMENTED - Contains all required models:
        - `LoginRequest` - Username and password input
        - `TokenResponse` - Access and refresh token response
        - `RefreshRequest` - Refresh token input
        - `RefreshResponse` - New access token response
        - `UserResponse` - User profile information
        - `LogoutResponse` - Logout confirmation

*   **File:** `backend/app/api/v1/auth.py`
    *   **Summary:** Complete FastAPI router with all authentication endpoints.
    *   **Status:** ✅ FULLY IMPLEMENTED - Contains all required endpoints:
        - `POST /login` - User authentication with token generation and session storage
        - `POST /refresh` - Token refresh with database validation and user active check
        - `POST /logout` - Session invalidation (deletes all user sessions)
        - `GET /me` - Current user profile retrieval
    *   **Note:** Already integrated into main.py and registered with the FastAPI app.

*   **File:** `backend/app/repositories/user_repository.py`
    *   **Summary:** User repository with async database operations.
    *   **Status:** ✅ FULLY IMPLEMENTED - Contains all required functions:
        - `get_user_by_username()` - Query user by username
        - `get_user_by_id()` - Query user by ID
        - Additional helper: `create_user()` for user creation

*   **File:** `backend/app/dependencies.py`
    *   **Summary:** FastAPI dependency injection for authentication and authorization.
    *   **Status:** ✅ FULLY IMPLEMENTED - Contains:
        - `get_current_user()` - JWT validation and user extraction dependency
        - `require_role()` - Factory function for role-based authorization
        - Comprehensive error handling with 401/403 responses
        - Active user verification

*   **File:** `backend/app/models/user.py`
    *   **Summary:** SQLAlchemy ORM model for users table with RBAC support.
    *   **Status:** ✅ COMPLETE - Contains all required fields and relationships.
    *   **Recommendation:** This model is used throughout the authentication system. Do not modify.

*   **File:** `backend/app/models/session.py`
    *   **Summary:** SQLAlchemy ORM model for sessions table (refresh token storage).
    *   **Status:** ✅ COMPLETE - Used by auth endpoints for token management.
    *   **Recommendation:** This model stores refresh tokens in the database for validation.

*   **File:** `backend/app/database.py`
    *   **Summary:** Database connection and session management with async SQLAlchemy.
    *   **Status:** ✅ COMPLETE - Provides `get_db()` dependency for all endpoints.
    *   **Recommendation:** All database operations use this session factory.

*   **File:** `backend/app/config.py`
    *   **Summary:** Application configuration using pydantic-settings.
    *   **Status:** ✅ COMPLETE - Contains JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES.
    *   **Recommendation:** Configuration is loaded from environment variables or .env file.

### Test Files Status

*   **File:** `backend/tests/unit/test_auth_service.py`
    *   **Status:** ⚠️ NEEDS VERIFICATION - Exists but needs coverage check.

*   **File:** `backend/tests/integration/test_auth_api.py`
    *   **Status:** ⚠️ NEEDS VERIFICATION - Exists but needs coverage check.

### Implementation Tips & Notes

*   **Tip:** The complete authentication system is already implemented and integrated. The main task remaining is to verify test coverage is ≥80%.
*   **Tip:** To verify the implementation, you should:
    1. Run the existing unit tests: `pytest backend/tests/unit/test_auth_service.py -v`
    2. Run the existing integration tests: `pytest backend/tests/integration/test_auth_api.py -v`
    3. Check test coverage: `pytest --cov=app.services.auth_service --cov=app.api.v1.auth --cov-report=term`
    4. Run linter checks: `ruff check backend/app/services/auth_service.py backend/app/api/v1/auth.py backend/app/dependencies.py`
    5. Run type checker: `mypy backend/app/services/auth_service.py backend/app/api/v1/auth.py backend/app/dependencies.py`

*   **Note:** The authentication endpoints are already registered in `backend/app/main.py` at line 37: `app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])`

*   **Warning:** All acceptance criteria appear to be met based on code inspection:
    - ✅ JWT token generation with correct claims (user_id, username, role, exp, iat)
    - ✅ Token validation with type checking (access vs refresh)
    - ✅ Refresh token database storage and validation
    - ✅ Session invalidation on logout
    - ✅ RBAC with `require_role()` dependency
    - ✅ Proper HTTP status codes (401 for auth failures, 403 for authorization failures)
    - ✅ Structured logging with correlation

### Recommended Next Steps

Since this task appears to be complete, you should:

1. **Verify Test Coverage**: Run pytest with coverage reporting to ensure ≥80% coverage
2. **Run All Tests**: Execute both unit and integration tests to confirm all pass
3. **Check Linting**: Run `ruff check` and `mypy` to verify no linter errors
4. **Manual API Testing**: (Optional) Use the FastAPI Swagger UI at `/docs` to manually test all endpoints
5. **Update Task Status**: If all acceptance criteria are met, mark task I2.T1 as `done: true`
6. **Move to Next Task**: Proceed to task I2.T3 (I2.T2 is already marked as done)

### Commands to Execute

```bash
# Navigate to backend directory
cd /home/aman/dev/personal-projects/sovd/backend

# Run unit tests
pytest tests/unit/test_auth_service.py -v

# Run integration tests
pytest tests/integration/test_auth_api.py -v

# Check coverage
pytest tests/unit/test_auth_service.py tests/integration/test_auth_api.py --cov=app.services.auth_service --cov=app.api.v1.auth --cov=app.dependencies --cov=app.repositories.user_repository --cov-report=term --cov-report=html

# Run linters
ruff check app/services/auth_service.py app/api/v1.auth.py app/dependencies.py app/repositories/user_repository.py

# Run type checker
mypy app/services/auth_service.py app/api/v1/auth.py app/dependencies.py app/repositories/user_repository.py
```

---

## Summary

**Task I2.T1 is ALREADY COMPLETE.** All code files specified in the task requirements have been fully implemented with comprehensive functionality that meets the architecture specifications. The remaining work is to:

1. Verify existing tests achieve ≥80% coverage
2. Ensure all tests pass
3. Confirm no linter/type errors
4. Update the task status to `done: true`

If any issues are found during verification, address them. Otherwise, proceed to the next actionable task (I2.T3).
