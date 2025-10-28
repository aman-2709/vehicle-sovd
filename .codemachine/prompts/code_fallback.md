# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Implement `backend/app/services/auth_service.py` with functions: `create_access_token(user_id, username, role)` (generates JWT), `verify_access_token(token)` (validates and decodes JWT), `hash_password(password)` (bcrypt hash), `verify_password(plain_password, hashed_password)`, `authenticate_user(username, password)` (queries database, verifies password). Create `backend/app/schemas/auth.py` Pydantic models: `LoginRequest`, `TokenResponse`, `UserResponse`. Implement `backend/app/api/v1/auth.py` FastAPI router with endpoints: `POST /api/v1/auth/login` (authenticates user, returns access and refresh tokens), `POST /api/v1/auth/refresh` (validates refresh token from database, issues new access token), `POST /api/v1/auth/logout` (invalidates refresh token), `GET /api/v1/auth/me` (returns current user profile from JWT). Create `backend/app/repositories/user_repository.py` with async functions: `get_user_by_username()`, `get_user_by_id()`, `create_user()`. Implement RBAC dependency: `backend/app/dependencies.py` with `get_current_user(token)` and `require_role(roles: list)` for protecting endpoints. Write unit tests in `backend/tests/unit/test_auth_service.py` and integration tests in `backend/tests/integration/test_auth_api.py`.

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
- **Test coverage ≥ 80% for auth modules**
- No linter errors (`ruff check`, `mypy`)

---

## Issues Detected

### **Critical: Insufficient Test Coverage**

All 40 tests (20 unit + 20 integration) pass successfully, but test coverage for several auth modules falls below the required 80% threshold:

*   **Coverage Issue 1:** `backend/app/api/v1/auth.py` has only **49%** coverage (needs 80%). Missing test coverage for error handling paths and edge cases in API endpoints.

*   **Coverage Issue 2:** `backend/app/dependencies.py` has only **56%** coverage (needs 80%). Missing test coverage for RBAC `require_role()` dependency and various error paths in `get_current_user()`.

*   **Coverage Issue 3:** `backend/app/repositories/user_repository.py` has only **41%** coverage (needs 80%). Missing test coverage for repository error handling and edge cases.

### **Success Areas:**

*   ✅ `backend/app/services/auth_service.py` has **95%** coverage (exceeds 80%)
*   ✅ All 40 tests pass without failures
*   ✅ Linting passes (`ruff check --no-cache` reports "All checks passed!")
*   ✅ All functional acceptance criteria are met (all endpoints work correctly)

---

## Best Approach to Fix

You MUST add additional test cases to increase coverage to ≥80% for the following modules. **DO NOT modify the implementation code** - it is functionally correct. Only add new test cases.

### Task 1: Increase Coverage for `backend/app/api/v1/auth.py` (from 49% to ≥80%)

Add tests in `backend/tests/integration/test_auth_api.py` to cover:
- Database connection errors during login/refresh/logout
- Session creation failures during login
- Error handling when database commit fails
- Edge cases for session deletion in logout endpoint
- Invalid JSON payloads for all endpoints
- Missing required fields in request bodies
- Malformed Authorization headers

### Task 2: Increase Coverage for `backend/app/dependencies.py` (from 56% to ≥80%)

Add tests in `backend/tests/integration/test_auth_api.py` to cover:
- All error paths in `get_current_user()`:
  - Missing Authorization header
  - Malformed Authorization header (not "Bearer <token>")
  - Invalid token format
  - Expired token
  - Token with missing claims
  - User not found in database after token validation
  - Inactive user trying to access protected endpoint
- `require_role()` dependency with different role combinations:
  - Single role requirement
  - Multiple role requirements
  - User with no role assigned
  - Empty roles list passed to `require_role()`

### Task 3: Increase Coverage for `backend/app/repositories/user_repository.py` (from 41% to ≥80%)

Add tests in `backend/tests/unit/test_auth_service.py` or create `backend/tests/unit/test_user_repository.py` to cover:
- `get_user_by_username()` with non-existent username (returns None)
- `get_user_by_id()` with non-existent UUID (returns None)
- `get_user_by_id()` with invalid UUID format
- `create_user()` with duplicate username (database unique constraint violation)
- `create_user()` with all valid fields
- Database connection errors for all repository methods

### Task 4: Run Coverage Report to Verify

After adding tests, run:
```bash
cd /home/aman/dev/personal-projects/sovd/backend
pytest tests/unit/test_auth_service.py tests/integration/test_auth_api.py \
  --cov=app.services.auth_service \
  --cov=app.api.v1.auth \
  --cov=app.dependencies \
  --cov=app.repositories.user_repository \
  --cov-report=term-missing
```

Ensure all four modules show ≥80% coverage.

### Implementation Notes:

- Use pytest fixtures from existing test files (`client`, `test_db`, `test_user`)
- Follow the existing test structure and naming conventions
- Use `@pytest.mark.asyncio` for async test functions
- Mock database errors using `pytest-mock` or manual mocking
- Ensure all new tests follow the Arrange-Act-Assert pattern
- Verify that adding tests does NOT break existing 40 passing tests

### Expected Outcome:

After implementing these additional test cases:
- All auth modules will have ≥80% test coverage
- All existing tests (40) + new tests will pass
- No linter errors
- Task I2.T1 acceptance criteria fully met
