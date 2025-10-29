# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Expand frontend component tests to achieve 80%+ coverage. Write additional tests for untested components and edge cases. Configure Vitest coverage reporting with `vitest --coverage`. Add `frontend:test` and `frontend:coverage` targets to root Makefile. Ensure all frontend tests pass. Run ESLint and Prettier on all frontend code, fix any violations. Configure Prettier to run on pre-commit hook (using husky or similar). Generate coverage HTML report. Update GitHub Actions CI workflow skeleton (from I1.T1) to run frontend tests and linting in CI pipeline.

**Acceptance Criteria:** `make frontend:test` runs all frontend tests successfully (0 failures); Coverage report shows ≥80% line coverage for `frontend/src/` directory; `npm run lint` (or `make frontend:lint`) passes with no errors; `npm run format` (or `make frontend:format`) formats all files consistently; Coverage HTML report generated in `frontend/coverage/` directory; GitHub Actions workflow runs frontend tests and linting on push (verify workflow syntax is valid); Component tests cover: all pages, key components (VehicleList, CommandForm, ResponseViewer), common components (Header, ErrorBoundary); Tests verify: rendering, user interactions, API integration (with mocked API), error handling; No console errors or warnings in tests; All frontend code follows ESLint and Prettier rules.

---

## Issues Detected

**CRITICAL:** The task acceptance criteria requires ≥80% coverage across ALL metrics, but the current code fails this requirement:

- **Function Coverage: 79.41%** - BELOW 80% threshold ❌
- **API Directory Coverage: 64.69%** - BELOW 80% threshold ❌
  - `frontend/src/api/client.ts`: **0% function coverage, 44.35% statement coverage** ❌
  - Uncovered lines in `client.ts`: 118-222, 234-236

**Specific Missing Tests:**

1. **No tests exist for `frontend/src/api/client.ts`** - This file contains critical authentication logic:
   - Token management functions (`setAccessToken`, `getAccessToken`)
   - Request interceptor (JWT token injection)
   - Response interceptor (401 handling and automatic token refresh)
   - Queue management for concurrent requests during token refresh (`processQueue`, `failedQueue`)
   - Auth API methods (`login`, `refresh`, `logout`, `getProfile`)
   - Vehicle API methods (`getVehicles`, `getVehicle`, `getVehicleStatus`)
   - Command API methods (`submitCommand`)

2. **Missing edge case coverage** - While `websocket.ts` has 100% function coverage, the overall function coverage needs to reach 80%+.

**What's Already Working:**
- ✓ All 132 tests passing (0 failures)
- ✓ ESLint passes with 0 errors
- ✓ Prettier formatting is correct
- ✓ Coverage HTML report generated in `frontend/coverage/`
- ✓ Statements: 90.19%, Branches: 87.17%, Lines: 90.19% (all above 80%)
- ✓ Makefile targets exist and work correctly
- ✓ GitHub Actions CI is properly configured

---

## Best Approach to Fix

**PRIMARY ACTION: Create comprehensive tests for `frontend/src/api/client.ts`**

You MUST create a new test file at `frontend/tests/api/client.test.ts` that achieves ≥80% coverage for the API client. Follow the existing test patterns from `frontend/tests/components/VehicleList.test.tsx`.

### Required Test Coverage for `client.test.ts`:

**1. Token Management Functions**
- Test `setAccessToken` and `getAccessToken` for storing and retrieving tokens
- Test that tokens are correctly set to null when cleared

**2. Request Interceptor Tests**
- Test that JWT token is injected into Authorization header for authenticated requests
- Test that token is NOT injected for `/auth/login` endpoint
- Test that token is NOT injected for `/auth/refresh` endpoint
- Test that requests without a token proceed without Authorization header

**3. Response Interceptor - 401 Token Refresh Flow**
- Test successful token refresh when 401 occurs (non-login endpoint)
- Test that the original request is retried with the new token after successful refresh
- Test that 401 errors on `/auth/login` endpoint do NOT trigger refresh
- Test that refresh failure redirects to `/login` and clears tokens
- Test that missing refresh token redirects to `/login` immediately
- Test concurrent requests during token refresh (queue management):
  - Multiple requests fail with 401 simultaneously
  - First request triggers refresh, subsequent requests are queued
  - All queued requests are retried with new token after successful refresh
  - All queued requests fail if refresh fails

**4. Auth API Methods**
- Test `authAPI.login` makes POST request to `/api/v1/auth/login` and returns token
- Test `authAPI.refresh` makes POST request to `/api/v1/auth/refresh` with refresh_token
- Test `authAPI.logout` makes POST request to `/api/v1/auth/logout`
- Test `authAPI.getProfile` makes GET request to `/api/v1/auth/me`

**5. Vehicle API Methods**
- Test `vehicleAPI.getVehicles` makes GET request to `/api/v1/vehicles` with query params
- Test `vehicleAPI.getVehicle` makes GET request to `/api/v1/vehicles/{id}`
- Test `vehicleAPI.getVehicleStatus` makes GET request to `/api/v1/vehicles/{id}/status`

**6. Command API Methods**
- Test `commandAPI.submitCommand` makes POST request to `/api/v1/commands`

### Implementation Tips:

**Mock Setup:**
```typescript
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest';
import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';

// Mock axios
vi.mock('axios', async () => {
  const actual = await vi.importActual('axios');
  return {
    ...actual,
    default: {
      ...actual.default,
      create: vi.fn(() => actual.default),
    },
  };
});

// Use axios-mock-adapter for interceptor testing
const mock = new MockAdapter(axios);

beforeEach(() => {
  mock.reset();
  localStorage.clear();
  // Reset module to clear interceptor state
  vi.resetModules();
});
```

**Testing Token Refresh Queue:**
```typescript
it('should queue concurrent requests during token refresh', async () => {
  // Setup: token refresh succeeds
  localStorage.setItem('refresh_token', 'valid-refresh-token');
  mock.onPost('/api/v1/auth/refresh').reply(200, { access_token: 'new-token' });

  // First request triggers 401
  mock.onGet('/api/v1/vehicles').replyOnce(401);
  // After refresh, retry succeeds
  mock.onGet('/api/v1/vehicles').reply(200, [{ id: '1' }]);

  // Make multiple concurrent requests
  const promise1 = vehicleAPI.getVehicles();
  const promise2 = vehicleAPI.getVehicles();

  // Both should resolve with data (not errors)
  const [result1, result2] = await Promise.all([promise1, promise2]);
  expect(result1).toEqual([{ id: '1' }]);
  expect(result2).toEqual([{ id: '1' }]);
});
```

**Testing window.location.href:**
```typescript
// Mock window.location
delete window.location;
window.location = { href: '' } as Location;

it('should redirect to login when refresh token is missing', async () => {
  mock.onGet('/api/v1/vehicles').reply(401);

  await expect(vehicleAPI.getVehicles()).rejects.toThrow();
  expect(window.location.href).toBe('/login');
});
```

### Dependencies:
You may need to install `axios-mock-adapter` if it's not already available:
```bash
cd frontend && npm install --save-dev axios-mock-adapter
```

### Success Criteria:
After implementing the tests, verify:
```bash
cd frontend
npm run test:coverage
```

Coverage must show:
- Functions: ≥80% (currently 79.41%)
- `api` directory: ≥80% (currently 64.69%)
- `api/client.ts`: ≥80% statements and functions (currently 44.35% / 0%)

All tests must pass with 0 failures.
