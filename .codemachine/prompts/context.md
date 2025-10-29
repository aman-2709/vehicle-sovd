# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T5",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Create Vehicles page `src/pages/VehiclesPage.tsx` displaying list of vehicles fetched from `GET /api/v1/vehicles` API. Implement: 1) Vehicle list component `src/components/vehicles/VehicleList.tsx` using MUI Table or Card layout, 2) Display vehicle fields: VIN, make, model, year, connection status (with color indicator: green=connected, gray=disconnected, red=error), last_seen_at (formatted as relative time, e.g., \"2 minutes ago\"), 3) React Query integration for data fetching, caching, and auto-refresh (refetch every 30 seconds), 4) Loading state (skeleton or spinner), 5) Error state (error message display), 6) Empty state (when no vehicles), 7) Search input to filter vehicles by VIN (client-side filtering initially), 8) Status filter dropdown (All, Connected, Disconnected). Create vehicle types `src/types/vehicle.ts` matching backend schemas. Write component tests in `frontend/tests/components/VehicleList.test.tsx`.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "OpenAPI spec from I2.T9 (vehicle endpoints); Architecture Blueprint Section 3.7 (API Endpoints - Vehicles).",
  "target_files": [
    "frontend/src/pages/VehiclesPage.tsx",
    "frontend/src/components/vehicles/VehicleList.tsx",
    "frontend/src/types/vehicle.ts",
    "frontend/src/api/client.ts",
    "frontend/tests/components/VehicleList.test.tsx"
  ],
  "input_files": [
    "docs/api/openapi.yaml",
    "frontend/src/api/client.ts"
  ],
  "deliverables": "Functional vehicle list page with API integration; React Query caching; filtering and search; loading/error states; component tests.",
  "acceptance_criteria": "Vehicles page displays all vehicles from backend (verify with seed data: 2 vehicles); Vehicle connection status shown with color coding; Last seen timestamp formatted as relative time; Search input filters vehicles by VIN (partial match, case-insensitive); Status filter dropdown filters by connection status; React Query caches data (verify with network tab: first load fetches, second load uses cache); Auto-refresh every 30 seconds (verify with network tab); Loading spinner shown during initial fetch; Error message displayed if API fails (test by stopping backend); Empty state shown if no vehicles match filters; Component tests verify: rendering vehicle list, search functionality, status filtering; No console errors; No linter errors",
  "dependencies": [
    "I2.T2",
    "I3.T4"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Vehicle API Endpoints (from OpenAPI Specification)

```markdown
## GET /api/v1/vehicles

**Summary:** List Vehicles

**Description:** Get list of vehicles with optional filtering and pagination.

Query parameters:
- `status`: Filter by connection status (connected, disconnected, error)
- `search`: Search by VIN (partial match, case-insensitive)
- `limit`: Maximum number of results (1-100, default: 50)
- `offset`: Number of results to skip (default: 0)

Requires authentication via JWT bearer token.

**Returns:**
List of vehicle objects with details (vehicle_id, vin, make, model, year, connection_status, last_seen_at, metadata)

**Raises:**
- 401 Unauthorized: If JWT token is missing or invalid
- 422 Unprocessable Entity: If query parameters are invalid

**Example Response Structure:**
The endpoint returns a direct array of VehicleResponse objects:
```
[
  {
    "vehicle_id": "123e4567-e89b-12d3-a456-426614174000",
    "vin": "1HGCM82633A123456",
    "make": "Honda",
    "model": "Accord",
    "year": 2024,
    "connection_status": "connected",
    "last_seen_at": "2025-10-28T10:00:00Z",
    "metadata": null
  }
]
```

## GET /api/v1/vehicles/{vehicle_id}

**Summary:** Get Vehicle

**Description:** Get a single vehicle by ID.

Path parameters:
- `vehicle_id`: UUID of the vehicle to retrieve

**Returns:**
Vehicle object with full details

**Raises:**
- 401 Unauthorized: If JWT token is missing or invalid
- 404 Not Found: If vehicle with given ID does not exist

## GET /api/v1/vehicles/{vehicle_id}/status

**Summary:** Get Vehicle Status

**Description:** Get vehicle connection status (cached in Redis for 30 seconds).

This endpoint is optimized for frequent polling by frontend dashboards.
Vehicle status is cached in Redis with a 30-second TTL to reduce database load.

**Returns:**
Vehicle status object with connection_status, last_seen_at, and health metrics

**Note:**
Second request within 30 seconds will return cached data (faster response).
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/src/api/client.ts`
    *   **Summary:** This file contains the API client configuration using Axios with automatic JWT token injection, token refresh logic on 401 responses, and authentication endpoints (authAPI object with login, refresh, logout, getProfile methods).
    *   **Recommendation:** You MUST extend this file to add vehicle-related API methods. Follow the existing pattern used for `authAPI` to create a `vehicleAPI` object with methods for `getVehicles()`, `getVehicle(id)`, and `getVehicleStatus(id)`. Export these methods so they can be imported in your React components.
    *   **Implementation Pattern:**
        ```typescript
        export const vehicleAPI = {
          getVehicles: async (params?: { status?: string; search?: string; limit?: number; offset?: number }) => {
            const response = await apiClient.get('/api/v1/vehicles', { params });
            return response.data; // Returns VehicleResponse[]
          },
          getVehicle: async (vehicleId: string) => {
            const response = await apiClient.get(`/api/v1/vehicles/${vehicleId}`);
            return response.data; // Returns VehicleResponse
          },
          getVehicleStatus: async (vehicleId: string) => {
            const response = await apiClient.get(`/api/v1/vehicles/${vehicleId}/status`);
            return response.data; // Returns VehicleStatusResponse
          },
        };
        ```

*   **File:** `frontend/src/context/AuthContext.tsx`
    *   **Summary:** This file provides authentication context with `useAuth` hook that exposes `isAuthenticated`, `user`, `login`, `logout`, and token management.
    *   **Recommendation:** You can use the `useAuth()` hook in your VehiclesPage to access the current user if needed for display or logging purposes. The JWT token is already automatically injected into all API calls via the API client interceptor, so you don't need to manually handle authentication in your vehicle components.

*   **File:** `frontend/src/types/auth.ts`
    *   **Summary:** This file contains TypeScript interfaces for authentication-related types matching backend Pydantic schemas (LoginRequest, TokenResponse, RefreshRequest, RefreshResponse, UserProfile, LogoutResponse).
    *   **Recommendation:** You MUST create a similar file `frontend/src/types/vehicle.ts` with TypeScript interfaces matching the backend vehicle schemas. Based on the OpenAPI spec and backend schemas, you should define:
        - `VehicleResponse` interface matching `backend/app/schemas/vehicle.py::VehicleResponse`
        - `VehicleStatusResponse` interface matching the status endpoint response
        - `VehicleListResponse` interface if needed for future pagination
    *   **Key Fields:** The `VehicleResponse` should include: `vehicle_id` (string), `vin` (string), `make` (string), `model` (string), `year` (number), `connection_status` (string), `last_seen_at` (string | null), `metadata` (object | null)

*   **File:** `backend/app/schemas/vehicle.py`
    *   **Summary:** This file defines the Pydantic schemas for vehicle responses with fields like `vehicle_id`, `vin`, `make`, `model`, `year`, `connection_status`, `last_seen_at`, and `metadata`.
    *   **Recommendation:** Your TypeScript types in `frontend/src/types/vehicle.ts` MUST match these Pydantic schemas exactly. Note that `vehicle_id` is a UUID that gets serialized to string, `last_seen_at` is a datetime (ISO 8601 string in JSON), and `metadata` is optional JSONB (object or null).
    *   **Critical Detail:** The backend uses `vehicle_metadata` as the field name in the model, but it's aliased to `metadata` in the response via `Field(alias="vehicle_metadata")`. Your TypeScript interface should use `metadata` as the field name to match the JSON response.

*   **File:** `backend/app/api/v1/vehicles.py`
    *   **Summary:** This file implements the vehicle API endpoints with filtering, pagination, and Redis caching for status endpoint. The `list_vehicles` endpoint returns `list[VehicleResponse]` directly, NOT a wrapped object.
    *   **Recommendation:** The backend endpoint returns a list of `VehicleResponse` objects directly (not wrapped in a pagination object with `vehicles`, `total`, etc.). You should handle the response accordingly in your frontend. Your API call should expect an array of vehicle objects.
    *   **Critical Note:** Line 105 of vehicles.py shows: `return [VehicleResponse.model_validate(v) for v in vehicles]` - this confirms the response is a direct array, not a wrapped object.

*   **File:** `frontend/src/pages/LoginPage.tsx`
    *   **Summary:** This file demonstrates the pattern for form handling, error states, loading states, and MUI components (Container, Paper, Box, TextField, Button, Alert, CircularProgress).
    *   **Recommendation:** You SHOULD follow the same patterns for loading states (`CircularProgress`), error display (`Alert`), and layouts using MUI components like `Paper`, `Container`, `Box`, `TextField`, and `Button`.

*   **File:** `frontend/src/App.tsx`
    *   **Summary:** This file sets up React Router with protected routes using the `ProtectedRoute` component. The `/vehicles` route already exists and points to `VehiclesPage`.
    *   **Recommendation:** The `/vehicles` route already exists and points to `VehiclesPage`. You are replacing the placeholder implementation with the full implementation. No changes needed to this file.

*   **File:** `frontend/src/main.tsx`
    *   **Summary:** This file is the entry point that wraps the app with `ThemeProvider`, `AuthProvider`, and `BrowserRouter`.
    *   **Recommendation:** You MUST add the React Query `QueryClientProvider` to this file to enable React Query throughout the application. Import `QueryClient` and `QueryClientProvider` from `@tanstack/react-query`, create a `QueryClient` instance, and wrap the `<App />` component with the provider.
    *   **Implementation:**
        ```typescript
        import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

        const queryClient = new QueryClient({
          defaultOptions: {
            queries: {
              refetchOnWindowFocus: false,
              retry: 1,
              staleTime: 30000, // 30 seconds
            },
          },
        });

        // In the render:
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </QueryClientProvider>
        ```

*   **File:** `frontend/src/pages/VehiclesPage.tsx`
    *   **Summary:** This is currently a placeholder component that displays a simple message.
    *   **Recommendation:** You MUST replace this entire file with the full implementation including the VehicleList component, search input, status filter, and integration with React Query.

### Implementation Tips & Notes

*   **Tip:** React Query is already installed (`@tanstack/react-query@^5.8.0` in package.json). You should use `useQuery` hook for fetching vehicles with automatic caching and refetching.

*   **Tip:** For relative time formatting (e.g., "2 minutes ago"), you can use a simple utility function or consider using a library like `date-fns` (not installed yet). Since the task requires "2 minutes ago" format and it's a common need, I recommend creating a simple utility function in `frontend/src/utils/dateUtils.ts`:
    ```typescript
    export const formatRelativeTime = (dateString: string | null): string => {
      if (!dateString) return 'Never';
      const date = new Date(dateString);
      const now = new Date();
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

      if (diffInSeconds < 60) return 'Just now';
      if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
      if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
      return `${Math.floor(diffInSeconds / 86400)} days ago`;
    };
    ```

*   **Tip:** For connection status color coding:
    - `connected` → green (use MUI theme color `success.main`)
    - `disconnected` → gray (use `text.secondary`)
    - `error` → red (use `error.main`)

    You can use MUI's `Chip` component with `color` prop or a `Box` with styled background color.

*   **Tip:** The backend currently returns a direct array of vehicles, not a wrapped object. Your API call should handle this:
    ```typescript
    const { data: vehicles, isLoading, error } = useQuery({
      queryKey: ['vehicles'],
      queryFn: () => vehicleAPI.getVehicles(),
      refetchInterval: 30000, // Auto-refresh every 30 seconds
    });
    ```

*   **Note:** For client-side filtering by VIN and status, you'll need to:
    1. Fetch all vehicles initially
    2. Use React state to manage search and status filter values
    3. Use `useMemo` to compute the filtered list based on the state
    4. Display the filtered list in the component

    Example:
    ```typescript
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('All');

    const filteredVehicles = useMemo(() => {
      if (!vehicles) return [];
      return vehicles.filter(v => {
        const matchesSearch = searchTerm === '' ||
          v.vin.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesStatus = statusFilter === 'All' ||
          v.connection_status === statusFilter.toLowerCase();
        return matchesSearch && matchesStatus;
      });
    }, [vehicles, searchTerm, statusFilter]);
    ```

*   **Warning:** The task specifies client-side filtering initially, but the backend actually supports server-side filtering via query parameters (`status` and `search`). For this task, implement client-side filtering as specified. However, document this decision and note that server-side filtering could be added as an optimization in a future iteration.

*   **Testing Note:** For component tests with React Query, you'll need to wrap your component in a `QueryClientProvider` with a test query client. Example:
    ```typescript
    import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

    const createTestQueryClient = () => new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    const renderWithClient = (ui: React.ReactElement) => {
      const testQueryClient = createTestQueryClient();
      return render(
        <QueryClientProvider client={testQueryClient}>
          {ui}
        </QueryClientProvider>
      );
    };
    ```

*   **Important:** The task requires MUI Table or Card layout. I recommend using MUI `TableContainer`, `Table`, `TableHead`, `TableBody`, `TableRow`, `TableCell` components for a clean tabular view. This will be easier to implement filtering and sorting in the future.

    Example structure:
    ```typescript
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>VIN</TableCell>
            <TableCell>Make</TableCell>
            <TableCell>Model</TableCell>
            <TableCell>Year</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Last Seen</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {filteredVehicles.map(vehicle => (
            <TableRow key={vehicle.vehicle_id}>
              {/* ... table cells ... */}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
    ```

*   **Project Convention:** Based on existing code, use:
    - Functional components with TypeScript (`React.FC`)
    - Arrow functions for component definitions
    - `async/await` for async operations wrapped in `void (async () => { ... })()`
    - MUI `sx` prop for styling instead of styled-components
    - JSDoc comments at the top of each file explaining its purpose

*   **Note:** For the empty state (when no vehicles match filters), use MUI components to display a user-friendly message. Example:
    ```typescript
    {filteredVehicles.length === 0 && (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="h6" color="text.secondary">
          No vehicles found
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {searchTerm || statusFilter !== 'All'
            ? 'Try adjusting your filters'
            : 'No vehicles available'}
        </Typography>
      </Box>
    )}
    ```

*   **Tip:** For the loading state, use MUI's `CircularProgress` centered in a Box:
    ```typescript
    {isLoading && (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    )}
    ```

*   **Tip:** For error state, use MUI's `Alert` component:
    ```typescript
    {error && (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load vehicles. Please try again.
      </Alert>
    )}
    ```

### Acceptance Criteria Verification Checklist

To meet all acceptance criteria, ensure:

1. **Data Display:** Vehicles page displays all vehicles from backend (2 seed vehicles visible)
2. **Status Indicator:** Connection status shown with color coding (green/gray/red)
3. **Time Formatting:** Last seen timestamp formatted as relative time ("X minutes ago")
4. **Search:** Search input filters vehicles by VIN (partial match, case-insensitive)
5. **Status Filter:** Dropdown filters by connection status (All, Connected, Disconnected)
6. **Caching:** React Query caches data (verify network tab shows cache behavior)
7. **Auto-refresh:** Data refetches every 30 seconds automatically
8. **Loading State:** Loading spinner shown during initial fetch
9. **Error State:** Error message displayed if API fails
10. **Empty State:** Empty state shown when no vehicles match filters
11. **Tests:** Component tests verify rendering, search, and filtering
12. **Quality:** No console errors, no linter errors

### File Structure Summary

Expected file organization:
```
frontend/src/
├── api/
│   └── client.ts (MODIFY: add vehicleAPI methods)
├── components/
│   └── vehicles/
│       └── VehicleList.tsx (CREATE: new component)
├── pages/
│   └── VehiclesPage.tsx (MODIFY: replace placeholder)
├── types/
│   └── vehicle.ts (CREATE: new types)
├── utils/
│   └── dateUtils.ts (CREATE: helper for relative time)
└── main.tsx (MODIFY: add QueryClientProvider)

frontend/tests/
└── components/
    └── VehicleList.test.tsx (CREATE: new test)
```

**CRITICAL:** Remember to update `frontend/src/main.tsx` to add the React Query `QueryClientProvider` wrapping before implementing the VehiclesPage, otherwise your `useQuery` hooks will fail with an error about missing QueryClient context.

### Backend API Response Format (Critical!)

Based on the actual backend implementation in `backend/app/api/v1/vehicles.py:105`:

```python
return [VehicleResponse.model_validate(v) for v in vehicles]
```

The `/api/v1/vehicles` endpoint returns a **direct array** of vehicle objects:

```typescript
// Correct response type:
VehicleResponse[]

// NOT:
{ vehicles: VehicleResponse[], total: number, ... }
```

Your TypeScript code MUST handle this correctly. The `vehicleAPI.getVehicles()` method should return `Promise<VehicleResponse[]>`, not a wrapped object.

### Color Coding Reference

For vehicle connection status indicators, use these MUI theme colors:

| Status | Color | MUI Theme Reference | Hex |
|--------|-------|---------------------|-----|
| connected | Green | `success.main` | #2e7d32 |
| disconnected | Gray | `text.secondary` | rgba(0,0,0,0.6) |
| error | Red | `error.main` | #d32f2f |

Implement this with MUI Chip:
```typescript
<Chip
  label={vehicle.connection_status}
  color={
    vehicle.connection_status === 'connected' ? 'success' :
    vehicle.connection_status === 'error' ? 'error' :
    'default'
  }
  size="small"
/>
```
