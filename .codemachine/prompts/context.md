# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T10",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Expand integration tests in `backend/tests/integration/` to achieve 80%+ coverage for all implemented modules. Write comprehensive test scenarios: authentication flows (login success/failure, token refresh, logout, protected endpoints), vehicle API (listing with filters, pagination, caching), command API (submission, validation errors, retrieval, response listing), audit logging (verify audit records created). Use pytest fixtures for database setup/teardown, test users, test vehicles. Configure pytest-cov to generate coverage report. Add `make test` target to Makefile to run `pytest --cov=app --cov-report=html --cov-report=term`. Ensure all tests pass and coverage meets 80% threshold. Fix any failing tests or bugs discovered.",
  "agent_type_hint": "BackendAgent",
  "inputs": "All implemented backend modules from I2.T1-I2.T7.",
  "target_files": [
    "backend/tests/integration/test_auth_api.py",
    "backend/tests/integration/test_vehicle_api.py",
    "backend/tests/integration/test_command_api.py",
    "backend/tests/conftest.py",
    "Makefile"
  ],
  "input_files": [],
  "deliverables": "Comprehensive integration test suite; coverage report showing 80%+ coverage; all tests passing.",
  "acceptance_criteria": "`make test` (or `pytest`) runs all tests successfully (0 failures); Coverage report shows ≥80% line coverage for `backend/app/` directory; Integration tests cover all API endpoints with success and error cases; Tests verify audit log creation for key events; Tests verify Redis caching behavior for vehicle status; Fixtures provide clean database state for each test; Coverage HTML report generated in `backend/htmlcov/` directory; Coverage summary displayed in terminal output; No flaky tests (tests pass consistently on multiple runs)",
  "dependencies": [
    "I2.T1",
    "I2.T2",
    "I2.T3",
    "I2.T4",
    "I2.T5",
    "I2.T6",
    "I2.T7"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: unit-testing (from 03_Verification_and_Glossary.md)

```markdown
#### Unit Testing

**Backend (Python/pytest)**
*   **Scope**: Individual functions and classes in services, repositories, utilities, and protocol handlers
*   **Framework**: pytest with pytest-asyncio for async code
*   **Coverage Target**: ≥80% line coverage for all modules
*   **Key Areas**:
    *   Auth service: JWT generation/validation, password hashing, RBAC logic
    *   Vehicle service: Filtering, caching logic
    *   Command service: Status transitions, validation
    *   SOVD protocol handler: Command validation, encoding/decoding
    *   Audit service: Log record creation
    *   Mock vehicle connector: Response generation
*   **Mocking**: Use pytest fixtures and `unittest.mock` for database, Redis, external dependencies
*   **Execution**: `pytest backend/tests/unit/` or `make test`
```

### Context: integration-testing (from 03_Verification_and_Glossary.md)

```markdown
#### Integration Testing

**Backend API Integration Tests**
*   **Scope**: API endpoints with database and Redis integration (using test containers or docker-compose services)
*   **Framework**: pytest with httpx async test client
*   **Key Scenarios**:
    *   Authentication flow: login, token refresh, logout, protected endpoint access
    *   Vehicle API: listing, filtering, pagination, caching behavior
    *   Command API: submission, retrieval, response listing, validation errors
    *   WebSocket: connection establishment, event delivery, authentication
    *   Error scenarios: validation errors, timeouts, database failures
    *   Audit logging: verify audit records created for all actions
*   **Test Data**: Use test fixtures for users, vehicles, commands (seed before tests, clean after)
*   **Execution**: `pytest backend/tests/integration/` (requires running docker-compose for db and redis)
```

### Context: code-quality-gates (from 03_Verification_and_Glossary.md)

```markdown
### 5.3. Code Quality Gates

#### Quality Metrics & Enforcement

**Code Coverage**
*   **Requirement**: ≥80% line coverage for both backend and frontend
*   **Enforcement**: CI pipeline fails if coverage drops below threshold
*   **Reporting**: HTML coverage reports generated and uploaded as artifacts
*   **Tool**: pytest-cov (backend), Vitest coverage (frontend)
```

### Context: task-i2-t10 (from 02_Iteration_I2.md)

```markdown
**Task 2.10: Integration Testing and Coverage Report**
*   **Task ID:** `I2.T10`
*   **Description:** Expand integration tests in `backend/tests/integration/` to achieve 80%+ coverage for all implemented modules. Write comprehensive test scenarios: authentication flows (login success/failure, token refresh, logout, protected endpoints), vehicle API (listing with filters, pagination, caching), command API (submission, validation errors, retrieval, response listing), audit logging (verify audit records created). Use pytest fixtures for database setup/teardown, test users, test vehicles. Configure pytest-cov to generate coverage report. Add `make test` target to Makefile to run `pytest --cov=app --cov-report=html --cov-report=term`. Ensure all tests pass and coverage meets 80% threshold. Fix any failing tests or bugs discovered.
*   **Agent Type Hint:** `BackendAgent`
*   **Inputs:** All implemented backend modules from I2.T1-I2.T7.
*   **Input Files:** [All backend source files in `backend/app/`]
*   **Target Files:**
    *   `backend/tests/integration/test_auth_api.py` (expand)
    *   `backend/tests/integration/test_vehicle_api.py` (expand)
    *   `backend/tests/integration/test_command_api.py` (expand)
    *   `backend/tests/conftest.py` (shared fixtures)
    *   Updates to `Makefile` (add test target)
*   **Deliverables:** Comprehensive integration test suite; coverage report showing 80%+ coverage; all tests passing.
*   **Acceptance Criteria:**
    *   `make test` (or `pytest`) runs all tests successfully (0 failures)
    *   Coverage report shows ≥80% line coverage for `backend/app/` directory
    *   Integration tests cover all API endpoints with success and error cases
    *   Tests verify audit log creation for key events
    *   Tests verify Redis caching behavior for vehicle status
    *   Fixtures provide clean database state for each test
    *   Coverage HTML report generated in `backend/htmlcov/` directory
    *   Coverage summary displayed in terminal output
    *   No flaky tests (tests pass consistently on multiple runs)
*   **Dependencies:** All I2 tasks (requires complete backend implementation)
*   **Parallelizable:** No (final validation task for iteration)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Current Test Coverage Status

**Overall Coverage: 88% (ALREADY EXCEEDS 80% THRESHOLD)**

**Current Status:**
- Total statements: 939
- Missed statements: 108
- Coverage: 88%
- **CRITICAL**: 3 tests are currently FAILING in `tests/unit/test_command_service.py`

**Files with Low Coverage (Below 80%):**
1. `app/repositories/command_repository.py`: 26% coverage (38 statements, 28 missed)
2. `app/repositories/response_repository.py`: 47% coverage (15 statements, 8 missed)
3. `app/repositories/vehicle_repository.py`: 31% coverage (29 statements, 20 missed)
4. `app/services/command_service.py`: 58% coverage (43 statements, 18 missed)
5. `app/database.py`: 69% coverage (16 statements, 5 missed)
6. `app/main.py`: 77% coverage (26 statements, 6 missed)

### Relevant Existing Code

*   **File:** `backend/tests/conftest.py`
    *   **Summary:** This file contains pytest fixtures for database sessions and async HTTP clients. It uses SQLite for testing (file-based at `./test.db`) and creates only the `users` and `sessions` tables since other tables require PostgreSQL-specific JSONB types.
    *   **Recommendation:** You MUST continue using this fixture pattern. The audit service is already mocked here (`patch("app.services.audit_service.log_audit_event")`), which is why audit tests pass even though the audit_logs table isn't created.
    *   **WARNING:** The conftest currently uses a **function-scoped** db_session fixture, which means each test gets a fresh database. This is good for isolation but tests are currently using SQLite instead of the real PostgreSQL database.

*   **File:** `backend/tests/integration/test_auth_api.py`
    *   **Summary:** This is an EXCELLENT reference implementation with 857 lines of comprehensive auth endpoint tests. It includes multiple test classes covering all endpoints, edge cases, and error paths.
    *   **Recommendation:** Use this file as your GOLD STANDARD template for test structure. Notice how it:
        - Organizes tests by endpoint into classes
        - Tests both success and failure paths
        - Includes edge cases (expired tokens, malformed headers, missing fields)
        - Has an end-to-end flow test
        - Verifies database state after operations

*   **File:** `backend/tests/integration/test_vehicle_api.py`
    *   **Summary:** Contains 450 lines of vehicle API tests covering listing, filtering, pagination, and caching scenarios.
    *   **Recommendation:** This file already has good coverage. Review it to ensure caching tests are comprehensive.

*   **File:** `backend/tests/integration/test_command_api.py`
    *   **Summary:** Contains 747 lines of command API tests.
    *   **Recommendation:** Review this file carefully - the low coverage of `command_repository.py` (26%) and `command_service.py` (58%) suggests missing test coverage for command filtering, pagination, and status update scenarios.

*   **File:** `backend/app/repositories/command_repository.py`
    *   **Summary:** Contains 4 key functions: `create_command`, `get_command_by_id`, `update_command_status`, and `get_commands` (with filtering by vehicle_id, user_id, status, and pagination).
    *   **CRITICAL:** The `get_commands` function (lines 102-136) has VERY LOW coverage. This function handles filtering and pagination logic that MUST be tested.
    *   **Recommendation:** You MUST write integration tests that exercise all filter combinations and pagination scenarios for this function.

*   **File:** `backend/app/repositories/vehicle_repository.py`
    *   **Summary:** Contains 4 functions: `get_all_vehicles` (with status_filter, search_term, pagination), `get_vehicle_by_id`, `get_vehicle_by_vin`, and `update_vehicle_status`.
    *   **CRITICAL:** Only 31% coverage - the filtering and search logic is likely not being tested.
    *   **Recommendation:** Write tests that exercise the VIN search (partial match, case-insensitive) and status filtering with various combinations.

*   **File:** `backend/app/repositories/response_repository.py`
    *   **Summary:** Low coverage at 47%. This repository handles command response storage.
    *   **Recommendation:** Add tests for response creation and retrieval scenarios, especially for multi-response commands.

*   **File:** `backend/app/services/command_service.py`
    *   **Summary:** Only 58% coverage. This service orchestrates command submission, validation, and async execution via the vehicle connector.
    *   **CRITICAL:** Missing coverage likely includes error paths, status transitions, and interaction with the vehicle connector.
    *   **Recommendation:** Add tests for command validation failures, vehicle connector errors, and status update scenarios.

### Implementation Tips & Notes

*   **Tip #1 - Failing Tests**: You have 3 FAILING tests in `tests/unit/test_command_service.py`. These MUST be fixed first before claiming task completion:
    - `test_submit_command_success`
    - `test_submit_command_vehicle_not_found`
    - `test_submit_command_empty_params`

*   **Tip #2 - Coverage Already Met**: The OVERALL coverage is 88%, which already exceeds the 80% threshold. However, several individual modules are below 80%. You should focus on:
    1. Fixing the 3 failing unit tests
    2. Adding integration tests to cover the low-coverage repository functions
    3. Ensuring the Makefile `test` target runs with coverage reporting

*   **Tip #3 - Makefile Update**: The current Makefile `test` target at line 21-27 does NOT include the `--cov` flags required by the acceptance criteria. You MUST update it to:
    ```makefile
    test:
        @echo "Running backend tests with coverage..."
        @cd backend && pytest --cov=app --cov-report=html --cov-report=term
    ```

*   **Tip #4 - SQLite vs PostgreSQL**: The current test setup uses SQLite, which means:
    - JSONB fields cannot be tested (audit_logs, command_params, response_payload)
    - The audit service is mocked in conftest.py
    - This is ACCEPTABLE for the current iteration since the task focuses on integration testing of APIs, not database implementation details

*   **Tip #5 - Redis Caching**: The vehicle service uses Redis caching (see requirement "Tests verify Redis caching behavior for vehicle status"). Make sure `test_vehicle_api.py` has tests that verify:
    - First request to `/vehicles/{id}/status` fetches from database
    - Second request within TTL (30 seconds) hits cache
    - Cache invalidation after TTL expiry

*   **Tip #6 - Audit Logging**: Since the audit service is mocked in conftest, tests should verify that `log_audit_event` was CALLED with correct parameters, not that actual database records were created. Check `test_auth_api.py` for examples if needed.

*   **Warning #1 - Test Isolation**: Each test should be independent and not rely on data from previous tests. The current `db_session` fixture (function-scoped) provides good isolation.

*   **Warning #2 - Async Patterns**: ALL repository and service functions are async. Make sure all test functions are marked with `@pytest.mark.asyncio` and use `await` correctly.

*   **Note #1 - Test Organization**: Follow the pattern in `test_auth_api.py` of organizing tests into classes by endpoint or feature area. This makes tests easier to navigate and maintain.

*   **Note #2 - Coverage HTML Report**: The coverage HTML report is generated in `backend/htmlcov/` and includes detailed line-by-line coverage highlighting. Use this to identify exactly which lines need test coverage.

### Action Plan Summary

1. **FIRST PRIORITY**: Fix the 3 failing unit tests in `tests/unit/test_command_service.py`
2. **SECOND PRIORITY**: Update the Makefile `test` target to include `--cov=app --cov-report=html --cov-report=term`
3. **THIRD PRIORITY**: Add integration tests to cover low-coverage repository functions:
   - Command repository filtering and pagination (`get_commands` function)
   - Vehicle repository filtering, search, and status updates
   - Response repository create and retrieval operations
4. **FOURTH PRIORITY**: Verify all acceptance criteria are met and tests pass consistently

### Coverage Improvement Targets

Focus your testing efforts on these specific uncovered code paths:

1. **command_repository.py** (26% → 80%+):
   - Test `get_commands` with various filter combinations (vehicle_id, user_id, status)
   - Test pagination (limit, offset)
   - Test ordering (should be by submitted_at desc)

2. **vehicle_repository.py** (31% → 80%+):
   - Test `get_all_vehicles` with status_filter
   - Test VIN search with partial matches
   - Test case-insensitive search
   - Test `update_vehicle_status` function

3. **response_repository.py** (47% → 80%+):
   - Test response creation with sequence numbers
   - Test retrieval by command_id
   - Test is_final flag handling

4. **command_service.py** (58% → 80%+):
   - Test command validation error paths
   - Test vehicle not found scenarios
   - Test interaction with vehicle connector
   - Test status transitions during command execution
