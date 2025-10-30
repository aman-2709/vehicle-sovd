# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T4",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Implement health check endpoints: GET /health/live (liveness), GET /health/ready (readiness with db/redis checks). Add health service to check dependencies. Configure docker-compose healthcheck. Write integration tests.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Health Checks); Kubernetes best practices.",
  "target_files": [
    "backend/app/api/health.py",
    "backend/app/services/health_service.py",
    "backend/app/main.py",
    "docker-compose.yml",
    "backend/tests/integration/test_health.py"
  ],
  "input_files": [
    "backend/app/database.py"
  ],
  "deliverables": "Liveness/readiness health check endpoints; health service; docker-compose healthchecks; tests.",
  "acceptance_criteria": "/health/live returns 200; /health/ready returns 200 when healthy, 503 when dependencies fail; Docker healthcheck uses /health/ready; Tests verify both endpoints; Coverage ≥80%; No errors",
  "dependencies": [
    "I1.T10"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Kubernetes Health Check Best Practices

According to Kubernetes best practices, health checks should be implemented with two distinct endpoints:

1. **Liveness Probe (`/health/live`)**: Indicates if the application is running. If this check fails, Kubernetes will restart the container. This should be a simple check that doesn't verify external dependencies.

2. **Readiness Probe (`/health/ready`)**: Indicates if the application is ready to serve traffic. If this check fails, Kubernetes will stop routing traffic to the pod. This should verify external dependencies like database and Redis connections.

**Key Principles:**
- Liveness checks should be lightweight and fast (< 1 second)
- Liveness should NOT check external dependencies (to avoid cascading failures)
- Readiness checks can be more thorough and check external dependencies
- Health endpoints should return appropriate HTTP status codes (200 for healthy, 503 for unhealthy)
- Health endpoints should include meaningful response bodies with status details

### Context: Docker Compose Health Checks

Docker Compose healthchecks follow this format:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 30s
```

The `start_period` gives the application time to initialize before health checks start failing.

### Context: FastAPI Health Check Implementation Pattern

FastAPI health checks are typically implemented as simple GET endpoints that:
1. Return JSON responses with status information
2. Set appropriate HTTP status codes (200, 503)
3. Are lightweight and fast
4. Can optionally check external service connectivity

Example structure:
```python
@app.get("/health/live")
async def liveness():
    return {"status": "ok"}

@app.get("/health/ready")
async def readiness():
    # Check database, Redis, etc.
    if not all_services_healthy:
        raise HTTPException(status_code=503, detail="Service unavailable")
    return {"status": "ready", "checks": {...}}
```

### Context: Existing Project Monitoring Infrastructure

The project already has:
- Prometheus metrics at `/metrics` endpoint
- Structured logging with structlog
- Redis connection pattern in `websocket.py` and `vehicle_service.py`
- SQLAlchemy async database connection in `database.py`
- Docker Compose with 6 services (db, redis, backend, frontend, prometheus, grafana)

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/main.py`
    *   **Summary:** This is the FastAPI application entry point. It configures middleware, CORS, registers API routers, and exposes Prometheus metrics. Currently has a basic `/health` endpoint that only returns a status message without checking dependencies.
    *   **Recommendation:** You MUST import and register the new health router from `backend/app/api/health.py` in this file. Add it to the router registration section (around line 47-50) with appropriate prefix and tags.
    *   **Current Health Endpoint:** There is already a basic `/health` endpoint at line 57-69. You should KEEP this for backward compatibility and add your new `/health/live` and `/health/ready` endpoints via the health router.

*   **File:** `backend/app/database.py`
    *   **Summary:** This file provides the core database connection infrastructure with SQLAlchemy async engine and session management. It exports a `get_db()` async generator for dependency injection and uses connection pooling (pool_size=20, max_overflow=10).
    *   **Recommendation:** For the health check service, you MUST import the `engine` object from this file to execute raw SQL health check queries. Use `engine.connect()` or execute a simple `SELECT 1` query to verify database connectivity.
    *   **Connection Pattern:** The async engine is already configured at module level (line 36-42). Your health check can reuse this engine directly.

*   **File:** `backend/app/config.py`
    *   **Summary:** This file manages application configuration using pydantic-settings. It loads `DATABASE_URL` and `REDIS_URL` from environment variables or `.env` file.
    *   **Recommendation:** You MUST import `settings` from this file to get the `REDIS_URL` for creating a Redis client in your health service.
    *   **Configuration Access:** Use `settings.DATABASE_URL` and `settings.REDIS_URL` to access connection strings.

*   **File:** `backend/app/services/vehicle_service.py`
    *   **Summary:** This file demonstrates the project's pattern for creating a module-level Redis client using `redis.asyncio as aioredis` (line 23-27). It shows how to connect to Redis with async support.
    *   **Recommendation:** You SHOULD follow this exact pattern in your health service to create a Redis client for health checks. Import `redis.asyncio as aioredis` and use `aioredis.from_url(settings.REDIS_URL, ...)` to create the client.
    *   **Redis Client Pattern:** Use `redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)` at module level.

*   **File:** `backend/tests/conftest.py`
    *   **Summary:** This is the pytest configuration file that provides fixtures for testing. It creates test database sessions using SQLite for tests, overrides the `get_db` dependency, and mocks audit service for integration tests.
    *   **Recommendation:** Your integration tests for health endpoints should use the `async_client` fixture from this file (line 82-113). This fixture provides an authenticated HTTP client for testing FastAPI endpoints.
    *   **Testing Pattern:** Use `@pytest.mark.asyncio` decorator and `async_client` fixture. Example: `async def test_liveness(self, async_client: AsyncClient)`.

*   **File:** `backend/tests/integration/test_auth_api.py`
    *   **Summary:** This file demonstrates the project's integration testing patterns. Tests are organized into classes by endpoint, use descriptive test names (line 20-80), and verify both success and error cases.
    *   **Recommendation:** You SHOULD follow this exact structure for your health endpoint tests. Create classes like `TestLivenessEndpoint` and `TestReadinessEndpoint`, with test methods that verify status codes and response formats.
    *   **Test Organization:** Group related tests in classes, test both success (200) and failure (503) cases, and verify response JSON structure.

*   **File:** `docker-compose.yml`
    *   **Summary:** This file orchestrates all services for local development. The database (lines 11-32) and Redis (lines 36-53) services already have healthchecks defined. The backend service (lines 57-88) does NOT currently have a healthcheck.
    *   **Recommendation:** You MUST add a healthcheck configuration to the `backend` service section. Use the `/health/ready` endpoint you create, with appropriate intervals and retries. Follow the pattern used for db and redis services.
    *   **Healthcheck Format:** Add between lines 88-89 (after `depends_on` and before `networks`). Use `test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]` with reasonable timing parameters.

### Implementation Tips & Notes

*   **Tip:** The project uses `structlog` for logging (imported in multiple service files). You SHOULD add structured logging to your health service to log health check results. Import with `import structlog` and get logger with `logger = structlog.get_logger(__name__)`.

*   **Note:** For the database health check in your service, execute a simple query like `SELECT 1` to verify connectivity. Use `await engine.connect()` with proper exception handling. If the connection or query fails, return unhealthy status.

*   **Note:** For the Redis health check, use the `ping()` method on the Redis client: `await redis_client.ping()`. Wrap this in a try/except block to catch connection failures gracefully.

*   **Warning:** The liveness endpoint (`/health/live`) should NEVER check external dependencies (database or Redis). It should only verify that the application process is running. Return a simple `{"status": "ok"}` response immediately.

*   **Tip:** The readiness endpoint (`/health/ready`) should check BOTH database and Redis. Structure your response to include individual check results, like:
    ```json
    {
        "status": "ready",
        "checks": {
            "database": "ok",
            "redis": "ok"
        }
    }
    ```

*   **Note:** When a dependency check fails in the readiness endpoint, use FastAPI's `HTTPException` with status code 503 to return Service Unavailable. Example: `raise HTTPException(status_code=503, detail={"status": "unavailable", "checks": {...}})`

*   **Tip:** The project already has `redis>=5.0.0` in requirements.txt (line 14), so you have the Redis async client available. Import it as `import redis.asyncio as aioredis` to match the project's convention seen in other service files.

*   **Note:** For integration tests, you may need to mock the database and Redis connections since tests use SQLite and might not have a real Redis instance. Use `unittest.mock.patch` to mock the health check functions and test both healthy and unhealthy scenarios.

*   **Warning:** The Docker healthcheck command requires `curl` to be available in the container. The backend Dockerfile should already have this, but verify that curl is installed. If not, you'll need to add it to the Dockerfile or use Python's httpx/requests for the healthcheck.

*   **Tip:** Follow the project's async patterns consistently. All service functions should be `async def` and use `await` for I/O operations (database queries, Redis commands). This matches the pattern seen in `vehicle_service.py` and other service files.

*   **Best Practice:** For production readiness, your health endpoints should respond quickly (< 1 second for liveness, < 3 seconds for readiness). If checks take longer, consider implementing timeouts on the database and Redis operations.

*   **Convention:** Based on the existing codebase structure, create your health API router in `backend/app/api/health.py` (NOT under `/api/v1/` since health endpoints are typically root-level). Import it in `main.py` as `from app.api import health` and register with `app.include_router(health.router, tags=["health"])`.

*   **SQLAlchemy Pattern:** When checking database health, use the async engine's `connect()` method within an async context manager:
    ```python
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    ```
    You'll need to import `from sqlalchemy import text` to execute raw SQL.

*   **Error Handling:** Wrap all health check operations in try/except blocks to gracefully handle failures. Log failures with structured logging including error details. Never let exceptions propagate unhandled from health endpoints.

*   **Testing Consideration:** Since the integration tests use SQLite (not PostgreSQL) and may not have Redis, you should mock the `check_database_health()` and `check_redis_health()` functions in your tests. Use `@patch('app.services.health_service.check_database_health')` to mock these dependencies.

---

## Summary

You are implementing Kubernetes-style health check endpoints for production readiness. Create two endpoints: `/health/live` (simple liveness) and `/health/ready` (checks database and Redis). Build a health service to encapsulate dependency checks, add Docker healthchecks to docker-compose.yml, and write comprehensive integration tests. Follow the project's existing async patterns, logging conventions, and testing structure. Ensure readiness returns 503 when dependencies are unavailable, and document response formats clearly.
