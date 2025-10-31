# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

**Task I4.T9: Performance Optimization and Bundle Analysis**

Optimize frontend performance and reduce bundle size. Implement: 1) Code splitting for routes (use React.lazy() for page components in `App.tsx`), 2) Image optimization (if images added, use appropriate formats and compression), 3) Analyze bundle size using `vite-plugin-bundle-analyzer`, identify large dependencies, 4) Tree-shake unused MUI components (import specific components instead of entire library), 5) Configure Vite build optimizations in `vite.config.ts` (minification, compression), 6) Add compression middleware to Nginx configuration (gzip for static files), 7) Implement service worker for caching static assets (optional, using Vite PWA plugin), 8) Measure and document performance metrics: First Contentful Paint (FCP), Time to Interactive (TTI), bundle size. Configure Lighthouse CI in GitHub Actions to track performance scores. Document performance benchmarks in README.

**Note:** The I4.T9 implementation is CORRECT and COMPLETE. However, there are pre-existing test failures from task I4.T8 (error handling) that must be fixed before I4.T9 can be marked as done.

---

## Issues Detected

The I4.T9 performance optimization implementation is complete and correct. However, there are 28 failing tests from the previous task (I4.T8 - Error Handling):

### ErrorToast Component Tests (11 failures in `tests/components/ErrorToast.test.tsx`)
*   **Test Timeout Errors:** All 11 tests in ErrorToast.test.tsx are timing out after 5000ms, indicating that the component is not rendering correctly or the test setup is incorrect.
*   Tests affected:
    - "displays error toast when error is triggered"
    - "displays error with correlation ID"
    - "displays success toast when success is triggered"
    - "displays warning toast when warning is triggered"
    - "displays info toast when info is triggered"
    - "stacks multiple toasts vertically"
    - "auto-dismisses error toast after 6 seconds"
    - "auto-dismisses success toast after 4 seconds"
    - "allows manual dismissal of toast via close button"
    - "displays correlation ID in separate section"
    - "handles multiple simultaneous errors with different correlation IDs"

### ConfirmDialog Component Tests (2 failures in `tests/components/ConfirmDialog.test.tsx`)
*   **Test Failure:** The test "does not render when open is false" is failing because `expect(element).not.toBeVisible()` is receiving `null` instead of an HTMLElement. The issue is that `queryByTestId('confirm-dialog')` returns `null` when the dialog is closed, and `.not.toBeVisible()` requires an element. Should use `.not.toBeInTheDocument()` instead.
*   **Test Failure:** The test "sets autoFocus on confirm button" is failing because the button doesn't have an `autofocus` attribute. MUI Button may use a different mechanism for auto-focus (like the `autoFocus` prop in React, not the HTML attribute).

### CommandDetailPage Tests (multiple failures in `tests/pages/CommandDetailPage.test.tsx`)
*   **Test Failure:** The test "should render page title and description" is failing because it cannot find the text "Command Details". The component is rendering an offline banner or error state instead of the expected content.

### API Retry Logic Tests (warnings in `tests/api/retryLogic.test.ts`)
*   **Warning:** "Not implemented: navigation to another Document" - This is a jsdom limitation warning when testing navigation, not a critical failure but should be addressed.

### Root Cause Analysis

The test failures are caused by incomplete or incorrect implementation of the I4.T8 error handling features:

1. **ErrorToast tests timing out:** The ErrorContext or ErrorToast component is likely not implemented correctly, causing tests to hang waiting for elements that never appear.

2. **ConfirmDialog tests failing:** The test assertions are using incorrect matchers for MUI Dialog behavior.

3. **CommandDetailPage tests failing:** The page is rendering error/offline state instead of normal content, likely due to the ErrorContext or offline detection interfering with test rendering.

4. **WebSocket errors in tests:** WebSocket connection errors in ResponseViewer tests suggest improper mocking or cleanup of WebSocket connections.

---

## Best Approach to Fix

**IMPORTANT:** The I4.T9 performance optimization code is complete and should NOT be modified. You must fix the I4.T8 test failures without changing any I4.T9 code.

### Fix 1: ErrorToast Component Tests

You MUST investigate why ErrorToast tests are timing out. Check the following:

1. Verify that `frontend/src/components/common/ErrorToast.tsx` is properly exporting the component
2. Verify that `frontend/src/context/ErrorContext.tsx` is correctly providing the error context
3. Check the test file `tests/components/ErrorToast.test.tsx` to ensure:
   - The ErrorProvider is properly wrapping the component in tests
   - The MUI ThemeProvider is included in the test wrapper
   - The test is calling the correct context methods to trigger toasts
   - The test is waiting for async operations with `waitFor()` or `await`

The most likely issue is that the ErrorToast component is not rendering because the ErrorContext is not properly set up in tests.

### Fix 2: ConfirmDialog Component Tests

You MUST fix the test assertions in `tests/components/ConfirmDialog.test.tsx`:

1. **For "does not render when open is false":** Change `expect(screen.queryByTestId('confirm-dialog')).not.toBeVisible()` to `expect(screen.queryByTestId('confirm-dialog')).not.toBeInTheDocument()` because MUI Dialog removes the element from the DOM when closed.

2. **For "sets autoFocus on confirm button":** Remove the test for the `autofocus` HTML attribute. MUI Button uses React's `autoFocus` prop which doesn't set an HTML attribute. Instead, test that the button has focus after the dialog opens: `expect(confirmButton).toHaveFocus()`.

### Fix 3: CommandDetailPage Tests

You MUST investigate why CommandDetailPage is not rendering the expected content. Check:

1. Verify that the test is properly mocking the API responses (useQuery hooks)
2. Verify that the ErrorContext and offline detection are properly mocked in tests
3. Ensure the test waits for async loading states to resolve before asserting on content

### Fix 4: WebSocket Warnings

You SHOULD suppress the WebSocket connection error warnings in tests by properly mocking WebSocket in the test setup or catching and suppressing expected errors in test teardown.

### Fix 5: Navigation Warnings

You SHOULD suppress the "Not implemented: navigation to another Document" warning by mocking `window.location` in tests that involve navigation.

---

## Verification Checklist

After fixing the tests, verify:

- [ ] All 28 failing tests now pass
- [ ] `npm run test:coverage` completes successfully with no test failures
- [ ] Coverage thresholds are still met (80%+ lines, 75%+ branches/functions)
- [ ] `npm run lint` passes with no errors
- [ ] `npm run build` succeeds with code splitting (this should already work)
- [ ] The I4.T9 performance optimization code remains unchanged

Only after ALL tests pass should you resubmit the code for verification.
