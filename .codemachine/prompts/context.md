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

### Note: Architecture Documents Not Found

The architecture documents referenced in the task inputs (Architecture Blueprint Section 3.7, 02_Architecture_Overview.md, 04_Behavior_and_Communication.md) could not be located in the expected paths. However, based on the codebase analysis and the OpenAPI specification found at `docs/api/openapi.yaml`, I can provide the following context:

### API Endpoints Context (from existing implementation)

The existing command API implementation (`backend/app/api/v1/commands.py`) provides:

1. **POST /api/v1/commands** - Submit command (requires engineer/admin role)
2. **GET /api/v1/commands/{command_id}** - Get single command details
3. **GET /api/v1/commands/{command_id}/responses** - Get command responses
4. **GET /api/v1/commands** - List commands with filters (already supports: vehicle_id, status, limit, offset)

The list endpoint (GET /api/v1/commands) ALREADY has most of the required functionality:
- Pagination via `limit` and `offset` query parameters
- Filtering by `vehicle_id` and `status`
- Authentication required via `get_current_user` dependency

**What's Missing for I4.T1:**
1. **RBAC Enforcement**: Currently NO role-based filtering (engineers see all commands, not just their own)
2. **User Filter**: No `user_id` filter in the API endpoint (though backend service supports it)
3. **Date Range Filter**: No date filtering capability
4. **Frontend**: No History page or CommandHistory component exists yet
5. **Command Detail Page**: No dedicated detail page for viewing single command

### Command Data Model Context

From `backend/app/models/command.py`:
- `command_id`: UUID (primary key)
- `user_id`: UUID (foreign key to users)
- `vehicle_id`: UUID (foreign key to vehicles)
- `command_name`: String (SOVD command identifier)
- `command_params`: JSONB (command parameters)
- `status`: String ('pending', 'in_progress', 'completed', 'failed')
- `error_message`: Text (optional)
- `submitted_at`: DateTime with timezone
- `completed_at`: DateTime with timezone (nullable)
- Relationships: `user`, `vehicle`, `responses`, `audit_logs`

### Authentication & Authorization Context

From `backend/app/dependencies.py`:
- `get_current_user()`: Extracts user from JWT token, returns User object
- `require_role(allowed_roles)`: Factory function for role-based access control
- User roles: "engineer", "admin", "viewer"
- User object has: `user_id`, `username`, `email`, `role`, `is_active`

### RBAC Requirements for This Task

**Engineers (role="engineer")**:
- Should see ONLY commands they submitted (filter by `user_id == current_user.user_id`)
- Can filter by vehicle, status, date range

**Admins (role="admin")**:
- Should see ALL commands from all users
- Can filter by vehicle, status, date range, AND user

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### Backend Files

**File:** `backend/app/api/v1/commands.py`
- **Summary**: FastAPI router with command endpoints. The `list_commands` endpoint (line 205-263) already implements pagination and filtering.
- **Recommendation**: You MUST modify the `list_commands` endpoint to:
  1. Add RBAC enforcement: if `current_user.role == "engineer"`, force `filters["user_id"] = current_user.user_id`
  2. Add optional `user_id` query parameter (only usable by admins)
  3. Add optional date range query parameters: `start_date`, `end_date`
  4. The endpoint currently uses `get_current_user` dependency - this is CORRECT, keep it
- **Current Implementation**: Already has vehicle_id and status filters, limit/offset pagination

**File:** `backend/app/services/command_service.py`
- **Summary**: Business logic for command operations. The `get_command_history` function (line 131-160) supports user_id filtering.
- **Recommendation**: You SHOULD enhance `get_command_history` to:
  1. Accept `start_date` and `end_date` parameters for date range filtering
  2. The function ALREADY supports `user_id` filtering - you can use this!
- **Note**: Service layer correctly delegates to repository layer

**File:** `backend/app/repositories/command_repository.py`
- **Summary**: Data access layer for commands. The `get_commands` function (line 102-136) builds queries with filters.
- **Recommendation**: You MUST modify `get_commands` to:
  1. Add `start_date` and `end_date` parameters
  2. Add date range filtering using SQLAlchemy's `Command.submitted_at >= start_date` and `Command.submitted_at <= end_date`
  3. Use `.where()` clauses like the existing vehicle_id and status filters (see lines 126-131)

**File:** `backend/app/models/command.py`
- **Summary**: SQLAlchemy ORM model for Command entity with all required fields
- **Recommendation**: You SHOULD use the existing relationships:
  - `command.user` to access user information (for displaying username)
  - `command.vehicle` to access vehicle information (for displaying VIN)
  - These relationships are already defined with proper foreign keys

**File:** `backend/app/schemas/command.py`
- **Summary**: Pydantic schemas for command API. Has `CommandResponse` and `CommandListResponse`.
- **Recommendation**: You MAY want to create an enhanced response schema that includes user and vehicle details (username, VIN) to avoid N+1 queries. Consider using SQLAlchemy's `joinedload` or create a new schema with nested user/vehicle objects.

**File:** `backend/app/dependencies.py`
- **Summary**: Authentication and authorization dependencies
- **Recommendation**: You MUST use `get_current_user` to access the authenticated user and check `current_user.role` for RBAC enforcement. The `require_role` factory is already available but NOT needed for this endpoint since both engineers and admins can access it (with different filtering).

#### Frontend Files

**File:** `frontend/src/pages/CommandPage.tsx`
- **Summary**: Existing page for command submission with vehicle selector and form
- **Recommendation**: You SHOULD follow the same component structure pattern:
  - Use MUI components (Container, Paper, Typography, Grid, Box)
  - Use React Query (`useQuery`, `useMutation`) for data fetching
  - Implement loading, error, and empty states
  - This is the BEST reference for styling and layout consistency

**File:** `frontend/src/components/vehicles/VehicleList.tsx`
- **Summary**: Table component displaying vehicles with status chips
- **Recommendation**: You SHOULD use this as a template for CommandHistory component:
  - Uses MUI Table with TableContainer, TableHead, TableBody, TableRow, TableCell
  - Implements loading state with CircularProgress
  - Implements error state with Alert
  - Implements empty state with Typography
  - Uses formatRelativeTime utility for timestamps (see line 126)
  - Uses Chip component for status display with color coding (see lines 117-122)

**File:** `frontend/src/context/AuthContext.tsx`
- **Summary**: Authentication context providing user profile and role
- **Recommendation**: You MUST use the `useAuth()` hook to:
  1. Get the current user's role: `const { user } = useAuth()`
  2. Check if `user?.role === "admin"` to show/hide the user filter
  3. The user profile includes: username, role, user_id

**File:** `frontend/src/api/client.ts`
- **Summary**: Axios client with JWT injection and token refresh
- **Recommendation**: You MUST extend this file to add a `commandAPI.getCommandHistory()` function with query parameters for filters. Follow the pattern used for other API calls (see the existing commandAPI structure starting around line 150+).

### Implementation Tips & Notes

#### Backend Tips

**Tip 1: RBAC Enforcement Pattern**
```python
# In backend/app/api/v1/commands.py, modify list_commands endpoint:
async def list_commands(
    vehicle_id: uuid.UUID | None = Query(None, description="Filter by vehicle ID"),
    status: str | None = Query(None, description="Filter by command status"),
    user_id: uuid.UUID | None = Query(None, description="Filter by user ID (admin only)"),
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CommandListResponse:
    # RBAC enforcement
    if current_user.role == "engineer":
        # Engineers can only see their own commands
        filters["user_id"] = current_user.user_id
    elif current_user.role == "admin":
        # Admins can optionally filter by user_id or see all
        if user_id is not None:
            filters["user_id"] = user_id
    # Otherwise (viewers, etc.) might have different logic
```

**Tip 2: Date Range Filtering in Repository**
```python
# In backend/app/repositories/command_repository.py, add to get_commands:
if start_date is not None:
    query = query.where(Command.submitted_at >= start_date)
if end_date is not None:
    query = query.where(Command.submitted_at <= end_date)
```

**Tip 3: Eager Loading to Avoid N+1 Queries**
You SHOULD use SQLAlchemy's `selectinload` or `joinedload` to load user and vehicle relationships:
```python
from sqlalchemy.orm import selectinload

query = select(Command).options(
    selectinload(Command.user),
    selectinload(Command.vehicle)
)
```
This allows you to access `command.user.username` and `command.vehicle.vin` without additional database queries.

**Tip 4: Testing Pattern**
Based on `backend/tests/integration/test_command_api.py`, you SHOULD:
- Create test fixtures for engineer and admin users
- Use `create_access_token()` to generate test JWT tokens
- Test both engineer (filtered) and admin (unfiltered) access
- Verify that engineers CANNOT see other users' commands
- Verify pagination works correctly (test with offset > 0)

#### Frontend Tips

**Tip 5: Date Filtering UI**
You SHOULD use MUI's DatePicker component (from `@mui/x-date-pickers`) for date range filters. However, I did NOT find this dependency in the codebase. You MAY need to:
1. Add the dependency: `npm install @mui/x-date-pickers`
2. OR use simple text inputs with type="date" for MVP
3. OR create a simple TextField with date format validation

**Tip 6: Table Columns for CommandHistory**
Based on the task description, your table MUST have these columns:
1. **Command Name**: `command.command_name`
2. **Vehicle (VIN)**: You'll need to fetch this from the vehicle relationship or join
3. **Status**: Use Chip component with color coding (success=completed, error=failed, default=pending/in_progress)
4. **Submitted At**: Use `formatRelativeTime(command.submitted_at)` utility
5. **User**: Display username (only for admins, or always?)
6. **Actions**: Button or link to "View Details" → navigate to CommandDetailPage

**Tip 7: Conditional Filter Display**
```typescript
const { user } = useAuth();
const isAdmin = user?.role === 'admin';

// In your render:
{isAdmin && (
  <TextField
    label="Filter by User"
    value={userFilter}
    onChange={(e) => setUserFilter(e.target.value)}
  />
)}
```

**Tip 8: React Query for History Fetching**
```typescript
const { data, isLoading, error } = useQuery({
  queryKey: ['commandHistory', { vehicleId, status, userId, startDate, endDate, limit, offset }],
  queryFn: () => commandAPI.getCommandHistory({
    vehicle_id: vehicleId,
    status,
    user_id: userId,
    start_date: startDate,
    end_date: endDate,
    limit,
    offset
  }),
  // Auto-refresh every 30 seconds (optional)
  refetchInterval: 30000,
});
```

**Tip 9: Navigation to Detail Page**
Use React Router's `useNavigate()`:
```typescript
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();

const handleViewDetails = (commandId: string) => {
  navigate(`/commands/${commandId}`);
};
```
Don't forget to add the route in `App.tsx`!

**Tip 10: Pagination Controls**
You SHOULD implement pagination using MUI's Pagination component or TablePagination. Example:
```typescript
<TablePagination
  component="div"
  count={-1}  // Unknown total (server doesn't return it)
  page={currentPage}
  onPageChange={handlePageChange}
  rowsPerPage={limit}
  onRowsPerPageChange={handleLimitChange}
  rowsPerPageOptions={[10, 25, 50, 100]}
/>
```

### Implementation Warnings & Gotchas

**Warning 1: Backend Already Has Most Functionality**
The backend `GET /api/v1/commands` endpoint ALREADY supports vehicle_id, status, limit, and offset. You ONLY need to add:
- RBAC enforcement (engineer vs admin filtering)
- user_id query parameter (admin only)
- Date range parameters (start_date, end_date)
- DO NOT rewrite the entire endpoint!

**Warning 2: Ensure Type Consistency**
The backend uses UUID types, but frontend/API uses string UUIDs. Ensure your frontend code:
- Passes vehicle_id, user_id as strings (they'll be converted on backend)
- Receives command_id, user_id, vehicle_id as strings in responses (Pydantic serializers handle this)

**Warning 3: Date Format**
PostgreSQL stores timestamps with timezone. When sending dates from frontend:
- Use ISO 8601 format: `2025-10-29T00:00:00Z`
- Consider timezone conversion for user-friendly date pickers
- The `submitted_at` field in responses will be in ISO format

**Warning 4: Test Coverage Requirement**
The acceptance criteria requires ≥80% coverage. You MUST write tests for:
- Backend: RBAC enforcement (engineer sees only own, admin sees all)
- Backend: Date range filtering works correctly
- Backend: Pagination works with new filters
- Frontend: CommandHistory component renders correctly
- Frontend: Filters work and trigger API calls
- Frontend: Admin sees user filter, engineer does not

**Warning 5: CommandDetailPage Scope**
The task mentions creating `CommandDetailPage.tsx`, but the acceptance criteria focuses on the history list. For the detail page:
- Create a SIMPLE page that displays a single command's details
- Reuse the existing `CommandResponse` type
- Include the ResponseViewer component (already exists from I3.T7)
- Add a "Back to History" button

### File Dependencies and Import Paths

**Backend Imports You MUST Use:**
```python
from app.dependencies import get_current_user
from app.models.user import User
from app.models.command import Command
from app.repositories.command_repository import get_commands
from sqlalchemy.orm import selectinload  # For eager loading
from datetime import datetime  # For date filtering
```

**Frontend Imports You SHOULD Use:**
```typescript
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { formatRelativeTime } from '../utils/dateUtils';
import {
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, Chip, Box, Typography, TextField, MenuItem, Button,
  TablePagination, CircularProgress, Alert
} from '@mui/material';
```

### Existing Utilities You SHOULD Reuse

1. **formatRelativeTime** (frontend/src/utils/dateUtils.ts): Already used in VehicleList for "Last Seen" column - use for "Submitted At" column
2. **get_current_user** (backend/app/dependencies.py): Already used in all command endpoints - use in enhanced list_commands
3. **structlog logger** (backend): Already used throughout backend for structured logging - add logs for RBAC decisions
4. **CommandResponse schema** (backend/app/schemas/command.py): Already defined - consider extending or enriching

---

## Summary Checklist for Coder Agent

### Backend Tasks (Priority Order):
1. ✅ Modify `backend/app/repositories/command_repository.py::get_commands()` to add start_date and end_date filtering
2. ✅ Modify `backend/app/services/command_service.py::get_command_history()` to pass date parameters
3. ✅ Modify `backend/app/api/v1/commands.py::list_commands()` to:
   - Add user_id, start_date, end_date query parameters
   - Implement RBAC enforcement (engineer sees only own commands)
   - Log RBAC filtering decisions
4. ✅ Write integration tests in `backend/tests/integration/test_command_history.py`:
   - Test engineer sees only own commands
   - Test admin sees all commands
   - Test date range filtering
   - Test pagination with filters
   - Verify ≥80% coverage

### Frontend Tasks (Priority Order):
1. ✅ Extend `frontend/src/api/client.ts` to add `commandAPI.getCommandHistory()` function
2. ✅ Create `frontend/src/pages/HistoryPage.tsx`:
   - Container with Paper layout
   - Filter controls (vehicle, status, date range, user [admin only])
   - Pagination controls
   - Integrate CommandHistory component
3. ✅ Create `frontend/src/components/commands/CommandHistory.tsx`:
   - MUI Table with columns: Command Name, Vehicle (VIN), Status, Submitted At, User, Actions
   - Use Chip for status (color coded)
   - Use formatRelativeTime for timestamps
   - "View Details" button → navigate to /commands/:id
4. ✅ Create `frontend/src/pages/CommandDetailPage.tsx`:
   - Display single command details
   - Include ResponseViewer component
   - "Back to History" button
5. ✅ Update `frontend/src/App.tsx` to add routes:
   - `/history` → HistoryPage
   - `/commands/:commandId` → CommandDetailPage
6. ✅ Write component tests for HistoryPage and CommandHistory
