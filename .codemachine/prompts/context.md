# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

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
