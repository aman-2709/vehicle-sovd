# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SOVD Command WebApp: Cloud-based service for remotely executing SOVD 2.0 (Service-Oriented Vehicle Diagnostics) commands on connected vehicles. React/TypeScript frontend with FastAPI backend, PostgreSQL database, Redis for caching/pub-sub, and real-time WebSocket communication.

## Essential Commands

### Development Environment
```bash
# Start all services (frontend, backend, database, redis, prometheus, grafana)
make up

# Initialize database (required on first run)
POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh

# View logs
make logs                          # All services
docker-compose logs -f backend     # Specific service
docker-compose logs -f frontend

# Stop all services
make down
```

### Testing
```bash
# Backend tests (from backend/ directory)
pytest                                    # All tests
pytest tests/unit/test_auth_service.py    # Single test file
pytest -k test_login_success              # Single test by name
pytest --cov=app --cov-report=html        # With coverage

# Frontend tests (from frontend/ directory)
npm run test                              # Interactive watch mode
npm run test:coverage                     # With coverage
npm run test -- LoginPage.test.tsx        # Single test file

# End-to-end tests (orchestrates full stack automatically)
make e2e
```

### Code Quality
```bash
# Backend (from backend/ directory)
ruff check app/                   # Lint
black app/                        # Format
mypy app/                         # Type check

# Frontend (from frontend/ directory)
npm run lint                      # ESLint
npm run format                    # Prettier
```

### Database Operations
```bash
# Access PostgreSQL
docker-compose exec db psql -U sovd_user -d sovd

# Run migrations (from backend/ directory)
alembic upgrade head              # Apply migrations
alembic downgrade -1              # Rollback one migration
alembic revision -m "description" # Create new migration
```

## Architecture Patterns

### Backend Layered Architecture

The backend follows a strict **API → Services → Repositories** layered pattern:

**API Layer** (`app/api/v1/`): FastAPI route handlers
- Validates requests using Pydantic schemas
- Handles HTTP concerns (status codes, headers)
- Delegates business logic to services
- Example: `auth.py`, `commands.py`, `vehicles.py`, `websocket.py`

**Service Layer** (`app/services/`): Business logic orchestration
- Coordinates multiple repositories
- Implements business rules and workflows
- Handles transactions and error scenarios
- Example: `command_service.py` coordinates command execution, WebSocket broadcasting, and audit logging
- Example: `auth_service.py` handles JWT creation, password hashing, and token validation

**Repository Layer** (`app/repositories/`): Database access abstraction
- Single responsibility: CRUD operations for one model
- Uses async SQLAlchemy with proper transaction handling
- All queries use `select()` statements (SQLAlchemy 2.0 style)
- Example: `command_repository.py`, `vehicle_repository.py`

**Key Pattern**: Always inject `AsyncSession` via FastAPI's `Depends(get_db)` at the API layer, then pass to services/repositories. Never create database sessions inside services or repositories.

### Authentication & Authorization Flow

**Token Strategy** (dual-token JWT):
- **Access Token**: Short-lived (15 min), stored in memory on frontend
- **Refresh Token**: Long-lived (7 days), stored in localStorage
- Backend validates access tokens on every API request via `get_current_user` dependency

**Token Refresh Flow**:
1. Frontend detects 401 response → calls `/api/v1/auth/refresh` with refresh token
2. Backend validates refresh token → issues new access token
3. Frontend retries original request with new token
4. Implemented in `frontend/src/api/client.ts` axios interceptors

**Security Notes**:
- Access tokens never persisted (XSS protection)
- Refresh tokens in localStorage (secure but accessible)
- All API routes except `/auth/login` and `/auth/refresh` require authentication
- RBAC implemented via `role` field in JWT claims (engineer, admin)

### Real-Time Communication Architecture

**WebSocket Connection Pattern**:
- Client connects to `/ws/{command_id}` with JWT token
- Backend registers connection in `WebSocketManager` (singleton)
- Command responses broadcast via Redis pub/sub to all connected clients
- Connection lifecycle managed per command (not global)

**Broadcast Flow**:
1. Vehicle sends command response → Backend receives via gRPC/WebSocket
2. Backend stores response in database → publishes event to Redis channel
3. Redis subscriber (`app/api/v1/websocket.py`) receives event
4. `WebSocketManager.broadcast()` sends to all WebSocket clients for that command_id
5. Frontend receives real-time update → displays in UI

**Key Files**:
- `backend/app/services/websocket_manager.py`: Connection registry and broadcast logic
- `backend/app/api/v1/websocket.py`: WebSocket endpoint and Redis subscriber
- `frontend/src/api/websocket.ts`: Client-side WebSocket connection manager

### Database Session Management

**Async SQLAlchemy Pattern**:
```python
# API Layer: Inject session
@router.get("/vehicles")
async def get_vehicles(db: AsyncSession = Depends(get_db)):
    return await vehicle_service.get_all(db)

# Service Layer: Accept session, pass to repositories
async def get_all(db: AsyncSession) -> list[Vehicle]:
    return await vehicle_repository.get_all(db)

# Repository Layer: Execute queries
async def get_all(db: AsyncSession) -> list[Vehicle]:
    result = await db.execute(select(Vehicle))
    return result.scalars().all()
```

**Transaction Handling**:
- Use `async with db.begin()` for explicit transactions in services
- Repositories should NOT commit/rollback (handled by service layer)
- `get_db()` dependency auto-commits on success, auto-rollbacks on exception

**Migration Strategy**:
- All schema changes via Alembic migrations (never manual SQL)
- Models defined in `app/models/` using SQLAlchemy 2.0 Declarative
- Alembic env configured for async engine (`alembic/env.py`)

### Middleware Execution Order

Middleware executes in **LIFO** (Last-In-First-Out) order:

**Registration Order** (in `app/main.py`):
1. `SecurityHeadersMiddleware` (last registered = outermost layer)
2. `SlowAPIMiddleware` (rate limiting)
3. `LoggingMiddleware` (correlation IDs, structured logs)
4. `CORSMiddleware` (cross-origin requests)

**Execution Order** (request → response):
1. **SecurityHeadersMiddleware**: Adds security headers (CSP, X-Frame-Options, etc.)
2. **SlowAPIMiddleware**: Checks rate limits, returns 429 if exceeded
3. **LoggingMiddleware**: Generates correlation ID, logs request/response
4. **CORSMiddleware**: Handles CORS preflight and headers
5. **Route Handler**: Actual endpoint logic

**Error Handling**: Global exception handlers in `app/main.py` convert all exceptions to standardized JSON responses with error codes (`app/utils/error_codes.py`).

### Frontend State Management

**Authentication State** (`AuthContext`):
- Centralized auth state (access token in memory, refresh token in localStorage)
- Provides `isAuthenticated`, `user`, `login()`, `logout()`, `refreshToken()`
- Used via `useAuth()` hook throughout the application
- Implements token refresh logic on mount

**Data Fetching** (React Query):
- All API calls use React Query hooks (`useQuery`, `useMutation`)
- Automatic caching, background refetch, and error handling
- Query keys pattern: `['entity', id]` or `['entity', 'list', filters]`
- Example: `useVehicles()` in `frontend/src/hooks/useVehicles.ts`

**WebSocket State** (`useWebSocket` hook):
- Manages WebSocket connection lifecycle per command
- Auto-reconnect on disconnect
- Returns `{messages, isConnected, error}` state
- Example: `frontend/src/hooks/useWebSocket.ts`

### Testing Structure

**Backend Tests**:
- **Unit Tests** (`backend/tests/unit/`): Test services and repositories in isolation
  - Use mocked dependencies (repositories mock database, services mock repositories)
  - Focus on business logic validation

- **Integration Tests** (`backend/tests/integration/`): Test API endpoints with real database
  - Use `TestClient` from FastAPI
  - Database state reset between tests via fixtures
  - Test full request/response cycle including middleware

**Frontend Tests**:
- **Component Tests**: Vitest + React Testing Library
  - Mock API calls using `axios-mock-adapter`
  - Mock `useAuth()` context for protected components
  - Test user interactions and state changes

**E2E Tests** (`tests/e2e/`):
- Playwright tests running against full Docker stack
- Cover critical user flows: authentication, vehicle management, command execution
- Run via `make e2e` (handles service orchestration automatically)

### Key Architectural Decisions

**Async-First Backend**:
- All I/O operations use `async/await` (database, Redis, HTTP, WebSocket)
- FastAPI with uvicorn ASGI server
- Benefits: Handle 100+ concurrent users with minimal resource usage

**Separation of Concerns**:
- Frontend never directly accesses database or Redis
- All vehicle communication proxied through backend
- Backend acts as secure gateway with authentication, rate limiting, and audit logging

**Real-Time Updates**:
- WebSocket for real-time command responses (low latency)
- Redis pub/sub for broadcast to multiple clients
- Fallback: Polling via HTTP if WebSocket unavailable

**Observability**:
- Structured JSON logging with correlation IDs (trace requests across services)
- Prometheus metrics exposed at `/metrics` endpoint
- Grafana dashboards for operations, commands, and vehicles (pre-configured)
- OpenTelemetry ready (tracing integration points exist)

## Security Considerations

**OWASP Top 10 Mitigations**:
- **Injection**: All database queries use parameterized statements (SQLAlchemy ORM)
- **Authentication**: JWT with short-lived access tokens, refresh token rotation
- **XSS**: React auto-escapes output, CSP headers enforced
- **CSRF**: Token-based auth (no cookies), CORS whitelist
- **Rate Limiting**: slowapi middleware (10 req/min for login, 100 req/min for API)
- **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options, HSTS

**Code Review Checklist**:
- Never commit secrets (use `.env.example` as template)
- Validate all user input using Pydantic schemas
- Use `Depends(get_current_user)` for protected endpoints
- Hash passwords with bcrypt (never store plaintext)
- Sanitize error messages (no sensitive data in responses)
