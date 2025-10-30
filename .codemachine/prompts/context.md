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
  "dependencies": ["I3.T4", "I3.T5", "I3.T6", "I3.T7", "I3.T8"],
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
```

### Context: ci-cd-pipeline (from 03_Verification_and_Glossary.md)

```markdown
### 5.2. CI/CD Pipeline Integration

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
```

### Context: technology-stack (from 02_Architecture_Overview.md)

```markdown
#### Technology Selection Matrix

| **Layer/Concern** | **Technology** | **Justification** |
|-------------------|----------------|-------------------|
| **Frontend Framework** | React 18 + TypeScript | Industry-standard component model; TypeScript provides type safety; extensive ecosystem; strong community support; meets requirement. |
| **Frontend State Management** | React Context + React Query | React Query for server state (caching, sync); Context for auth/global UI state; avoids Redux complexity for this scale. |
| **Frontend Build** | Vite | Fast dev server and build times; superior to CRA; excellent TypeScript support; optimized production bundles. |
| **Frontend UI Library** | Material-UI (MUI) | Comprehensive component library; automotive industry precedent; accessibility built-in; professional appearance. |
| **Testing - Frontend** | Vitest + React Testing Library | Vite-native; fast; compatible with Jest patterns; RTL for component testing. |
| **Code Quality - Frontend** | ESLint + Prettier + TypeScript | Requirements specified; catches errors; consistent formatting; type safety. |
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Current Test Coverage Status

**Overall Coverage: 90.19%** (Already exceeds 80% target!)

**Coverage by Module:**
- **api/client.ts**: 44.35% - **NEEDS SIGNIFICANT IMPROVEMENT**
- **api/websocket.ts**: 89% - Good coverage
- **components/auth**: 100% - Excellent
- **components/commands**: 99.05% - Excellent
- **components/common**: 95.53% - Excellent
- **components/vehicles**: 96.49% - Excellent (VehicleSelector has some gaps)
- **context/AuthContext.tsx**: 95% - Very good
- **utils/dateUtils.ts**: 94.59% - Very good

### Critical Files Requiring Attention

#### 1. API Client (`frontend/src/api/client.ts`)
**Current Coverage: 44.35%** - This is the PRIMARY area needing work.

**Summary:** This file contains the core axios instance with JWT token management, automatic token refresh logic, and all API method definitions (auth, vehicle, command APIs). It has extensive interceptor logic for handling 401 responses and token refresh queuing.

**Uncovered Lines:** 118-222, 234-236 (based on coverage report)

**CRITICAL IMPLEMENTATION NOTES:**
- Lines 118-222 contain the **token refresh logic** - this is complex and needs thorough testing
- The file uses a queue system (`failedQueue`) to handle concurrent requests during token refresh
- Interceptors modify request/response flows - you MUST test these in isolation
- The `processQueue` function handles resolution/rejection of queued requests
- Token refresh involves `localStorage.getItem('refresh_token')` and `window.location.href` redirects

**Testing Strategy YOU MUST Follow:**
1. **Mock axios and test the interceptors directly** - Don't try to test through the exported API methods alone
2. **Test token refresh scenarios:**
   - 401 response triggers refresh
   - Multiple concurrent 401s queue properly
   - Failed refresh clears tokens and redirects
   - Successful refresh retries original request
3. **Test the exported API methods** (authAPI, vehicleAPI, commandAPI)
4. **Mock localStorage** and **window.location** for testing
5. **Test edge cases:**
   - No refresh token available
   - Refresh endpoint returns 401
   - Token refresh in progress when new 401 arrives

**Required Tools:**
```typescript
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter'; // You'll need to install this: npm install --save-dev axios-mock-adapter
```

#### 2. VehicleSelector Component (`frontend/src/components/vehicles/VehicleSelector.tsx`)
**Current Coverage: 91.2%** (Lines 55-56, 73-75, 78-80 uncovered)

**Summary:** Dropdown component for selecting vehicles, filters to show only connected vehicles, integrates with React Query for data fetching.

**CRITICAL IMPLEMENTATION NOTES:**
- Uncovered lines are likely error handling or edge cases
- You SHOULD add tests for:
  - Empty vehicle list
  - Loading state
  - Error state when API fails
  - Filtering logic (only connected vehicles)

#### 3. WebSocket Client (`frontend/src/api/websocket.ts`)
**Current Coverage: 89%** (Lines 55-156, 167-169 uncovered)

**Summary:** WebSocket connection management for real-time response streaming.

**Recommendation:** While coverage is good (89%), the uncovered lines likely represent error handling. Consider adding tests for connection failures and message parsing errors.

### Existing Test Patterns to Follow

**Pattern from VehicleList.test.tsx:**
```typescript
describe('Component Name', () => {
  describe('Feature Group (e.g., Loading State)', () => {
    it('should do specific thing', () => {
      render(<Component {...props} />);
      expect(screen.getByRole('...')).toBeInTheDocument();
    });
  });
});
```

**Key Testing Utilities Used:**
- `render` from '@testing-library/react'
- `screen` for querying elements
- `userEvent` for simulating interactions (async)
- `waitFor` for async operations
- `vi.fn()` for mock functions
- `vi.mock()` for module mocking

### Configuration Files - Already Correct

#### Vitest Configuration (`frontend/vite.config.ts`)
- ✅ Coverage thresholds already set: lines: 80, branches: 75, functions: 75, statements: 80
- ✅ Coverage includes: `src/**/*.{ts,tsx}`
- ✅ Coverage excludes: tests, pages, App.tsx, main.tsx (correct - these are integration level)
- ✅ Reporter configured: ['text', 'html', 'json', 'lcov']
- **NO CHANGES NEEDED** to vite.config.ts

#### ESLint Configuration (`.eslintrc.json`)
- ✅ Already configured with React, TypeScript, and React Hooks rules
- ✅ Test file overrides present
- **NO CHANGES NEEDED** to ESLint config

#### Prettier Configuration (`.prettierrc`)
- ✅ Already configured with sensible defaults
- **NO CHANGES NEEDED** to Prettier config

### Makefile Updates Required

**Current Issues:**
1. Line 37: `npm test run` is **INCORRECT** - should be `npm run test` or just `npm test`
2. Missing `frontend:coverage` target (required by acceptance criteria)

**YOU MUST:**
1. Fix line 37 in Makefile: Change `npm test run` to `npm test`
2. Ensure `frontend:coverage` target exists and works (Line 40-43 already has it!)

### CI/CD Workflow - Already Implemented

**Good News:** `.github/workflows/ci-cd.yml` is already comprehensive!
- ✅ Frontend linting job exists (ESLint + Prettier)
- ✅ Frontend test job exists with coverage check
- ✅ Coverage artifacts uploaded
- ✅ Runs on push to main/master/develop branches
- **VERIFY** the workflow syntax is valid by running it

### Implementation Tips & Notes

**Tip 1: Installing axios-mock-adapter**
You WILL need `axios-mock-adapter` for testing the API client. Install it:
```bash
npm install --save-dev axios-mock-adapter
```

**Tip 2: Mocking localStorage**
Use Vitest's built-in mocking:
```typescript
beforeEach(() => {
  const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  };
  global.localStorage = localStorageMock as any;
});
```

**Tip 3: Mocking window.location**
```typescript
delete (window as any).location;
window.location = { href: '' } as any;
```

**Tip 4: Testing Axios Interceptors**
You need to test the interceptors by triggering actual axios requests with mocked responses, not by calling the interceptor functions directly.

**Tip 5: Test File Naming**
Create: `frontend/tests/api/client.test.ts` (note: `.ts` not `.tsx` since no JSX)

**Warning 1: Don't Over-Test**
The acceptance criteria explicitly excludes pages and App.tsx from coverage requirements (see vite.config.ts lines 40-41). DO NOT waste time writing tests for pages - they are considered integration-level and are covered by E2E tests.

**Warning 2: Coverage Already Exceeds Target**
Current coverage is 90.19% overall. The main issue is the **unbalanced coverage** where api/client.ts drags down the average. Focus efforts on the API client tests specifically.

**Warning 3: Existing Tests Are Comprehensive**
Don't duplicate existing tests. Review the 13 existing test files carefully before writing new ones. Most components already have excellent coverage.

### Test Execution Verification Steps

After implementing your tests:

1. **Run tests locally:**
   ```bash
   cd frontend
   npm test
   npm run test:coverage
   ```

2. **Verify coverage thresholds pass:**
   - Lines: ≥80%
   - Branches: ≥75%
   - Functions: ≥75%
   - Statements: ≥80%

3. **Check linting:**
   ```bash
   npm run lint
   npm run format
   ```

4. **Verify Makefile targets work:**
   ```bash
   make frontend:test
   make frontend:coverage
   make frontend:lint
   make frontend:format
   ```

5. **Commit and push to trigger CI**

### Files You MUST Create or Modify

**Create:**
- `frontend/tests/api/client.test.ts` (NEW - critical priority)
- Additional tests for VehicleSelector edge cases (optional, low priority)

**Modify:**
- `Makefile` (fix line 37: `npm test run` → `npm test`)
- Verify `.github/workflows/ci-cd.yml` is correct (likely already good)

**Do NOT Modify:**
- `frontend/vite.config.ts` (already correctly configured)
- `frontend/.eslintrc.json` (already correctly configured)
- `frontend/.prettierrc` (already correctly configured)

### Final Strategic Recommendation

**Primary Focus: API Client Tests**
The API client (`frontend/src/api/client.ts`) is the ONLY file significantly below the 80% threshold. This is where you should invest 80% of your effort. Specifically:

1. Write comprehensive tests for the token refresh interceptor logic
2. Test all exported API methods (authAPI, vehicleAPI, commandAPI)
3. Test error handling and edge cases
4. Achieve at least 80% coverage on this file

**Secondary Focus: Minor Fixes**
- Fix Makefile line 37
- Verify CI workflow syntax
- Add a few edge case tests for VehicleSelector (optional)

**Success Criteria:**
When you run `npm run test:coverage`, you should see:
- Overall coverage: ≥80% (currently 90.19%, should stay above)
- api/client.ts: ≥80% (currently 44.35% - PRIMARY TARGET)
- All tests passing
- No linting errors
