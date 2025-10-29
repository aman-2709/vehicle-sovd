# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T9",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Set up Playwright for E2E testing in `tests/e2e/`. Configure `tests/e2e/playwright.config.ts` with base URL `http://localhost:3000`, browsers (chromium, firefox), headless mode, screenshot on failure. Write initial E2E test scenarios: 1) `tests/e2e/specs/auth.spec.ts`: complete auth flow (login with valid credentials, verify redirect to dashboard, verify header shows username, logout, verify redirect to login), 2) `tests/e2e/specs/vehicle_management.spec.ts`: navigate to vehicles page, verify vehicle list displays, search for vehicle by VIN, filter by status, 3) `tests/e2e/specs/command_execution.spec.ts`: navigate to command page, select vehicle, select command \"ReadDTC\", fill parameters, submit, verify command_id displayed, verify response viewer shows responses (wait for WebSocket events). Add `make e2e` target to root Makefile to run E2E tests (starts docker-compose, waits for services, runs tests, stops services). Document E2E test execution in README.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Implemented frontend pages from I3.T4-I3.T8; backend APIs from I2.",
  "target_files": [
    "tests/e2e/playwright.config.ts",
    "tests/e2e/specs/auth.spec.ts",
    "tests/e2e/specs/vehicle_management.spec.ts",
    "tests/e2e/specs/command_execution.spec.ts",
    "Makefile",
    "README.md"
  ],
  "input_files": [],
  "deliverables": "Configured Playwright E2E testing framework; three E2E test suites covering critical user flows; Makefile automation; documentation.",
  "acceptance_criteria": "`make e2e` starts services, runs all E2E tests, stops services; Auth E2E test passes: login → dashboard → logout flow works end-to-end; Vehicle management E2E test passes: vehicle list displays, search and filter work; Command execution E2E test passes: full flow from selecting vehicle to viewing responses works (including WebSocket updates); Tests run in headless mode without errors; Screenshots captured on failure (saved to `tests/e2e/screenshots/`); Tests run across multiple browsers (chromium, firefox) successfully; E2E tests complete in <5 minutes; README includes clear instructions for running E2E tests; No flaky tests (tests pass consistently)",
  "dependencies": [
    "I3.T1",
    "I3.T2",
    "I3.T3",
    "I3.T4",
    "I3.T5",
    "I3.T6",
    "I3.T7",
    "I3.T8"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: e2e-testing (from 03_Verification_and_Glossary.md)

```markdown
#### End-to-End (E2E) Testing

**Full-Stack E2E Tests**
*   **Scope**: Complete user workflows across frontend and backend with real services running
*   **Framework**: Playwright (supports multiple browsers: Chromium, Firefox, WebKit)
*   **Environment**: docker-compose with all services (frontend, backend, database, redis)
*   **Key Scenarios**:
    *   **Authentication**: Complete login flow, verify session persistence, logout
    *   **Vehicle Management**: Navigate to vehicles page, search/filter vehicles, view vehicle details
    *   **Command Execution**: End-to-end flow (login → select vehicle → submit command → view real-time responses in ResponseViewer)
    *   **Command History**: View history, filter by status/vehicle, view command details
    *   **Error Handling**: Invalid login, vehicle timeout simulation, network failures
*   **Assertions**: Page navigation, element visibility, API responses, WebSocket events, database state
*   **Screenshot on Failure**: Automatic screenshot capture for debugging
*   **Execution**: `make e2e` (starts docker-compose, runs Playwright tests, stops services)
*   **Duration Target**: <5 minutes for full E2E suite
```

### Context: ci-cd-pipeline (from 03_Verification_and_Glossary.md)

```markdown
#### Pipeline Overview (GitHub Actions)

The CI/CD pipeline (`github/workflows/ci-cd.yml`) orchestrates all verification activities automatically:

**Stage 1: Lint & Format Check (Parallel)**
*   Backend: ruff, black --check, mypy
*   Frontend: eslint, prettier --check
*   **Failure Condition**: Any linting errors
*   **Duration**: ~2 minutes

**Stage 2: Unit Tests (Parallel)**
*   Backend: pytest unit tests with coverage report
*   Frontend: npm test (Vitest) with coverage report
*   **Failure Condition**: Test failure or coverage <80%
*   **Duration**: ~3 minutes

**Stage 3: Integration Tests**
*   Start docker-compose (db, redis, backend)
*   Run backend integration tests
*   Stop docker-compose
*   **Failure Condition**: Test failure
*   **Duration**: ~5 minutes

**Stage 4: E2E Tests**
*   Start full docker-compose stack (frontend, backend, db, redis)
*   Run Playwright E2E tests (headless mode)
*   Capture screenshots on failure
*   Stop docker-compose
*   **Failure Condition**: Test failure
*   **Duration**: ~5 minutes
```

### Context: task-i3-t9 (from 02_Iteration_I3.md)

```markdown
*   **Task 3.9: End-to-End Testing Setup and Initial E2E Tests**
    *   **Task ID:** `I3.T9`
    *   **Description:** Set up Playwright for E2E testing in `tests/e2e/`. Configure `tests/e2e/playwright.config.ts` with base URL `http://localhost:3000`, browsers (chromium, firefox), headless mode, screenshot on failure. Write initial E2E test scenarios: 1) `tests/e2e/specs/auth.spec.ts`: complete auth flow (login with valid credentials, verify redirect to dashboard, verify header shows username, logout, verify redirect to login), 2) `tests/e2e/specs/vehicle_management.spec.ts`: navigate to vehicles page, verify vehicle list displays, search for vehicle by VIN, filter by status, 3) `tests/e2e/specs/command_execution.spec.ts`: navigate to command page, select vehicle, select command "ReadDTC", fill parameters, submit, verify command_id displayed, verify response viewer shows responses (wait for WebSocket events). Add `make e2e` target to root Makefile to run E2E tests (starts docker-compose, waits for services, runs tests, stops services). Document E2E test execution in README.
    *   **Agent Type Hint:** `FrontendAgent` or `TestingAgent`
    *   **Inputs:** Implemented frontend pages from I3.T4-I3.T8; backend APIs from I2.
    *   **Input Files:** [All frontend and backend source files]
    *   **Target Files:**
        *   `tests/e2e/playwright.config.ts`
        *   `tests/e2e/specs/auth.spec.ts`
        *   `tests/e2e/specs/vehicle_management.spec.ts`
        *   `tests/e2e/specs/command_execution.spec.ts`
        *   Updates to `Makefile` (add e2e target)
        *   Updates to `README.md` (document E2E test execution)
    *   **Deliverables:** Configured Playwright E2E testing framework; three E2E test suites covering critical user flows; Makefile automation; documentation.
    *   **Acceptance Criteria:**
        *   `make e2e` starts services, runs all E2E tests, stops services
        *   Auth E2E test passes: login → dashboard → logout flow works end-to-end
        *   Vehicle management E2E test passes: vehicle list displays, search and filter work
        *   Command execution E2E test passes: full flow from selecting vehicle to viewing responses works (including WebSocket updates)
        *   Tests run in headless mode without errors
        *   Screenshots captured on failure (saved to `tests/e2e/screenshots/`)
        *   Tests run across multiple browsers (chromium, firefox) successfully
        *   E2E tests complete in <5 minutes
        *   README includes clear instructions for running E2E tests
        *   No flaky tests (tests pass consistently)
    *   **Dependencies:** All I3 tasks (requires complete frontend and WebSocket implementation)
    *   **Parallelizable:** No (final validation task for iteration)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `tests/e2e/` directory
    *   **Summary:** The E2E test directory already exists with a `specs/` subdirectory and `test-results/` subdirectory. This indicates partial setup, but no actual test files or Playwright configuration exists yet.
    *   **Recommendation:** You MUST create the `playwright.config.ts` file in the `tests/e2e/` directory and populate the `specs/` directory with the three required test files.

*   **File:** `frontend/package.json`
    *   **Summary:** The frontend package.json contains Vitest for unit testing but does NOT include Playwright dependencies. The test script runs Vitest, not Playwright.
    *   **Recommendation:** You MUST create a separate `package.json` file in the `tests/e2e/` directory (separate from the frontend package.json) and install Playwright there using `npm init -y && npm install -D @playwright/test`. This is standard practice to keep E2E dependencies isolated.

*   **File:** `Makefile`
    *   **Summary:** The Makefile already has a `test` target that attempts to run E2E tests with `cd tests/e2e && npx playwright test || true`, but Playwright is not installed yet. The Makefile also shows a structure for starting services with docker-compose.
    *   **Recommendation:** You MUST update the `e2e` target in the Makefile (or create it if it doesn't exist as a separate target) to: (1) Start docker-compose with `docker-compose up -d`, (2) Wait for services to be healthy (use `docker-compose ps` or health checks), (3) Run Playwright tests from `tests/e2e/`, (4) Stop services with `docker-compose down`. Follow the pattern shown in the CI/CD pipeline documentation.

*   **File:** `docker-compose.yml`
    *   **Summary:** Docker Compose configuration includes all four services (db, redis, backend, frontend) with health checks defined for db and redis. Services are exposed on standard ports (frontend: 3000, backend: 8000, db: 5432, redis: 6379).
    *   **Recommendation:** Your Playwright config SHOULD use `http://localhost:3000` as the base URL since that's where the frontend service runs. When running in the `make e2e` context, the services will already be started by docker-compose.

*   **File:** `frontend/src/pages/LoginPage.tsx`
    *   **Summary:** Login page accepts username and password, calls the `login` function from AuthContext, and redirects to `/dashboard` on success. It displays error messages for invalid credentials (401 status).
    *   **Recommendation:** Your auth E2E test SHOULD use the seed data credentials documented in the README: `admin` / `admin123` or `engineer` / `engineer123`. The test MUST verify redirect to `/dashboard` after successful login and MUST check that the header displays the username.

*   **File:** `frontend/src/pages/VehiclesPage.tsx`
    *   **Summary:** Vehicles page uses React Query to fetch vehicle data with 30-second auto-refresh. It includes client-side search filtering by VIN and status filter dropdown with options "All", "Connected", "Disconnected".
    *   **Recommendation:** Your vehicle management E2E test SHOULD navigate to `/vehicles`, verify that the vehicle list is visible (check for VIN elements), interact with the search input to filter by VIN, and interact with the status dropdown to filter vehicles. Use Playwright's auto-waiting features to handle the React Query loading states.

*   **File:** `frontend/src/pages/CommandPage.tsx`
    *   **Summary:** Command page includes a vehicle selector dropdown and a command form that dynamically changes based on selected command. On successful command submission, it displays the command_id and sets `activeCommandId` to show the ResponseViewer component.
    *   **Recommendation:** Your command execution E2E test MUST: (1) Navigate to `/commands` or the command page route, (2) Select a vehicle from the dropdown (use the seed vehicle VINs), (3) Select "ReadDTC" command, (4) Fill in the ecuAddress parameter field, (5) Submit the form, (6) Wait for the success message and command_id to appear, (7) Verify that the ResponseViewer component is visible and displays responses. Since responses are streamed via WebSocket, you SHOULD add `page.waitForSelector()` calls to wait for response elements to appear.

*   **File:** `backend/app/api/v1/websocket.py`
    *   **Summary:** WebSocket endpoint at `/ws/responses/{command_id}` requires JWT authentication via query parameter `?token={jwt}`. The endpoint authenticates the user, subscribes to Redis Pub/Sub channel, and streams response events to the client.
    *   **Recommendation:** For the command execution E2E test, you DO NOT need to manually connect to the WebSocket endpoint—the ResponseViewer component handles this automatically. However, you SHOULD wait for response elements to appear in the ResponseViewer, which will indicate that WebSocket events are being received correctly.

*   **File:** `README.md`
    *   **Summary:** README includes comprehensive documentation for quick start, docker-compose services, and troubleshooting. It does NOT currently include E2E testing instructions.
    *   **Recommendation:** You MUST add a new section to the README documenting E2E test execution. Include: (1) Prerequisites (Node.js, Playwright browsers installed), (2) Running tests with `make e2e`, (3) Running tests in headed mode for debugging, (4) Location of screenshots on failure, (5) Troubleshooting common E2E test issues.

### Implementation Tips & Notes

*   **Tip:** Playwright's `page.waitForURL()` is excellent for verifying navigation after login and logout. Use it to assert that the URL changes to `/dashboard` after login and `/login` after logout.

*   **Tip:** For the vehicle management test, use Playwright's `page.locator()` with text selectors to find vehicle VINs. The seed data includes two test vehicles with VINs `TESTVIN0000000001` and `TESTVIN0000000002` (from the init_db.sh script context).

*   **Tip:** When testing the command execution flow, you SHOULD use `page.waitForTimeout()` sparingly and prefer `page.waitForSelector()` or `page.waitForResponse()` for more reliable waiting. WebSocket responses are streamed, so you may need to wait for multiple response elements to appear.

*   **Note:** The Makefile currently runs E2E tests with `|| true` which suppresses failures. For the `make e2e` target you implement, you SHOULD remove the `|| true` so that failures cause the Make target to fail (this is critical for CI/CD integration).

*   **Note:** Playwright configuration SHOULD include `screenshot: 'only-on-failure'` and `video: 'retain-on-failure'` for debugging. The screenshots directory `tests/e2e/screenshots/` already exists (test-results subdirectory).

*   **Tip:** To wait for services to be healthy in the Makefile, you can use a simple loop checking `docker-compose ps` output or use `docker-compose up --wait` if your docker-compose version supports it. Alternatively, use a shell script that polls the health endpoints (`http://localhost:3000` for frontend, `http://localhost:8000/docs` for backend).

*   **Warning:** The current Makefile `test` target runs all tests (backend, frontend, E2E) sequentially. Your `make e2e` target SHOULD be separate and independent, so it can be run in isolation. The general `make test` target can remain as is or be updated to call `make e2e` if desired.

*   **Tip:** Playwright projects feature allows you to run tests across multiple browsers. Configure projects for `chromium` and `firefox` in playwright.config.ts. You can skip webkit for now to keep test duration under 5 minutes.

*   **Note:** The frontend uses MUI components which may have dynamic IDs. When writing selectors, prefer `page.getByRole()`, `page.getByLabel()`, `page.getByText()`, or `data-testid` attributes over CSS selectors. This makes tests more robust to UI changes.

*   **Tip:** For the auth test, verify that the username appears in the header after login. Based on the LoginPage implementation, after login the user is redirected to dashboard. The header should be visible on all authenticated pages (since it's part of the Layout component from I3.T8).

---

## 4. Additional Context: Environment and Services

**Docker Compose Services:**
- **Frontend:** Runs on port 3000, Vite dev server with HMR
- **Backend:** Runs on port 8000, FastAPI with uvicorn
- **Database:** PostgreSQL on port 5432, initialized with seed data (2 users, 2 vehicles)
- **Redis:** Runs on port 6379, used for WebSocket pub/sub

**Seed Data (from README.md):**
- Admin user: `admin` / `admin123`
- Engineer user: `engineer` / `engineer123`
- Test vehicles: VINs `TESTVIN0000000001` and `TESTVIN0000000002`

**Application URLs:**
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs (Swagger): `http://localhost:8000/docs`

**Testing Infrastructure:**
- Backend tests: pytest (unit + integration tests exist in `backend/tests/`)
- Frontend tests: Vitest (component tests exist in `frontend/tests/components/`)
- E2E tests: Playwright (to be set up in this task)

---

## 5. Task Execution Strategy

Based on my analysis, here is the recommended implementation order:

1. **Initialize Playwright in tests/e2e/**
   - Create `tests/e2e/package.json` with Playwright dependency
   - Run `npm install` to install Playwright and browsers
   - Create `tests/e2e/playwright.config.ts` with proper configuration

2. **Write auth.spec.ts**
   - Test complete auth flow: login → dashboard → logout
   - Verify JWT token handling and session persistence
   - Verify header displays username after login

3. **Write vehicle_management.spec.ts**
   - Navigate to vehicles page and verify list renders
   - Test search filtering by VIN
   - Test status filter dropdown functionality

4. **Write command_execution.spec.ts**
   - Full flow: select vehicle → choose command → fill params → submit
   - Wait for command_id in success message
   - Verify ResponseViewer shows real-time WebSocket responses

5. **Update Makefile**
   - Create or update `e2e` target with service orchestration
   - Ensure proper startup, health checks, test execution, and teardown

6. **Update README.md**
   - Add E2E Testing section with clear instructions
   - Document troubleshooting tips and debugging commands

7. **Validate**
   - Run `make e2e` end-to-end to ensure all acceptance criteria pass
   - Verify tests run in headless mode successfully
   - Check screenshot capture on failure works

---

**End of Task Briefing Package**
