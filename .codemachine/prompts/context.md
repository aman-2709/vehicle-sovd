# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T1",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Create Command History page with paginated list. Implement history list component with columns: Command Name, Vehicle (VIN), Status, Submitted At, User, Actions. Add filters: vehicle, status, date range, user (admin sees all, engineers see own). Enhance backend GET /api/v1/commands for pagination and filtering with RBAC enforcement.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Architecture Blueprint Section 3.7; Requirements (command history).",
  "target_files": [
    "frontend/src/pages/HistoryPage.tsx",
    "frontend/src/components/commands/CommandHistory.tsx",
    "frontend/src/pages/CommandDetailPage.tsx",
    "backend/app/api/v1/commands.py",
    "backend/app/services/command_service.py",
    "backend/tests/integration/test_command_history.py"
  ],
  "input_files": [
    "backend/app/api/v1/commands.py",
    "backend/app/services/command_service.py"
  ],
  "deliverables": "Functional command history page with pagination/filtering; backend API enhancements; RBAC enforcement; tests.",
  "acceptance_criteria": "History page displays commands with pagination; Filtering by vehicle, status works; Engineers see only own commands; Admins see all; View Details navigates to detail page; Backend supports limit, offset, filters; Tests verify pagination, filtering, RBAC; Coverage ≥80%; No linter errors",
  "dependencies": [
    "I2.T3",
    "I3.T4"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: command-endpoints (from 04_Behavior_and_Communication.md)

```markdown
**Command Endpoints**

POST   /api/v1/commands
Headers:  Authorization: Bearer {token}
Request:  {
  "vehicle_id": "uuid",
  "command_name": "ReadDTC",
  "command_params": { "ecuAddress": "0x10", "format": "UDS" }
}
Response: {
  "command_id": "uuid",
  "status": "pending",
  "submitted_at": "2025-10-28T10:00:00Z",
  "stream_url": "wss://api.sovd.example.com/ws/responses/{command_id}"
}

GET    /api/v1/commands/{command_id}
Headers:  Authorization: Bearer {token}
Response: {
  "command_id": "uuid",
  "vehicle_id": "uuid",
  "command_name": "ReadDTC",
  "command_params": { ... },
  "status": "completed",
  "submitted_at": "2025-10-28T10:00:00Z",
  "completed_at": "2025-10-28T10:00:01.5Z"
}

GET    /api/v1/commands/{command_id}/responses
Headers:  Authorization: Bearer {token}
Response: [
  {
    "response_id": "uuid",
    "response_payload": { "dtcCode": "P0420", "description": "Catalyst System Efficiency Below Threshold" },
    "sequence_number": 1,
    "is_final": false,
    "received_at": "2025-10-28T10:00:01Z"
  },
  {
    "response_id": "uuid",
    "response_payload": { "status": "complete" },
    "sequence_number": 2,
    "is_final": true,
    "received_at": "2025-10-28T10:00:01.5Z"
  }
]

GET    /api/v1/commands
Headers:  Authorization: Bearer {token}
Query:    ?vehicle_id=uuid&status=completed&limit=20&offset=0
Response: [
  { "command_id": "uuid", "command_name": "ReadDTC", "status": "completed", ... }
]
```

### Context: rbac (from 05_Operational_Architecture.md)

```markdown
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

**Future Enhancement: Fine-Grained Permissions**
- Transition to permission-based model (e.g., `execute_command`, `view_all_commands`)
- Implement using Casbin or custom RBAC engine
```

### Context: communication-security (from 04_Behavior_and_Communication.md)

```markdown
**Communication Security**

**TLS Everywhere:**
- Client ↔ API Gateway: TLS 1.3 (HTTPS, WSS)
- API Gateway ↔ Backend Services: TLS (internal certificates)
- Backend ↔ Vehicle: TLS (mutual TLS for production)

**Authentication:**
- JWT tokens in Authorization header for REST APIs
- JWT token in query parameter for WebSocket (upgraded after validation)
- Token expiration: 15 minutes (access), 7 days (refresh)

**Authorization:**
- RBAC middleware validates user role for every endpoint
- Command execution requires `engineer` or `admin` role
- Admin-only endpoints (user management) enforce `admin` role

**Input Validation:**
- Pydantic models validate all request payloads
- SOVD Protocol Handler validates command structure against SOVD 2.0 spec
- SQL injection prevention via parameterized queries (SQLAlchemy ORM)
- XSS prevention via React's automatic escaping

**Rate Limiting:**
- API Gateway (Nginx) enforces rate limits: 100 req/min per user
- Prevents abuse and DoS attacks
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/api/v1/commands.py`
    *   **Summary:** This file contains the FastAPI router for command management endpoints. **CRITICAL:** It already implements a fully functional `GET /api/v1/commands` endpoint (lines 205-335) with comprehensive RBAC enforcement, pagination, and filtering support including vehicle_id, status, user_id (admin only), start_date, and end_date filters.
    *   **Recommendation:** You MUST examine this existing implementation carefully. The backend API endpoint is **ALREADY COMPLETE** and passes all tests in `test_command_history.py`. Your task is primarily to build the **FRONTEND** components that consume this API. Do NOT modify the backend unless you find a specific bug or need to add missing functionality that is not already there.
    *   **Key Implementation Details:**
        - Lines 266-297: RBAC enforcement - Engineers are automatically filtered to see only their own commands (effective_user_id = current_user.user_id), while admins can optionally filter by user_id or see all commands
        - Lines 242-264: Date parsing with proper error handling (ISO 8601 format with Z suffix replacement)
        - Lines 311-319: Filters dictionary construction passed to service layer
        - Lines 331-335: Response using CommandListResponse schema with commands list, limit, and offset

*   **File:** `backend/app/services/command_service.py`
    *   **Summary:** This file contains the business logic for command operations. It already includes `get_command_history()` function (lines 131-164) that delegates to the repository layer with all filter parameters.
    *   **Recommendation:** This service function is complete and functional. Do NOT modify unless there is a specific missing feature.

*   **File:** `backend/app/repositories/command_repository.py`
    *   **Summary:** This file contains the data access layer for commands. The `get_commands()` function (lines 102-144) implements comprehensive filtering with SQLAlchemy queries including vehicle_id, user_id, status, start_date, end_date filters, plus pagination with limit/offset, and ordering by submitted_at DESC (newest first).
    *   **Recommendation:** The repository layer is complete. It properly handles all filters and pagination. Do NOT modify.

*   **File:** `backend/app/dependencies.py`
    *   **Summary:** This file contains authentication and authorization dependency injection functions. It includes `get_current_user()` for JWT validation and `require_role()` factory function for role-based authorization.
    *   **Recommendation:** You MUST use `get_current_user()` in your frontend API calls to include the JWT token in the Authorization header. The user's role is embedded in the JWT and enforced by the backend.

*   **File:** `backend/app/schemas/command.py`
    *   **Summary:** This file defines Pydantic schemas for command-related API requests and responses. Key schemas:
        - `CommandResponse`: Complete command details with all fields (command_id, user_id, vehicle_id, command_name, command_params, status, error_message, submitted_at, completed_at)
        - `CommandListResponse`: Paginated response with commands list, limit, and offset
    *   **Recommendation:** Use these exact schemas for TypeScript type definitions in the frontend. The API returns data matching these schemas.

*   **File:** `backend/app/models/command.py` and `backend/app/models/user.py`
    *   **Summary:** SQLAlchemy ORM models defining the database schema. Command model has all necessary fields and relationships. User model includes role field for RBAC.
    *   **Recommendation:** These define the data structure you'll be displaying. Note that the Command model includes relationships to User and Vehicle, which means you can display user information if needed (though the current API doesn't return joined data).

*   **File:** `backend/tests/integration/test_command_history.py`
    *   **Summary:** **THIS IS CRITICAL** - This is a comprehensive test suite (714 lines) that verifies ALL the functionality you need to implement in the frontend. It contains:
        - TestCommandHistoryRBAC: Tests for engineers seeing only own commands, admins seeing all commands, admin filtering by user
        - TestCommandHistoryFiltering: Tests for filtering by vehicle, status, date range (start_date, end_date)
        - TestCommandHistoryPagination: Tests for pagination with limit/offset, combined with filters
        - TestCommandHistoryEdgeCases: Tests for no results, unauthorized access
    *   **Recommendation:** **READ THIS FILE CAREFULLY**. It documents exactly how the backend API behaves. Use this as a specification for what your frontend must support. All these tests already PASS, meaning the backend functionality is complete and working.

### Implementation Tips & Notes

*   **Tip 1 - Backend is Complete:** The backend API at `GET /api/v1/commands` is fully implemented with all required features (pagination, filtering, RBAC). All integration tests pass. Your primary task is to build the **FRONTEND** components.

*   **Tip 2 - RBAC is Automatic:** The backend automatically enforces RBAC. Engineers are filtered to see only their own commands - this happens on the backend (lines 266-270 of commands.py), so your frontend does NOT need to filter results. Simply display what the API returns. Admins can optionally use the `user_id` query parameter to filter by specific users.

*   **Tip 3 - Date Format:** The API accepts ISO 8601 date format for start_date and end_date query parameters (e.g., "2025-10-29T00:00:00Z"). The backend handles parsing and converts the 'Z' suffix to '+00:00' timezone format. Make sure your frontend date pickers generate this format.

*   **Tip 4 - Pagination:** The API supports standard limit/offset pagination. Default limit is 50, max is 100 (enforced by Query validator on line 212). Your frontend should implement "Load More" or page-based navigation.

*   **Tip 5 - Existing Frontend Patterns:** You already have working frontend pages:
    - `frontend/src/pages/VehiclesPage.tsx` - Shows list with React Query, filtering, and loading states
    - `frontend/src/pages/CommandPage.tsx` - Shows form submission with validation
    - `frontend/src/components/commands/ResponseViewer.tsx` - Shows detail view with data fetching
    - You SHOULD follow the same patterns (React Query for data fetching, MUI components, TypeScript strict typing)

*   **Tip 6 - API Client:** You have an existing API client at `frontend/src/api/client.ts` that automatically injects JWT tokens and handles token refresh. You SHOULD use this client for all API calls.

*   **Tip 7 - Authentication Context:** The `frontend/src/context/AuthContext.tsx` provides access to the current user's information including their role. You SHOULD use this to conditionally show/hide UI elements (e.g., user filter dropdown only for admins).

*   **Tip 8 - Status Values:** Based on the Command model, valid status values are: 'pending', 'in_progress', 'completed', 'failed'. Your status filter dropdown should include these options.

*   **Tip 9 - MUI Table Component:** For the history list, consider using MUI's `<Table>` component with `<TablePagination>` for a professional look that matches the existing UI theme. Alternatively, use `<DataGrid>` from `@mui/x-data-grid` for advanced features (sorting, filtering), but note this may require additional npm packages.

*   **Tip 10 - Navigation to Detail Page:** Your CommandHistory component should include an "Actions" column with a "View Details" button that navigates to a detail page showing the full command info and responses. You can create a new route like `/commands/:commandId` that uses the existing `ResponseViewer` component.

*   **Tip 11 - Vehicle VIN Display:** The current API returns vehicle_id (UUID), not the VIN string. You have two options:
    1. Make a separate API call to `GET /api/v1/vehicles/{vehicle_id}` to fetch VIN (recommended for accuracy)
    2. Accept that the table will show vehicle_id instead of VIN (simpler, but less user-friendly)
    The task description requests "Vehicle (VIN)", so option 1 is preferred, but may require caching or pre-fetching vehicle data.

*   **Tip 12 - User Display:** Similarly, the API returns user_id, not username. If the task requires showing usernames, you may need to fetch user data or extend the backend API to join user information (but read the acceptance criteria carefully - it may only require user_id).

*   **Note:** The backend test file (`test_command_history.py`) uses mocks because it's testing the API endpoint logic, not end-to-end database queries. When you manually test your frontend, ensure your local backend is running with the actual database so you see real data.

*   **Warning:** Do NOT create a new `GET /api/v1/commands` endpoint or modify the existing one unless you find a specific bug. The endpoint is already feature-complete. Focus your backend work on writing additional tests if coverage is below 80% or fixing any bugs you discover during frontend testing.

*   **Testing Strategy:** The acceptance criteria requires ≥80% test coverage. The backend integration tests already exist and pass. You MUST write frontend component tests for:
    - HistoryPage rendering and loading states
    - CommandHistory component with mock data
    - Filter interactions (vehicle dropdown, status dropdown, date pickers)
    - Pagination controls (Next, Previous, page size)
    - RBAC behavior (engineers vs admins)
    - Navigation to CommandDetailPage
