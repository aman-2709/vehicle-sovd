# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T8",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Implement common UI components and application layout. Create: 1) Header component `src/components/common/Header.tsx` with app title, user profile menu (displays username, logout button), navigation links (Dashboard, Vehicles, Commands, History), 2) Sidebar component `src/components/common/Sidebar.tsx` for navigation (alternative to header nav, can use MUI Drawer), 3) Main layout component `src/components/common/Layout.tsx` that wraps pages with header/sidebar and content area, 4) Error boundary `src/components/common/ErrorBoundary.tsx` to catch React errors and display fallback UI, 5) Loading spinner component `src/components/common/LoadingSpinner.tsx`, 6) Empty state component `src/components/common/EmptyState.tsx` (icon + message), 7) Implement logout functionality in header (call `/api/v1/auth/logout`, clear tokens, redirect to login). Update all page components to use Layout wrapper. Write component tests for header (logout functionality) and error boundary.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Standard web app UX patterns; MUI component library documentation.",
  "target_files": [
    "frontend/src/components/common/Header.tsx",
    "frontend/src/components/common/Sidebar.tsx",
    "frontend/src/components/common/Layout.tsx",
    "frontend/src/components/common/ErrorBoundary.tsx",
    "frontend/src/components/common/LoadingSpinner.tsx",
    "frontend/src/components/common/EmptyState.tsx",
    "frontend/tests/components/Header.test.tsx",
    "frontend/tests/components/ErrorBoundary.test.tsx"
  ],
  "input_files": [
    "frontend/src/context/AuthContext.tsx",
    "frontend/src/styles/theme.ts"
  ],
  "deliverables": "Complete common component library; application layout with header/sidebar; error boundary; logout functionality; component tests.",
  "acceptance_criteria": "All pages wrapped in Layout component (Header visible on all pages); Header displays username from auth context; Clicking logout button calls `/api/v1/auth/logout`, clears tokens, redirects to login; Navigation links in header/sidebar navigate correctly (Dashboard, Vehicles, Commands); Error boundary catches component errors and displays fallback UI (test by throwing error in child component); Loading spinner used in vehicle and command pages (consistent styling); Empty state component used when no data available (consistent messaging); Component tests verify: logout flow, navigation, error boundary behavior; UI consistent with MUI theme; No console errors; No linter errors",
  "dependencies": [
    "I3.T4",
    "I2.T1"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Technology Stack (from README.md)

```markdown
## Technology Stack

### Frontend
- **Framework:** React 18 with TypeScript
- **UI Library:** Material-UI (MUI)
- **State Management:** React Query
- **Build Tool:** Vite
- **Code Quality:** ESLint, Prettier, TypeScript

### Backend
- **Framework:** Python 3.11+ with FastAPI
- **Server:** Uvicorn (ASGI)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose, passlib)
- **Code Quality:** Ruff, Black, mypy

### Infrastructure
- **Database:** PostgreSQL 15+
- **Cache/Messaging:** Redis 7
- **Vehicle Communication:** gRPC (primary), WebSocket (fallback)
- **API Gateway:** Nginx (production)
- **Containerization:** Docker, Docker Compose (local), Kubernetes/Helm (production)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana, structlog
- **Tracing:** OpenTelemetry + Jaeger

### Testing
- **Backend:** pytest, pytest-asyncio, httpx
- **Frontend:** Vitest, React Testing Library
- **E2E:** Playwright
```

### Context: Authentication API Endpoints (from docs/api/README.md)

```markdown
### Authentication Endpoints

All API endpoints (except `/health` and `/`) require JWT authentication.

- `POST /api/v1/auth/login` - Authenticate and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Invalidate refresh tokens
- `GET /api/v1/auth/me` - Get current user profile

## Authentication

The API uses **JWT Bearer token authentication**:

1. **Login**: Send credentials to `POST /api/v1/auth/login`
   ```json
   {
     "username": "engineer1",
     "password": "your_password"
   }
   ```

2. **Receive tokens**:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "expires_in": 900
   }
   ```

3. **Use access token**: Include in all requests:
   ```
   Authorization: Bearer eyJhbGc...
   ```

4. **Token expiration**:
   - Access tokens expire in 15 minutes
   - Refresh tokens expire in 7 days
   - Use `POST /api/v1/auth/refresh` to get a new access token

## Logout

Call `POST /api/v1/auth/logout` to invalidate the current refresh token. This ensures the user cannot use the refresh token to obtain new access tokens.
```

### Context: Project Goals (from README.md)

```markdown
## Goals

- User authentication and role-based access control (Engineer, Admin roles)
- Vehicle registry with connection status monitoring
- SOVD command submission with parameter validation
- Real-time response streaming via WebSocket
- Command history and audit logging
- <2 second round-trip time for 95% of commands
- Support for 100+ concurrent users
- Secure communication (TLS, JWT, RBAC)
- Docker-based deployment ready for cloud platforms (AWS/GCP/Azure)
- 80%+ test coverage with CI/CD pipeline
- OpenAPI/Swagger documentation for all backend APIs
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/src/context/AuthContext.tsx`
    *   **Summary:** This file implements the authentication context provider that manages JWT tokens and authentication state. It stores the access token in memory and refresh token in localStorage.
    *   **Recommendation:** You MUST import and use the `useAuth()` hook from this file in your Header component to:
        - Access the current user profile (`user` object with `username` and `role`)
        - Access the `isAuthenticated` boolean state
        - Call the `logout()` function when the logout button is clicked
    *   **Key Methods:**
        - `login()`: Authenticates user and stores tokens
        - `logout()`: Calls `/api/v1/auth/logout` API, clears tokens from memory and localStorage, resets state
        - `user`: Contains `{ user_id, username, role }` from the profile
        - `isAuthenticated`: Boolean indicating if user is logged in

*   **File:** `frontend/src/styles/theme.ts`
    *   **Summary:** This file exports the MUI theme configuration with an automotive-inspired color scheme. It defines primary colors (blue), secondary colors (dark gray), and component style overrides.
    *   **Recommendation:** You MUST use this theme in your components. All new components should follow the established color scheme:
        - Primary color: `#1976d2` (deep blue)
        - Secondary color: `#424242` (dark gray)
        - Success: `#2e7d32` (green)
        - Error: `#d32f2f` (red)
        - Warning: `#ed6c02` (orange)
        - Background: `#f5f5f5` (light gray)
    *   **Typography:** Buttons use `textTransform: 'none'` (no uppercase), font weights are 500 for headings
    *   **Border Radius:** Default is 4px for all components

*   **File:** `frontend/src/App.tsx`
    *   **Summary:** This is the main application component with React Router route definitions. It currently renders routes directly without a layout wrapper.
    *   **Recommendation:** You MUST update this file to wrap all protected routes with your new `Layout` component. The current structure has routes for:
        - `/` - Redirects to dashboard or login based on auth state
        - `/login` - Public login page (should NOT have layout)
        - `/dashboard`, `/vehicles`, `/commands`, `/history` - Protected routes (SHOULD be wrapped in Layout)
    *   **Pattern to Follow:** Wrap the `<ProtectedRoute>` children with your `<Layout>` component like this:
        ```tsx
        <ProtectedRoute>
          <Layout>
            <DashboardPage />
          </Layout>
        </ProtectedRoute>
        ```

*   **File:** `frontend/src/pages/VehiclesPage.tsx`
    *   **Summary:** Example of a current page implementation. It has its own container and header, which will be replaced by the Layout component.
    *   **Recommendation:** After you implement the Layout component, you SHOULD remove the redundant `<Box sx={{ minHeight: '100vh', bgcolor: 'background.default', py: 4 }}>` wrapper from all pages. The Layout component will provide this.
    *   **Current Pattern:** Pages currently have their own page-level Box with padding and background color. Your Layout component should provide this so pages can just render their content.

*   **File:** `frontend/src/pages/DashboardPage.tsx`
    *   **Summary:** The dashboard page currently implements its own logout button and navigation. This demonstrates the logout pattern you need to implement in the Header.
    *   **Recommendation:** You SHOULD follow the same logout pattern from this file:
        ```tsx
        const { logout } = useAuth();
        const navigate = useNavigate();

        const handleLogout = () => {
          void (async () => {
            await logout();
            navigate('/login', { replace: true });
          })();
        };
        ```
    *   **Note:** After implementing the Header with logout, you can remove the standalone logout button from DashboardPage since it will be in the header.

*   **File:** `frontend/src/api/client.ts`
    *   **Summary:** This file exports the API client with axios configured for JWT authentication and token refresh. It exports specialized API objects like `authAPI`, `vehicleAPI`, `commandAPI`.
    *   **Recommendation:** The `authAPI.logout()` function is already implemented and available. You MUST use this in your Header logout handler. The function signature is:
        ```tsx
        authAPI.logout(): Promise<LogoutResponse>
        ```
    *   **Important:** The AuthContext's `logout()` method already calls `authAPI.logout()` internally, so you just need to call `logout()` from the auth context.

### Implementation Tips & Notes

*   **Tip - MUI Drawer for Sidebar:** I recommend using MUI's `Drawer` component for the sidebar. Since this is a desktop-focused application, you can use a permanent drawer that's always visible. Example structure:
    ```tsx
    import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText } from '@mui/material';
    ```
    Consider making it 240px wide (MUI standard) with a light background.

*   **Tip - Header Structure:** The Header should use MUI's `AppBar` component with `Toolbar`. Position it at the top with `position="sticky"` or `position="fixed"`. Include:
    1. App title on the left
    2. Navigation links in the center (using MUI `Tabs` or `Button` components)
    3. User profile menu on the right (using MUI `Menu` component with `IconButton` trigger)

*   **Tip - Navigation Links:** Use React Router's `useNavigate()` hook for navigation. The routes you need to link to are:
    - Dashboard: `/dashboard`
    - Vehicles: `/vehicles`
    - Commands: `/commands`
    - History: `/history`
    Use React Router's `useLocation()` hook to highlight the active link.

*   **Tip - Error Boundary Implementation:** React Error Boundaries must be class components (not functional components). Use the following pattern:
    ```tsx
    class ErrorBoundary extends React.Component<Props, State> {
      static getDerivedStateFromError(error: Error) { ... }
      componentDidCatch(error: Error, errorInfo: ErrorInfo) { ... }
      render() { ... }
    }
    ```
    Display a fallback UI with a "Reload Page" button when an error is caught.

*   **Tip - LoadingSpinner Component:** Create a simple reusable spinner using MUI's `CircularProgress`. Accept optional `size` and `message` props. Center it in the container with flexbox. This will be used in pages during data fetching.

*   **Tip - EmptyState Component:** Create a component that displays an icon (from `@mui/icons-material`), a title, and an optional message. Use MUI's `Box` and `Typography`. Accept props for `icon`, `title`, `message`. This will be used when lists are empty.

*   **Warning - Layout Component:** The Layout component should accept `children` as a prop and render the page content in a main content area. DO NOT hardcode specific pages in the Layout. Use this pattern:
    ```tsx
    const Layout: React.FC<{ children: ReactNode }> = ({ children }) => {
      return (
        <Box sx={{ display: 'flex' }}>
          <Sidebar />
          <Box sx={{ flexGrow: 1 }}>
            <Header />
            <Box component="main" sx={{ p: 3 }}>
              {children}
            </Box>
          </Box>
        </Box>
      );
    };
    ```

*   **Warning - Testing with Vitest:** When writing component tests, you MUST mock the `useAuth` hook since it depends on AuthContext. Example:
    ```tsx
    import { vi } from 'vitest';
    import * as AuthContext from '../context/AuthContext';

    vi.spyOn(AuthContext, 'useAuth').mockReturnValue({
      isAuthenticated: true,
      user: { user_id: '1', username: 'testuser', role: 'engineer' },
      logout: vi.fn(),
      // ... other required properties
    });
    ```

*   **Warning - React Router in Tests:** You MUST wrap components that use React Router hooks (`useNavigate`, `useLocation`) in a `MemoryRouter` when testing:
    ```tsx
    import { MemoryRouter } from 'react-router-dom';

    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Header />
      </MemoryRouter>
    );
    ```

*   **Note - Responsive Design:** While the primary focus is desktop, ensure the layout is reasonably responsive. Consider using MUI's responsive drawer (temporary drawer on mobile) if time permits, but a simple permanent drawer is acceptable for the MVP.

*   **Note - Accessibility:** Use semantic HTML elements (`<nav>`, `<header>`, `<main>`) and ensure all interactive elements have proper ARIA labels. MUI components generally handle this well, but add labels to IconButtons:
    ```tsx
    <IconButton aria-label="User menu" onClick={handleMenuOpen}>
      <AccountCircle />
    </IconButton>
    ```

*   **Note - Code Organization:** The `frontend/src/components/common/` directory currently exists but is empty. This is the correct location for all your new common components. Maintain consistent file naming (PascalCase for component files).

### Project File Structure Reference

```
frontend/src/
├── api/
│   ├── client.ts          (API client with JWT auth - USE authAPI from here)
│   └── websocket.ts       (WebSocket client)
├── components/
│   ├── auth/
│   │   └── ProtectedRoute.tsx
│   ├── commands/
│   │   ├── CommandForm.tsx
│   │   └── ResponseViewer.tsx
│   ├── vehicles/
│   │   ├── VehicleList.tsx
│   │   └── VehicleSelector.tsx
│   └── common/            (YOUR NEW COMPONENTS GO HERE)
│       ├── Header.tsx     (TO CREATE)
│       ├── Sidebar.tsx    (TO CREATE)
│       ├── Layout.tsx     (TO CREATE)
│       ├── ErrorBoundary.tsx (TO CREATE)
│       ├── LoadingSpinner.tsx (TO CREATE)
│       └── EmptyState.tsx (TO CREATE)
├── context/
│   └── AuthContext.tsx    (USE useAuth() hook from here)
├── pages/
│   ├── LoginPage.tsx      (DO NOT wrap with Layout)
│   ├── DashboardPage.tsx  (WRAP with Layout - see handleLogout pattern)
│   ├── VehiclesPage.tsx   (WRAP with Layout - remove page-level wrapper)
│   ├── CommandPage.tsx    (WRAP with Layout)
│   └── HistoryPage.tsx    (WRAP with Layout)
├── styles/
│   └── theme.ts           (USE this MUI theme)
├── types/
│   ├── auth.ts            (UserProfile type is here)
│   ├── command.ts
│   ├── response.ts
│   └── vehicle.ts
├── App.tsx                (UPDATE to use Layout wrapper)
└── main.tsx               (Entry point with theme provider)
```

### Testing Strategy

1. **Header Component Tests** (`frontend/tests/components/Header.test.tsx`):
   - Test that username is displayed from auth context
   - Test logout button click calls `logout()` and navigates to `/login`
   - Test navigation links render and navigate correctly
   - Test user menu opens and closes
   - Mock `useAuth` and `useNavigate` hooks

2. **ErrorBoundary Component Tests** (`frontend/tests/components/ErrorBoundary.test.tsx`):
   - Test that normal children render without errors
   - Test that fallback UI displays when child throws error
   - Test that error is logged to console
   - Create a test component that throws an error on render
   - Test reload button functionality (should call `window.location.reload()`)

3. **Integration Testing:**
   - After wrapping pages with Layout, ensure all pages still render correctly
   - Test navigation flow between pages
   - Test that logout from any page redirects to login

### Acceptance Criteria Checklist

Use this checklist to verify your implementation meets all requirements:

- [ ] Header component created with app title
- [ ] Header displays username from `useAuth().user.username`
- [ ] Header has user profile menu with logout button
- [ ] Header has navigation links (Dashboard, Vehicles, Commands, History)
- [ ] Navigation links use React Router and highlight active route
- [ ] Logout button calls `POST /api/v1/auth/logout` via authContext.logout()
- [ ] Logout clears tokens and redirects to `/login`
- [ ] Sidebar component created with navigation (can be simpler version of header nav)
- [ ] Layout component created that wraps Header + Sidebar + children
- [ ] All protected routes in App.tsx wrapped with Layout
- [ ] Login page NOT wrapped with Layout (remains standalone)
- [ ] ErrorBoundary component catches React errors and displays fallback UI
- [ ] LoadingSpinner component created and styled consistently
- [ ] EmptyState component created with icon + message
- [ ] Component tests written for Header (logout, navigation)
- [ ] Component tests written for ErrorBoundary (error catching, fallback)
- [ ] All tests pass (`npm run test` or `vitest`)
- [ ] No linter errors (`npm run lint`)
- [ ] No console errors in browser when running app
- [ ] UI consistent with MUI theme from `theme.ts`
- [ ] Layout is responsive (at minimum, works on desktop)

---

**END OF TASK BRIEFING PACKAGE**

You now have all the context, guidance, and references needed to complete Task I3.T8. Please implement the common UI components and layout as specified, following the patterns and recommendations above.
