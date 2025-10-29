# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T4",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Create React application foundation in `frontend/src/`. Implement: 1) Main entry point `main.tsx` with React Router setup, 2) Root component `App.tsx` with route definitions (Login, Dashboard, Vehicles, Commands, History), 3) Authentication context `src/context/AuthContext.tsx` for managing JWT tokens (access token in memory, refresh token in localStorage), 4) Login page `src/pages/LoginPage.tsx` with form (username, password fields, submit button), 5) API client `src/api/client.ts` using axios with base URL from environment variable, automatic JWT injection via interceptor, token refresh logic on 401 response. Implement login flow: submit credentials to `POST /api/v1/auth/login`, store tokens in context, redirect to dashboard. Implement protected route wrapper `src/components/auth/ProtectedRoute.tsx` that redirects to login if not authenticated. Create MUI theme in `src/styles/theme.ts` with automotive-inspired color scheme. Write component tests using Vitest and React Testing Library in `frontend/tests/components/`.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Architecture Blueprint Section 3.3 (Container Diagram - Web App); Technology Stack (React 18, TypeScript, MUI).",
  "target_files": [
    "frontend/src/main.tsx",
    "frontend/src/App.tsx",
    "frontend/src/context/AuthContext.tsx",
    "frontend/src/pages/LoginPage.tsx",
    "frontend/src/api/client.ts",
    "frontend/src/components/auth/ProtectedRoute.tsx",
    "frontend/src/styles/theme.ts",
    "frontend/tests/components/LoginPage.test.tsx"
  ],
  "input_files": [
    "docs/api/openapi.yaml"
  ],
  "deliverables": "Functional React application with login page; JWT authentication context; API client with token management; protected routes; MUI theme; component tests.",
  "acceptance_criteria": "`npm run dev` starts frontend at `http://localhost:3000`; Login page renders with username and password fields; Submitting valid credentials (from seed data: admin/admin123) calls `/api/v1/auth/login` and stores tokens; After login, user redirected to Dashboard page (can be placeholder for now); Protected routes redirect to login if not authenticated; API client injects `Authorization: Bearer {token}` header on all requests; On 401 response, API client attempts token refresh automatically; MUI theme applied globally (verify by checking component styling); Component tests verify: login form submission, error handling, token storage; No console errors in browser; No linter errors (`npm run lint`)",
  "dependencies": [
    "I2.T1",
    "I2.T9"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Technology Stack (from 02_Architecture_Overview.md)

```markdown
<!-- anchor: technology-stack -->
### 3.2. Technology Stack Summary

<!-- anchor: stack-overview -->
#### Technology Selection Matrix

| **Layer/Concern** | **Technology** | **Justification** |
|-------------------|----------------|-------------------|
| **Frontend Framework** | React 18 + TypeScript | Industry-standard component model; TypeScript provides type safety; extensive ecosystem; strong community support; meets requirement. |
| **Frontend State Management** | React Context + React Query | React Query for server state (caching, sync); Context for auth/global UI state; avoids Redux complexity for this scale. |
| **Frontend Build** | Vite | Fast dev server and build times; superior to CRA; excellent TypeScript support; optimized production bundles. |
| **Frontend UI Library** | Material-UI (MUI) | Comprehensive component library; automotive industry precedent; accessibility built-in; professional appearance. |
| **Authentication** | JWT (JSON Web Tokens) | Stateless; scalable; industry standard; supported by FastAPI middleware. |
| **Auth Library** | python-jose + passlib | JWT encoding/decoding; secure password hashing (bcrypt); widely adopted. |
| **API Style** | REST (OpenAPI 3.1)| Requirements explicitly request OpenAPI/Swagger docs; RESTful design well-understood; mature tooling. |
```

**Key Technology Decisions**

**FastAPI over Node.js/Express:**
- Superior async/await model for handling concurrent vehicle connections
- Automatic OpenAPI generation saves development time
- Native WebSocket support crucial for streaming responses
- Type hints improve maintainability and align with TypeScript frontend philosophy
- Performance benchmarks show FastAPI competitive with Node.js for I/O-bound operations
```

### Context: Container Diagram - Web Application (from 03_System_Structure_and_Data.md)

```markdown
<!-- anchor: container-diagram -->
### 3.4. Container Diagram (C4 Level 2)

<!-- anchor: container-diagram-description -->
#### Description

This diagram zooms into the SOVD Command WebApp system boundary and shows the major deployable containers (applications and data stores). Key containers include:

- **Web Application (SPA)**: React-based frontend served as static files
- **API Gateway**: Nginx reverse proxy for routing, TLS termination, and load balancing
- **Application Server**: FastAPI-based backend with modular services
- **WebSocket Server**: Handles real-time streaming responses (embedded in FastAPI)
- **Vehicle Connector Service**: Abstraction layer for vehicle communication protocols
- **PostgreSQL Database**: Primary data store for vehicles, commands, responses, and audit logs
- **Redis Cache**: Session storage and response caching for performance

**Container Diagram:**
```
Container(web_app, "Web Application", "React 18, TypeScript, MUI", "Provides UI for authentication, vehicle selection, command execution, and response viewing")
```

Relationships:
- Engineer → web_app (Uses, HTTPS)
- web_app → api_gateway (Makes API calls, HTTPS, JSON)
- web_app → ws_server (Opens WebSocket for streaming, WSS)
```

### Context: Authentication API Specification (from docs/api/openapi.yaml)

```yaml
/api/v1/auth/login:
  post:
    tags:
      - auth
    summary: Login
    description: "Authenticate user and return access and refresh tokens."
    operationId: login_api_v1_auth_login_post
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LoginRequest'
          example:
            username: engineer1
            password: securePassword123
      required: true
    responses:
      '200':
        description: Successful Response
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TokenResponse'

components:
  schemas:
    LoginRequest:
      properties:
        username:
          type: string
          minLength: 1
          maxLength: 100
        password:
          type: string
          minLength: 1
      required:
        - username
        - password

    TokenResponse:
      properties:
        access_token:
          type: string
          description: "JWT access token"
        refresh_token:
          type: string
          description: "JWT refresh token"
        token_type:
          type: string
          default: "bearer"
        expires_in:
          type: integer
          description: "Access token expiration time in seconds"
```

### Context: Authentication Endpoints (from backend implementation)

The backend authentication service has been implemented with the following endpoints:

1. **POST /api/v1/auth/login**
   - Accepts: `{ username: string, password: string }`
   - Returns: `{ access_token, refresh_token, token_type, expires_in }`
   - On success: Creates session in database and returns tokens
   - On failure: Returns 401 Unauthorized

2. **POST /api/v1/auth/refresh**
   - Accepts: `{ refresh_token: string }`
   - Returns: `{ access_token, token_type, expires_in }`
   - Validates refresh token against database and issues new access token

3. **POST /api/v1/auth/logout**
   - Requires: Bearer token in Authorization header
   - Returns: `{ message: "Logged out successfully" }`
   - Deletes all sessions for the user

4. **GET /api/v1/auth/me**
   - Requires: Bearer token in Authorization header
   - Returns: `{ user_id, username, role, email }`

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/package.json`
    *   **Summary:** This file contains all the necessary dependencies for the task. The project is already configured with React 18.2.0, TypeScript, MUI 5.14.0, React Router 6.20.0, axios 1.6.0, @tanstack/react-query 5.8.0, and Vite. All testing dependencies are in place: vitest, @testing-library/react, @testing-library/jest-dom.
    *   **Recommendation:** You DO NOT need to install any additional dependencies. All required packages are already present. Simply use them directly in your implementation.

*   **File:** `frontend/tsconfig.json`
    *   **Summary:** TypeScript is configured with strict mode enabled (`"strict": true`), with additional strict linting rules (`noUnusedLocals`, `noUnusedParameters`, `noFallthroughCasesInSwitch`). The JSX mode is set to `react-jsx` (modern JSX transform).
    *   **Recommendation:** Your TypeScript code MUST adhere to strict type checking. Ensure all variables are typed, avoid `any` types, and handle all potential null/undefined cases.

*   **File:** `frontend/vite.config.ts`
    *   **Summary:** Vite is configured to run on host `0.0.0.0` port 3000 with HMR. The React plugin is already configured.
    *   **Recommendation:** The dev server will be accessible at http://localhost:3000. No additional Vite configuration is needed for this task.

*   **File:** `frontend/.eslintrc.json` and `frontend/.prettierrc`
    *   **Summary:** ESLint and Prettier are already configured in the project.
    *   **Recommendation:** Run `npm run lint` to check for linting errors and `npm run format` to format your code before completing the task.

*   **File:** `frontend/src/main.tsx`
    *   **Summary:** This is a minimal placeholder that renders the App component into the root element using React 18's `createRoot` API. It includes `React.StrictMode`.
    *   **Recommendation:** You MUST update this file to wrap the App component with React Router's `BrowserRouter`. You should also integrate the AuthContext provider here so it's available throughout the application.

*   **File:** `frontend/src/App.tsx`
    *   **Summary:** This is a minimal placeholder component that displays a status message.
    *   **Recommendation:** You MUST replace this entirely with route definitions using React Router. Define routes for `/login`, `/dashboard`, `/vehicles`, `/commands`, and `/history`. The root path `/` should redirect to either `/login` or `/dashboard` based on authentication status.

*   **File:** `backend/app/api/v1/auth.py`
    *   **Summary:** The authentication API is fully implemented with login, refresh, logout, and profile endpoints. The login endpoint returns `TokenResponse` with `access_token`, `refresh_token`, `token_type`, and `expires_in`.
    *   **Recommendation:** Your API client MUST call `POST /api/v1/auth/login` with Content-Type `application/json` and a body containing `{ username, password }`. The backend expects these exact field names.

*   **File:** `backend/app/schemas/auth.py`
    *   **Summary:** The Pydantic schemas define the exact structure of authentication requests and responses. `LoginRequest` has `username` and `password` fields. `TokenResponse` has `access_token`, `refresh_token`, `token_type`, and `expires_in` fields.
    *   **Recommendation:** Your TypeScript types MUST match these schemas exactly. Create interfaces that mirror the Pydantic models.

*   **File:** `frontend/index.html`
    *   **Summary:** The HTML template includes a root div with id="root" and loads the main.tsx script.
    *   **Recommendation:** No changes needed to this file. The root element is already in place for React mounting.

### Implementation Tips & Notes

*   **Tip:** The backend runs on port 8000 (based on docker-compose.yml configuration). Your axios baseURL should be `http://localhost:8000` for development. Consider using Vite's `import.meta.env` to make this configurable (e.g., `import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'`).

*   **Note:** The task specifies storing the access token in memory and refresh token in localStorage. This is a security best practice. Implement the AuthContext with a state variable for the access token (in-memory) and use `localStorage.setItem('refresh_token', token)` for the refresh token.

*   **Warning:** The axios interceptor for 401 responses MUST implement retry logic carefully to avoid infinite loops. When a 401 is received, attempt to refresh the token ONCE using the refresh token from localStorage. If the refresh succeeds, retry the original request with the new access token. If the refresh fails, clear all tokens and redirect to login.

*   **Tip:** For the MUI theme, create an "automotive-inspired" color scheme. Consider using dark blues, grays, and metallic colors. MUI's `createTheme` function accepts a palette object where you can customize primary, secondary, and error colors. Example:
    ```typescript
    const theme = createTheme({
      palette: {
        primary: { main: '#1976d2' }, // Blue
        secondary: { main: '#424242' }, // Dark gray
      }
    });
    ```

*   **Note:** The ProtectedRoute component should use React Router's Navigate component for redirection. Check the authentication state from AuthContext, and if not authenticated, render `<Navigate to="/login" replace />`.

*   **Tip:** For testing, the seed data includes two users: `admin/admin123` and `engineer/engineer123`. Your component tests should use these credentials when mocking successful login scenarios.

*   **Warning:** The task requires component tests but does NOT require E2E tests at this stage. Focus on unit tests for the LoginPage component using React Testing Library. Mock the axios calls and AuthContext for isolated component testing.

*   **Note:** The directory structure shows that `frontend/src/components/auth/`, `frontend/src/components/common/`, `frontend/src/pages/`, `frontend/src/api/`, and `frontend/src/styles/` directories already exist but are empty. You SHOULD create files in these existing directories rather than creating new directories.

*   **Tip:** For the Dashboard placeholder, you can create a simple component that displays "Dashboard" and a logout button. The full dashboard implementation will come in later tasks. The key is to demonstrate that authenticated users can access it and unauthenticated users are redirected.

*   **Important:** The axios interceptor MUST add the Authorization header for ALL requests (except login/refresh). Use `config.headers.Authorization = Bearer ${token}` in the request interceptor. Exclude the /auth/login and /auth/refresh endpoints from this header injection.

*   **Note:** When implementing the token refresh logic, you need to handle the case where multiple concurrent requests receive 401 errors. Implement a promise-based queue so that only ONE refresh request is made, and all other pending requests wait for it to complete. This prevents multiple simultaneous refresh calls.

*   **Tip:** For Vitest configuration, create a `vitest.config.ts` file or add vitest configuration to the existing `vite.config.ts`. You'll need to set up the test environment to 'jsdom' and configure global test utilities. Example:
    ```typescript
    export default defineConfig({
      test: {
        environment: 'jsdom',
        setupFiles: ['./tests/setup.ts'],
        globals: true,
      },
    });
    ```

*   **Warning:** The task acceptance criteria requires "No console errors in browser". Ensure your code doesn't have any console.error calls during normal operation. Console warnings are acceptable during development but should be minimized.

---

## 4. Task Execution Checklist

Use this checklist to ensure you complete all requirements:

### Phase 1: Project Setup
- [ ] Create `.env.local` or use Vite's `import.meta.env` for API base URL configuration
- [ ] Set up Vitest configuration for component testing
- [ ] Create test setup file with React Testing Library configuration

### Phase 2: Core Authentication Infrastructure
- [ ] Implement `frontend/src/api/client.ts` with axios instance, base URL, request/response interceptors
- [ ] Implement token refresh logic in interceptor with proper error handling
- [ ] Create TypeScript interfaces matching backend schemas (LoginRequest, TokenResponse, etc.)

### Phase 3: Authentication Context
- [ ] Implement `frontend/src/context/AuthContext.tsx` with state for access token (memory) and methods to manage tokens
- [ ] Implement `login` function that calls `/api/v1/auth/login` and stores tokens
- [ ] Implement `logout` function that clears tokens and calls `/api/v1/auth/logout`
- [ ] Implement `refreshToken` function for token refresh flow
- [ ] Create custom hook `useAuth` for consuming the context

### Phase 4: Routing and Protected Routes
- [ ] Update `frontend/src/main.tsx` to include BrowserRouter and AuthContext provider
- [ ] Update `frontend/src/App.tsx` with route definitions for all pages
- [ ] Implement `frontend/src/components/auth/ProtectedRoute.tsx` wrapper component
- [ ] Set up root path `/` to redirect based on auth status

### Phase 5: Login Page
- [ ] Implement `frontend/src/pages/LoginPage.tsx` with MUI form components
- [ ] Add form validation (required fields)
- [ ] Implement form submission handler that calls AuthContext.login
- [ ] Add error display for authentication failures
- [ ] Add loading state during login attempt
- [ ] Implement redirect to dashboard on successful login

### Phase 6: Placeholder Pages
- [ ] Create `frontend/src/pages/DashboardPage.tsx` (simple placeholder)
- [ ] Create empty placeholders for VehiclesPage, CommandsPage, HistoryPage (or just Dashboard for now)

### Phase 7: MUI Theme
- [ ] Implement `frontend/src/styles/theme.ts` with automotive-inspired color scheme
- [ ] Wrap App with ThemeProvider in main.tsx

### Phase 8: Testing
- [ ] Write component test for LoginPage (form rendering, submission, error handling)
- [ ] Test token storage in AuthContext
- [ ] Test protected route redirection
- [ ] Ensure all tests pass with `npm run test`
- [ ] Verify linting passes with `npm run lint`

### Phase 9: Validation
- [ ] Verify `npm run dev` starts successfully on port 3000
- [ ] Manually test login flow with admin/admin123 credentials
- [ ] Verify JWT token in Authorization header using browser DevTools Network tab
- [ ] Test automatic token refresh on 401 response
- [ ] Test logout functionality
- [ ] Test protected route redirection when not logged in
- [ ] Check browser console for errors (should be none)

---

## 5. Critical Success Factors

1. **Authentication Flow**: The login → token storage → protected route → auto-refresh flow MUST work seamlessly. This is the foundation for all future frontend features.

2. **Type Safety**: All TypeScript types must match backend schemas exactly. Use strict typing throughout.

3. **Token Security**: Access token in memory (React state), refresh token in localStorage. Never store access tokens in localStorage (security vulnerability).

4. **Error Handling**: Gracefully handle network errors, authentication failures, and token expiration. Display user-friendly error messages.

5. **Axios Interceptor**: The interceptor logic for token injection and refresh is complex. Test it thoroughly to avoid infinite loops or duplicate requests.

6. **Testing**: Component tests must be comprehensive. Test both success and failure scenarios for login.

7. **MUI Integration**: Ensure MUI theme is applied globally and components use MUI styling consistently.

8. **No Console Errors**: The acceptance criteria explicitly requires no console errors. Debug and fix any errors before completing.
