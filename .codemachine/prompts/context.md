# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T10",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Expand frontend component tests to achieve 80%+ coverage. Write additional tests for untested components and edge cases. Configure Vitest coverage reporting with `vitest --coverage`. Add `frontend:test` and `frontend:coverage` targets to root Makefile. Ensure all frontend tests pass. Run ESLint and Prettier on all frontend code, fix any violations. Configure Prettier to run on pre-commit hook (using husky or similar). Generate coverage HTML report. Update GitHub Actions CI workflow skeleton (from I1.T1) to run frontend tests and linting in CI pipeline.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "All frontend components from I3.T4-I3.T8.",
  "target_files": [
    "frontend/tests/components/VehicleList.test.tsx",
    "frontend/tests/components/CommandForm.test.tsx",
    "frontend/tests/components/ResponseViewer.test.tsx",
    "frontend/vitest.config.ts",
    "Makefile",
    ".github/workflows/ci-cd.yml",
    "frontend/.prettierrc"
  ],
  "input_files": [
    "frontend/src/pages/VehiclesPage.tsx",
    "frontend/src/pages/CommandPage.tsx",
    "frontend/src/components/commands/ResponseViewer.tsx"
  ],
  "deliverables": "Comprehensive frontend test suite with 80%+ coverage; all tests passing; linting and formatting configured; CI integration.",
  "acceptance_criteria": "`make frontend:test` runs all frontend tests successfully (0 failures); Coverage report shows ≥80% line coverage for `frontend/src/` directory; `npm run lint` (or `make frontend:lint`) passes with no errors; `npm run format` (or `make frontend:format`) formats all files consistently; Coverage HTML report generated in `frontend/coverage/` directory; GitHub Actions workflow runs frontend tests and linting on push (verify workflow syntax is valid); Component tests cover: all pages, key components (VehicleList, CommandForm, ResponseViewer), common components (Header, ErrorBoundary); Tests verify: rendering, user interactions, API integration (with mocked API), error handling; No console errors or warnings in tests; All frontend code follows ESLint and Prettier rules",
  "dependencies": [
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

### Context: testing-levels (from 03_Verification_and_Glossary.md)

```markdown
<!-- anchor: testing-levels -->
### 5.1. Testing Levels

The project employs a comprehensive testing strategy across multiple levels to ensure quality, reliability, and adherence to requirements.

<!-- anchor: unit-testing -->
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

**Frontend (TypeScript/Vitest)**
*   **Scope**: Individual React components, hooks, utility functions
*   **Framework**: Vitest with React Testing Library
*   **Coverage Target**: ≥80% line coverage for all components
*   **Key Areas**:
    *   Authentication components: LoginForm, ProtectedRoute
    *   Vehicle components: VehicleList, VehicleSelector
    *   Command components: CommandForm, ResponseViewer
    *   Common components: Header, ErrorBoundary, LoadingSpinner
    *   API client: Token management, retry logic
*   **Mocking**: Mock API calls using Vitest's `vi.mock()`, mock WebSocket connections
*   **Execution**: `npm run test` or `make frontend:test`

<!-- anchor: integration-testing -->
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
<!-- anchor: code-quality-gates -->
### 5.3. Code Quality Gates

<!-- anchor: quality-metrics -->
#### Quality Metrics & Enforcement

**Code Coverage**
*   **Requirement**: ≥80% line coverage for both backend and frontend
*   **Enforcement**: CI pipeline fails if coverage drops below threshold
*   **Reporting**: HTML coverage reports generated and uploaded as artifacts
*   **Tool**: pytest-cov (backend), Vitest coverage (frontend)

**Linting & Formatting**
*   **Backend Standards**:
    *   Ruff: Select rules E (errors), F (pyflakes), I (import order)
    *   Black: Line length 100, enforced formatting
    *   mypy: Strict mode (type checking)
*   **Frontend Standards**:
    *   ESLint: React rules, security rules, TypeScript rules
    *   Prettier: Consistent formatting (trailing commas, semicolons)
*   **Enforcement**: CI pipeline fails on any linting errors
*   **Pre-commit Hooks**: Optional (can use husky to run linters before commit)

**Type Safety**
*   **Backend**: mypy strict mode ensures all functions have type hints
*   **Frontend**: TypeScript strict mode (`"strict": true` in tsconfig.json)
*   **Enforcement**: CI pipeline runs type checkers

**Dependency Security**
*   **Tools**: pip-audit (backend), npm audit (frontend), Trivy (Docker)
*   **Enforcement**: CI pipeline fails on critical vulnerabilities
```

### Context: nfr-usability (from 01_Context_and_Drivers.md)

```markdown
<!-- anchor: nfr-usability -->
#### Usability
- **Intuitive UI**: Clean, modern interface following UX best practices
- **Error Handling**: Clear error messages with actionable guidance
- **Responsive Design**: Support for desktop and tablet form factors

**Architectural Impact**: Component-based UI framework (React), design system, comprehensive error handling middleware.
```

### Context: ci-cd-pipeline (from 03_Verification_and_Glossary.md)

```markdown
<!-- anchor: ci-cd-pipeline -->
### 5.4. Continuous Integration & Deployment Pipeline

<!-- anchor: pipeline-overview -->
#### Pipeline Overview

**GitHub Actions Workflow Stages**

1. **Lint (Parallel)**
   - Backend linting: `ruff check`, `black --check`, `mypy`
   - Frontend linting: `eslint`, `prettier --check`
   - **Duration**: ~2 minutes
   - **Failure Action**: Fail build, block merge

2. **Unit Tests (Parallel)**
   - Backend unit tests: `pytest backend/tests/unit/ --cov`
   - Frontend unit tests: `vitest run --coverage`
   - **Coverage Threshold**: ≥80%
   - **Duration**: ~3 minutes
   - **Failure Action**: Fail build if tests fail or coverage < 80%

3. **Integration Tests (Sequential)**
   - Start docker-compose (PostgreSQL, Redis, backend services)
   - Backend integration tests: `pytest backend/tests/integration/`
   - **Duration**: ~5 minutes
   - **Failure Action**: Fail build, stop services

4. **E2E Tests (Sequential)**
   - Start full application stack (docker-compose)
   - Frontend E2E tests: `playwright test`
   - **Duration**: ~8 minutes
   - **Failure Action**: Fail build, capture screenshots/videos

5. **Security Scans (Parallel)**
   - Backend: `pip-audit`, `bandit`
   - Frontend: `npm audit`
   - Docker: `trivy` image scans
   - **Duration**: ~3 minutes
   - **Failure Action**: Fail on critical vulnerabilities

6. **Build Images (Parallel)**
   - Build production Docker images
   - Tag: `<branch>-<git-sha>`, `latest` (for main)
   - **Duration**: ~5 minutes
   - **Artifacts**: Docker images

7. **Push to Registry (Sequential)**
   - Push images to container registry (Docker Hub, ECR, etc.)
   - **Condition**: Only on main/develop branches
   - **Duration**: ~3 minutes

8. **Deploy to Staging (Sequential)**
   - Deploy to staging environment using Helm
   - **Trigger**: Automatic on `develop` branch
   - Run smoke tests
   - **Duration**: ~5 minutes

9. **Deploy to Production (Manual Approval)**
   - Deploy to production environment
   - **Trigger**: Manual approval required on `main` branch
   - Run smoke tests
   - **Rollback**: Automatic rollback on smoke test failure
   - **Duration**: ~5 minutes
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/vite.config.ts`
    *   **Summary:** Vite configuration already includes basic test setup with `test.environment: 'jsdom'` and `test.setupFiles: ['./tests/setup.ts']`. Coverage configuration is NOT yet present.
    *   **Recommendation:** You MUST add coverage configuration to the `test` section to enable coverage reporting. Add the `coverage` property with provider (use `@vitest/coverage-v8`), reporter options (text, html, json), and threshold settings (minimum 80% for lines, branches, functions, statements).

*   **File:** `frontend/package.json`
    *   **Summary:** Currently has basic test script `"test": "vitest"`. No coverage-specific script or coverage dependencies present. The package uses Vitest 1.0.0.
    *   **Recommendation:** You MUST add `@vitest/coverage-v8` as a devDependency. You SHOULD add a separate `"test:coverage"` script that runs `vitest run --coverage` for one-time coverage generation, while keeping `"test"` for watch mode during development.

*   **File:** `frontend/tests/setup.ts`
    *   **Summary:** Basic Vitest setup with `@testing-library/jest-dom` imports and cleanup after each test. This is correctly configured.
    *   **Recommendation:** This file is properly configured. You can OPTIONALLY add global mocks here (e.g., for window.matchMedia which MUI components might use).

*   **File:** `frontend/.eslintrc.json`
    *   **Summary:** Comprehensive ESLint configuration with TypeScript, React, and React Hooks plugins. Already configured with recommended rules and type checking enabled. Has specific overrides for test files.
    *   **Recommendation:** The configuration is already strong. You MUST ensure all frontend code passes these linting rules. Run `npm run lint` and fix any violations.

*   **File:** `frontend/.prettierrc`
    *   **Summary:** Prettier configuration with line length 100, single quotes, trailing commas, and other standard settings.
    *   **Recommendation:** You MUST run `npm run format` (or add this script if missing) to format all files. The configuration is already correct.

*   **File:** `frontend/src/api/client.ts`
    *   **Summary:** Complex API client with axios interceptors for JWT injection and automatic token refresh. Includes retry logic and queuing for concurrent requests during token refresh.
    *   **Recommendation:** This file has complex logic that SHOULD be unit tested separately. Create `frontend/tests/unit/api/client.test.ts` to test: token injection, token refresh flow, request queuing, error handling. Mock axios and localStorage.

*   **File:** `frontend/src/context/AuthContext.tsx`
    *   **Summary:** Authentication context provider with login, logout, and refresh token methods. Manages authentication state and user profile.
    *   **Recommendation:** Create `frontend/tests/unit/context/AuthContext.test.tsx` to test the context provider. Test: initial state, login flow, logout flow, token refresh, error handling. You SHOULD use React Testing Library's `renderHook` utility for testing hooks.

*   **File:** `Makefile`
    *   **Summary:** Currently has targets for `up`, `down`, `test`, `e2e`, `lint`, and `logs`. The `test` target runs backend tests but frontend test command uses `|| true` which ignores failures.
    *   **Recommendation:** You MUST add `frontend:test` and `frontend:coverage` targets. Remove the `|| true` from the main test target for frontend to ensure failures are caught. The `frontend:test` target should run `cd frontend && npm test run` (for CI) and `frontend:coverage` should run `cd frontend && npm run test:coverage`.

*   **File:** `.github/workflows/ci-cd.yml`
    *   **Summary:** Currently a placeholder with only a basic checkout step. Needs complete implementation.
    *   **Recommendation:** You MUST implement proper CI jobs following the pipeline overview from the plan. Create separate jobs for: `frontend-lint`, `frontend-test`, `backend-lint`, `backend-test`, `integration-test`, `e2e-test`. Each job should fail the build on errors. Frontend test job MUST check coverage threshold.

### Implementation Tips & Notes

*   **Tip:** The existing test files (VehicleList.test.tsx, CommandForm.test.tsx, etc.) follow a good pattern with describe blocks for different scenarios (Loading State, Error State, Empty State, etc.). You SHOULD follow this same pattern for consistency.

*   **Tip:** I found that `@testing-library/jest-dom` is already installed and imported in tests/setup.ts. This provides helpful matchers like `toBeInTheDocument()`, `toBeVisible()`, etc. Use these extensively.

*   **Note:** The project uses TypeScript strict mode. All test files MUST be written in TypeScript with proper type annotations. Pay special attention to mocking - you'll need to properly type your mocks.

*   **Note:** For testing components that use React Router (like ProtectedRoute), you MUST wrap them in a `<MemoryRouter>` or `<BrowserRouter>` in your tests. Example pattern from existing tests shows proper component wrapping.

*   **Tip:** For testing the WebSocket client (`frontend/src/api/websocket.ts`) and ResponseViewer component, you'll need to mock WebSocket. Create a mock WebSocket class in your test file. The existing ResponseViewer.test.tsx likely already has this pattern - study it.

*   **Note:** The frontend uses MUI (Material-UI) components. These render with specific ARIA roles. Use `screen.getByRole()` queries in tests for better accessibility testing. For example, CircularProgress has role="progressbar".

*   **Warning:** The current Makefile target for frontend tests uses `|| true` which causes it to always succeed. This is INCORRECT for CI/CD. You MUST remove this so that test failures properly fail the build.

*   **Tip:** Vitest coverage threshold can be configured in vite.config.ts under `test.coverage.thresholds`. Set `lines: 80, branches: 80, functions: 80, statements: 80` to enforce the 80% requirement. The build should fail if coverage drops below this.

*   **Note:** For pre-commit hooks, the task suggests using husky. However, this is marked as OPTIONAL. Given time constraints, you MAY skip husky setup and just document the manual lint/format commands in the README. CI enforcement is more important.

*   **Tip:** When creating new test files for untested components, prioritize coverage of:
    1. `LoadingSpinner.tsx` - Simple, test rendering with different props
    2. `EmptyState.tsx` - Simple, test rendering with different props
    3. `ProtectedRoute.tsx` - Critical, test auth states (loading, authenticated, not authenticated)
    4. `VehicleSelector.tsx` - Test vehicle fetching and selection
    5. `Sidebar.tsx` - Test navigation rendering
    6. `Layout.tsx` - Test children rendering and header/sidebar integration
    7. Pages (VehiclesPage, CommandPage, ResponsePage, DashboardPage) - Test page rendering and component integration
    8. API client utility functions
    9. AuthContext provider

*   **Note:** The acceptance criteria specifically mentions "No console errors or warnings in tests". You MUST ensure your tests don't trigger console warnings. Common issues: missing act() warnings, React key warnings, unhandled promise rejections. Clean these up.

*   **Tip:** For testing API integration with mocked responses, use `vi.mock()` to mock the entire `../api/client` module. Return mock implementations of the API methods. See existing test files for patterns.

*   **Critical:** The task requires updating the GitHub Actions workflow to run frontend tests and linting. You MUST ensure the workflow includes:
    - A job that runs `npm install` in the frontend directory
    - A job that runs `npm run lint` (fails on errors)
    - A job that runs `npm run test:coverage` (fails if coverage < 80% or tests fail)
    - Proper caching of node_modules for faster builds
    - Upload of coverage reports as artifacts

*   **Note:** The plan specifies that the CI pipeline should complete in ~15 minutes total. Frontend tests should be fast (< 3 minutes). If tests are slow, consider running them in parallel or optimizing test setup.

---

## 4. Missing Components Requiring Test Coverage

Based on my analysis, the following components/modules exist in the codebase but do NOT have corresponding test files:

**High Priority (Critical functionality):**
1. `frontend/src/components/auth/ProtectedRoute.tsx` - No test file exists
2. `frontend/src/components/common/LoadingSpinner.tsx` - No test file exists
3. `frontend/src/components/common/EmptyState.tsx` - No test file exists
4. `frontend/src/components/common/Sidebar.tsx` - No test file exists
5. `frontend/src/components/common/Layout.tsx` - No test file exists
6. `frontend/src/components/vehicles/VehicleSelector.tsx` - No test file exists
7. `frontend/src/context/AuthContext.tsx` - No test file exists
8. `frontend/src/api/client.ts` - No test file exists (complex logic with interceptors)
9. `frontend/src/api/websocket.ts` - No test file exists

**Medium Priority (Pages):**
10. `frontend/src/pages/VehiclesPage.tsx` - No test file exists
11. `frontend/src/pages/CommandPage.tsx` - No test file exists
12. `frontend/src/pages/ResponsePage.tsx` - No test file exists
13. `frontend/src/pages/DashboardPage.tsx` - No test file exists
14. `frontend/src/pages/HistoryPage.tsx` - No test file exists
15. `frontend/src/pages/CommandsPage.tsx` - No test file exists

**Lower Priority (Utilities):**
16. `frontend/src/utils/dateUtils.ts` - No test file exists
17. `frontend/src/App.tsx` - No test file exists

**Already Tested (Existing test files):**
- ✅ `frontend/tests/components/VehicleList.test.tsx`
- ✅ `frontend/tests/components/CommandForm.test.tsx`
- ✅ `frontend/tests/components/ResponseViewer.test.tsx`
- ✅ `frontend/tests/components/ErrorBoundary.test.tsx`
- ✅ `frontend/tests/components/Header.test.tsx`
- ✅ `frontend/tests/components/LoginPage.test.tsx`

**Recommendation:** Focus on the High Priority items first, then Medium Priority. You can achieve 80% coverage without testing every single page if you focus on components with complex logic (AuthContext, API client, ProtectedRoute, etc.) and the critical user flows.

---

## 5. Acceptance Criteria Checklist

When you complete this task, verify ALL of these criteria:

- [ ] `make frontend:test` runs all frontend tests successfully (0 failures)
- [ ] Coverage report shows ≥80% line coverage for `frontend/src/` directory
- [ ] `npm run lint` (or `make frontend:lint`) passes with no errors
- [ ] `npm run format` (or `make frontend:format`) formats all files consistently
- [ ] Coverage HTML report generated in `frontend/coverage/` directory
- [ ] GitHub Actions workflow runs frontend tests and linting on push (verify workflow syntax is valid)
- [ ] Component tests cover: all pages, key components (VehicleList, CommandForm, ResponseViewer), common components (Header, ErrorBoundary)
- [ ] Tests verify: rendering, user interactions, API integration (with mocked API), error handling
- [ ] No console errors or warnings in tests
- [ ] All frontend code follows ESLint and Prettier rules

**Commands to verify:**
```bash
cd frontend
npm run lint                     # Should pass with 0 errors
npm run format                   # Should format files
npm run test:coverage            # Should show ≥80% coverage, 0 failures
cd ..
make frontend:test               # Should run tests successfully
make frontend:lint               # Should pass linting
```
