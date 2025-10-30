# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T8",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Enhance frontend error handling: global error toast with MUI Snackbar, retry logic for API calls (max 3 with backoff), offline detection banner, loading states on buttons, improved form validation, confirmation dialogs. Write component tests.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Architecture Blueprint Section 2.2 (NFRs - Usability).",
  "target_files": [
    "frontend/src/components/common/ErrorToast.tsx",
    "frontend/src/context/ErrorContext.tsx",
    "frontend/src/utils/errorMessages.ts",
    "frontend/src/api/client.ts",
    "frontend/src/components/common/OfflineBanner.tsx",
    "frontend/tests/components/ErrorToast.test.tsx"
  ],
  "input_files": [
    "frontend/src/api/client.ts"
  ],
  "deliverables": "Global error notifications; retry logic; offline detection; loading states; confirmations; tests.",
  "acceptance_criteria": "API errors show toast with user-friendly message; 503 errors retried 3x; Offline banner when offline; Buttons show spinner during calls; Form errors inline; Logout shows confirmation; Error codes mapped; Tests verify toast, retry, offline; No errors",
  "dependencies": [
    "I3.T4",
    "I4.T5"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Usability Requirements (from 01_Context_and_Drivers.md)

```markdown
<!-- anchor: nfr-usability -->
#### Usability
- **Intuitive UI**: Clean, modern interface following UX best practices
- **Error Handling**: Clear error messages with actionable guidance
- **Responsive Design**: Support for desktop and tablet form factors

**Architectural Impact**: Component-based UI framework (React), design system, comprehensive error handling middleware.
```

### Context: Error Handling Requirement (from 01_Context_and_Drivers.md)

```markdown
**Response Handling**
- Display command responses in structured, human-readable format
- Support for streaming responses with progressive rendering
- Response caching and history retrieval
- Error handling with clear diagnostic messages
```

### Context: Backend Error Code System (from error_codes.py)

The backend implements a hierarchical error code system with the following categories:
- **RATE_001**: Rate limit exceeded
- **AUTH_xxx**: Authentication errors (invalid credentials, expired tokens, insufficient permissions)
- **VAL_xxx**: Validation errors (vehicle not found, invalid command, missing fields)
- **DB_xxx**: Database errors (connection failed, query timeout)
- **VEH_xxx**: Vehicle communication errors (unreachable, timeout, invalid response)
- **SYS_xxx**: System errors (internal error, service unavailable, timeout)

All backend error responses follow this standardized format:
```json
{
  "error": {
    "code": "AUTH_001",
    "message": "Invalid username or password",
    "correlation_id": "uuid-here",
    "timestamp": "2025-10-30T14:48:00Z",
    "path": "/api/v1/auth/login"
  }
}
```

### Context: Error Status Code Mapping

The backend maps error codes to HTTP status codes:
- **401**: AUTH_INVALID_CREDENTIALS, AUTH_TOKEN_EXPIRED, AUTH_TOKEN_INVALID
- **403**: AUTH_INSUFFICIENT_PERMISSIONS, AUTH_USER_INACTIVE
- **404**: VAL_VEHICLE_NOT_FOUND, VAL_RESOURCE_NOT_FOUND
- **400**: VAL_INVALID_COMMAND, VAL_MISSING_FIELD, VAL_INVALID_FORMAT
- **429**: RATE_LIMIT_EXCEEDED
- **503**: VEH_UNREACHABLE, DB_CONNECTION_FAILED, SYS_SERVICE_UNAVAILABLE
- **504**: VEH_COMMAND_TIMEOUT, DB_QUERY_TIMEOUT, SYS_TIMEOUT
- **500**: VEH_COMMAND_FAILED, SYS_INTERNAL_ERROR

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/src/api/client.ts`
    *   **Summary:** This is the core API client using Axios with automatic JWT injection and token refresh logic. It has request/response interceptors that handle authentication (401) with automatic token refresh via a queuing mechanism.
    *   **Recommendation:** You MUST enhance this file to add retry logic for 503/504 errors. The current interceptor only handles 401 for token refresh. Add a new response interceptor that catches 503/504 errors and retries with exponential backoff (max 3 retries). DO NOT modify the existing 401 refresh logic - it's working correctly.
    *   **Implementation Note:** The retry logic should be added as a SEPARATE concern from token refresh. Use a retry counter on the config object (similar to `_retry` for token refresh) to track retry attempts. Implement exponential backoff: 1st retry after 1s, 2nd after 2s, 3rd after 4s.

*   **File:** `frontend/src/context/AuthContext.tsx`
    *   **Summary:** Authentication context managing JWT tokens and auth state. Access token in memory, refresh token in localStorage.
    *   **Recommendation:** You SHOULD integrate this with your ErrorContext to clear error state on successful logout. The logout function is already robust with try-catch, so errors during logout should be captured by your global error handler.

*   **File:** `backend/app/utils/error_codes.py`
    *   **Summary:** Backend error code enum with hierarchical categories (AUTH, VAL, DB, VEH, SYS) and mapping to HTTP status codes and user-friendly messages.
    *   **Recommendation:** You MUST create a frontend utility `errorMessages.ts` that maps backend error codes to user-friendly, actionable messages. Extract the error code from the backend response format `response.data.error.code` and map it to a friendly message. For unknown codes, fall back to the backend's `message` field.

*   **File:** `backend/app/middleware/error_handling_middleware.py`
    *   **Summary:** Global error handler that formats all exceptions into standardized responses with error codes and correlation IDs. All errors follow the format: `{error: {code, message, correlation_id, timestamp, path}}`.
    *   **Recommendation:** Your frontend ErrorContext MUST extract the `correlation_id` from error responses and display it in the error toast. This allows users to report errors with a specific ID that engineers can search in logs.

*   **File:** `frontend/src/components/common/Header.tsx`
    *   **Summary:** Application header with navigation and user profile menu. Logout is async with navigation to login after completion.
    *   **Recommendation:** You MUST add a confirmation dialog before logout. Create a reusable `ConfirmDialog` component that you can use here and in other components. The confirmation should say "Are you sure you want to log out?" with Cancel and Confirm buttons.

*   **File:** `frontend/src/components/common/LoadingSpinner.tsx`, `ErrorBoundary.tsx`, `EmptyState.tsx`
    *   **Summary:** Common UI components already exist for loading states, error boundaries, and empty states.
    *   **Recommendation:** You SHOULD leverage these existing patterns. Your ErrorToast should follow similar MUI component structure and theming. The LoadingSpinner can be reused in button loading states.

### Implementation Tips & Notes

*   **Tip:** MUI provides `Snackbar` and `Alert` components that work together for toast notifications. Use `Alert` inside `Snackbar` for severity levels (error, warning, info, success). Position the Snackbar at `anchorOrigin={{ vertical: 'top', horizontal: 'center' }}` for maximum visibility.

*   **Note:** For offline detection, use the browser's `navigator.onLine` API along with event listeners for `online` and `offline` events. Create a React hook `useOnlineStatus` that returns a boolean and can be used in any component.

*   **Tip:** The retry logic should ONLY retry on network errors or 503/504 status codes. DO NOT retry 400/401/403/404 errors - these are client errors that won't be fixed by retrying. Use Axios error type checking: `axios.isAxiosError(error)` and check `error.response?.status`.

*   **Note:** For button loading states, Material-UI Button accepts a `loading` prop when using the LoadingButton component from `@mui/lab`. However, this package may not be installed. Instead, you can add a `CircularProgress` component as a startIcon: `startIcon={isLoading ? <CircularProgress size={20} /> : null}`.

*   **Tip:** Error message mapping should be comprehensive. Based on the error codes, create friendly messages like:
    - `AUTH_001`: "Invalid username or password. Please try again."
    - `AUTH_002`: "Your session has expired. Please log in again."
    - `VEH_UNREACHABLE`: "The vehicle is currently unreachable. Please check vehicle connectivity."
    - `RATE_001`: "Too many requests. Please wait a moment before trying again."

*   **Warning:** DO NOT display raw error messages from the backend directly to users without mapping. Some error messages may contain technical details that confuse non-technical users. Always map error codes to user-friendly messages first, and only fall back to the backend message if no mapping exists.

*   **Tip:** The ErrorContext should provide functions like `showError(message, options?)`, `showSuccess(message)`, `showInfo(message)`, `clearErrors()`. This makes it easy for any component to trigger notifications. Store errors in a queue to support multiple simultaneous toasts.

*   **Note:** For form validation errors (422), the backend returns detailed validation messages in the format `"field -> nested: message"`. Your error mapping should handle these specially and extract just the validation messages without the technical field paths when possible.

*   **Tip:** The offline banner should be non-dismissible and sticky at the top of the page (above the header or just below it). Use MUI `Alert` with severity "warning" and icon. It should automatically disappear when the connection is restored.

*   **Note:** Confirmation dialogs should use MUI `Dialog` with `DialogTitle`, `DialogContent`, and `DialogActions`. Create a reusable `ConfirmDialog` component that accepts props: `open`, `title`, `message`, `onConfirm`, `onCancel`, `confirmText`, `cancelText`.

*   **Warning:** When implementing retry logic, be careful with the interceptor order. The retry interceptor should run BEFORE the token refresh interceptor, so that retries don't interfere with token refresh attempts. Add the retry interceptor first, then the token refresh interceptor.

*   **Tip:** For testing, use `vitest` with `@testing-library/react`. Mock the Axios instance for testing retry logic. Use `waitFor` from testing-library to test async error handling. Mock `navigator.onLine` for offline detection tests.

### Critical Success Factors

1. **User-Friendly Messages**: Error codes must be mapped to clear, actionable messages that guide users on what to do next
2. **Correlation ID Visibility**: Always display the correlation_id in error toasts so users can report issues with a reference ID
3. **Retry Logic Precision**: Only retry network errors and 503/504 (service unavailable/timeout), never retry 4xx errors
4. **Non-Intrusive Loading**: Loading states should be clear but not block the entire UI - use button-level spinners
5. **Graceful Offline**: The offline banner should be informative and automatically appear/disappear based on connection state
6. **Test Coverage**: Achieve 80%+ coverage by testing error toast display, retry behavior, offline detection, and confirmation dialogs
7. **Accessibility**: Ensure toasts are announced to screen readers (MUI Alert has aria-live by default)
8. **No Duplicate Handlers**: DO NOT modify the existing 401 token refresh logic - it's working correctly

### Component Architecture Recommendations

**ErrorContext Structure:**
```typescript
interface ErrorContextType {
  showError: (message: string, options?: { code?: string; correlationId?: string }) => void;
  showSuccess: (message: string) => void;
  showWarning: (message: string) => void;
  showInfo: (message: string) => void;
  clearError: (id: string) => void;
  clearAllErrors: () => void;
}
```

**Error Toast Queue:**
- Support multiple simultaneous toasts (stack them vertically)
- Each toast should auto-dismiss after 6 seconds for errors, 4 seconds for success
- User can manually dismiss by clicking the close button
- Store toasts in an array in context state

**Retry Logic Flow:**
```
1. Request fails with 503/504 or network error
2. Check retry count on config (_retryCount)
3. If < 3, increment count and wait (exponential backoff)
4. Retry the request with updated config
5. If still fails after 3 attempts, reject and show error toast
```

**Offline Detection Hook:**
```typescript
function useOnlineStatus(): boolean {
  const [isOnline, setIsOnline] = useState(navigator.onLine);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return isOnline;
}
```
