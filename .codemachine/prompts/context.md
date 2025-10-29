# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T6",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Create Command Execution page `src/pages/CommandPage.tsx`. Implement: 1) Vehicle selector dropdown component `src/components/vehicles/VehicleSelector.tsx` (fetches vehicles via React Query, filters to connected vehicles only), 2) Command form component `src/components/commands/CommandForm.tsx` with fields: command_name (dropdown with options: ReadDTC, ClearDTC, ReadDataByID), command_params (dynamic form fields based on selected command - for ReadDTC: ecuAddress input), submit button, 3) Form validation using react-hook-form (required fields, valid ecuAddress format), 4) On submit, call `POST /api/v1/commands` API, 5) On success, display command_id and navigate to response viewer (placeholder for now), 6) On error, display validation errors or API error message. Create command types `src/types/command.ts`. Write component tests in `frontend/tests/components/CommandForm.test.tsx`.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "OpenAPI spec from I2.T9 (command endpoints); SOVD command schema from I2.T6.",
  "target_files": [
    "frontend/src/pages/CommandPage.tsx",
    "frontend/src/components/vehicles/VehicleSelector.tsx",
    "frontend/src/components/commands/CommandForm.tsx",
    "frontend/src/types/command.ts",
    "frontend/src/api/client.ts",
    "frontend/tests/components/CommandForm.test.tsx"
  ],
  "input_files": [
    "docs/api/openapi.yaml",
    "docs/api/sovd_command_schema.json",
    "frontend/src/api/client.ts"
  ],
  "deliverables": "Functional command submission page with vehicle selector; dynamic form based on command type; form validation; API integration; component tests.",
  "acceptance_criteria": "Command page displays vehicle selector dropdown (populated with connected vehicles); Selecting vehicle enables command form; Command name dropdown shows options: ReadDTC, ClearDTC, ReadDataByID; Selecting \"ReadDTC\" shows ecuAddress input field; Form validates required fields (shows error if empty); Submitting valid command calls `POST /api/v1/commands` with correct payload; On success, displays success message with command_id; On validation error from backend (400), displays error message; Component tests verify: form rendering, validation, submission, error handling; No console errors; No linter errors",
  "dependencies": ["I2.T3", "I3.T4", "I3.T5"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents.

### Context: Command Submission Requirements

The task requires implementing a command submission interface with:
- Vehicle selection (connected vehicles only)
- Command type selection (ReadDTC, ClearDTC, ReadDataByID)
- Dynamic parameter fields based on command type
- Form validation with react-hook-form
- API integration with POST /api/v1/commands

### Context: SOVD Command Validation Rules

From sovd_command_schema.json:

**ReadDTC Command:**
- Required: ecuAddress (format: `^0x[0-9A-Fa-f]{2}$`)
- Example: `{"ecuAddress": "0x10"}`

**ClearDTC Command:**
- Required: ecuAddress (format: `^0x[0-9A-Fa-f]{2}$`)
- Optional: dtcCode (format: `^P[0-9A-F]{4}$`)
- Example: `{"ecuAddress": "0x10", "dtcCode": "P0420"}`

**ReadDataByID Command:**
- Required: ecuAddress (format: `^0x[0-9A-Fa-f]{2}$`)
- Required: dataId (format: `^0x[0-9A-Fa-f]{4}$`)
- Example: `{"ecuAddress": "0x10", "dataId": "0x1234"}`

### Context: API Contract

**POST /api/v1/commands** (from openapi.yaml line 268)

Request Body:
```json
{
  "vehicle_id": "uuid",
  "command_name": "ReadDTC",
  "command_params": {
    "ecuAddress": "0x10"
  }
}
```

Response (201 Created):
```json
{
  "command_id": "uuid",
  "user_id": "uuid",
  "vehicle_id": "uuid",
  "command_name": "ReadDTC",
  "command_params": {"ecuAddress": "0x10"},
  "status": "pending",
  "error_message": null,
  "submitted_at": "2025-10-28T10:00:00Z",
  "completed_at": null
}
```

---

## 3. Codebase Analysis & Strategic Guidance

### Relevant Existing Code

*   **File:** `frontend/src/api/client.ts` (line 166-227)
    *   **Summary:** Axios API client with JWT authentication, token refresh, and existing API method exports (`authAPI`, `vehicleAPI`).
    *   **Recommendation:** You MUST extend this file by adding a `commandAPI` object following the exact same pattern as `vehicleAPI`. Use the existing `apiClient` instance and export the new API object.
    *   **Example Pattern:**
        ```typescript
        export const commandAPI = {
          submitCommand: async (request: CommandSubmitRequest): Promise<CommandResponse> => {
            const response = await apiClient.post<CommandResponse>('/api/v1/commands', request);
            return response.data;
          },
        };
        ```

*   **File:** `frontend/src/types/vehicle.ts`
    *   **Summary:** TypeScript interfaces that match backend Pydantic schemas. Includes `VehicleResponse` with all vehicle fields.
    *   **Recommendation:** Create `frontend/src/types/command.ts` using this file as a TEMPLATE. Your command types MUST exactly match the backend schemas in `backend/app/schemas/command.py` (lines 12-48).

*   **File:** `frontend/src/pages/VehiclesPage.tsx` (line 24-109)
    *   **Summary:** Complete page implementation using React Query, useState for filters, MUI Grid layout, and child components.
    *   **Recommendation:** Use this as your TEMPLATE for `CommandPage.tsx`. Note the structure:
        - React Query for data fetching
        - useState for form state
        - MUI Container, Grid, and Paper components
        - Props passed to child components

*   **File:** `frontend/src/components/vehicles/VehicleList.tsx` (line 51-141)
    *   **Summary:** Well-structured presentational component with loading/error/empty states using MUI Table.
    *   **Recommendation:** Follow this PATTERN for your components:
        - Clear TypeScript interface for props
        - Separate handling of loading, error, and empty states
        - Consistent MUI component usage
        - Proper TypeScript typing throughout

*   **File:** `frontend/src/pages/CommandsPage.tsx` (line 10-27)
    *   **Summary:** Current PLACEHOLDER with minimal content - just a Paper component with placeholder text.
    *   **Recommendation:** You will REPLACE this file entirely with your CommandPage implementation. Discard all current content.

*   **File:** `frontend/src/App.tsx` (line 56-62)
    *   **Summary:** React Router configuration with `/commands` route already set up with ProtectedRoute wrapper.
    *   **Recommendation:** You do NOT need to modify this file. Your new CommandPage will automatically be used.

*   **File:** `backend/app/schemas/command.py` (lines 12-48)
    *   **Summary:** Pydantic schemas defining CommandSubmitRequest and CommandResponse with exact field types.
    *   **Recommendation:** Your TypeScript types MUST match these schemas exactly. Pay attention to UUID serialization (serialized as strings in JSON).

### Implementation Tips & Notes

*   **CRITICAL - Missing Dependency:** React Hook Form is NOT in package.json. You MUST install it first:
    ```bash
    cd frontend && npm install react-hook-form @hookform/resolvers
    ```

*   **Tip - Vehicle Filtering:** VehicleSelector must filter to connected vehicles. Use: `vehicles.filter(v => v.connection_status === 'connected')`. See VehiclesPage line 43-53 for filtering pattern.

*   **Tip - Dynamic Form Fields:** Implement conditional rendering based on selected command_name:
    - ReadDTC → show ecuAddress field only
    - ClearDTC → show ecuAddress (required) + dtcCode (optional)
    - ReadDataByID → show ecuAddress + dataId fields
    Use React Hook Form's `watch()` to monitor command_name changes.

*   **Tip - Validation Patterns:** Use these regex patterns in react-hook-form validation:
    - ecuAddress: `/^0x[0-9A-Fa-f]{2}$/`
    - dtcCode: `/^P[0-9A-F]{4}$/`
    - dataId: `/^0x[0-9A-Fa-f]{4}$/`

*   **Tip - Success Handling:** Since ResponseViewer (I3.T7) is not implemented yet, display success message on same page using MUI Alert or Snackbar. Show the returned `command_id`.

*   **Warning - HTTP Status:** API returns 201 (Created), not 200. Axios will still resolve the promise normally.

*   **Note - Directory Structure:** Create `frontend/src/components/commands/` directory for CommandForm. Place VehicleSelector in existing `frontend/src/components/vehicles/` directory.

*   **Note - Test Location:** Tests go in `frontend/tests/components/`, not `frontend/src/tests/`.

*   **Note - Existing Utils:** The file `frontend/src/utils/dateUtils.ts` exists with `formatRelativeTime()` function. You may need it if displaying timestamps.

### Key Files You Will Create/Modify

1. **CREATE** `frontend/src/types/command.ts` - CommandSubmitRequest, CommandResponse interfaces
2. **UPDATE** `frontend/src/api/client.ts` - Add commandAPI object with submitCommand()
3. **CREATE** `frontend/src/components/vehicles/VehicleSelector.tsx` - Connected vehicles dropdown
4. **CREATE** `frontend/src/components/commands/CommandForm.tsx` - Form with dynamic fields and validation
5. **REPLACE** `frontend/src/pages/CommandPage.tsx` - Main page combining components
6. **CREATE** `frontend/tests/components/CommandForm.test.tsx` - Test suite

### Recommended Implementation Order

1. Install dependencies: `cd frontend && npm install react-hook-form @hookform/resolvers`
2. Create `frontend/src/types/command.ts` (match backend schemas exactly)
3. Update `frontend/src/api/client.ts` (add commandAPI)
4. Create `frontend/src/components/vehicles/VehicleSelector.tsx` (simpler component first)
5. Create `frontend/src/components/commands/CommandForm.tsx` (complex dynamic form)
6. Replace `frontend/src/pages/CommandPage.tsx` (integrate components)
7. Create `frontend/tests/components/CommandForm.test.tsx` (comprehensive tests)
8. Manual testing in browser (verify all acceptance criteria)

### Acceptance Criteria Checklist

- [ ] Vehicle selector shows only connected vehicles
- [ ] Command form disabled until vehicle selected
- [ ] Command dropdown has ReadDTC, ClearDTC, ReadDataByID options
- [ ] Dynamic fields appear based on command selection
- [ ] Form validation catches empty/invalid fields
- [ ] POST /api/v1/commands called with correct payload
- [ ] Success message displays command_id
- [ ] API error (400) displays error message
- [ ] Component tests pass
- [ ] No console errors
- [ ] No linter errors

Good luck! Follow the established patterns and the implementation will be straightforward.
