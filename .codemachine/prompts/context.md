# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T6",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Implement rate limiting using slowapi with Redis backend. Configure different limits: auth (5/min), commands (10/min), general (100/min). Return 429 with Retry-After. Add admin exemptions. Write integration tests.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Security - Rate Limiting).",
  "target_files": [
    "backend/app/middleware/rate_limiting_middleware.py",
    "backend/app/main.py",
    "backend/requirements.txt",
    "backend/tests/integration/test_rate_limiting.py"
  ],
  "input_files": [
    "backend/app/main.py"
  ],
  "deliverables": "Rate limiting middleware; Redis-backed storage; admin exemptions; tests.",
  "acceptance_criteria": "6th login request in 1min returns 429; Response includes Retry-After; 11th command returns 429; Admins exceed limits; Limits reset after window; Tests verify enforcement, reset, exemption; Coverage ≥80%; No errors",
  "dependencies": [
    "I2.T1"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Rate Limiting Strategy (Architecture Blueprint Section 3.8)

**Security Requirements - Rate Limiting:**

The system must implement rate limiting to protect against abuse and ensure fair resource usage:

1. **Purpose:**
   - Prevent brute force attacks on authentication endpoints
   - Protect against API abuse and DoS attacks
   - Ensure fair resource allocation across users
   - Maintain system stability under load

2. **Rate Limit Tiers:**
   - **Authentication endpoints (`/api/v1/auth/*`):** 5 requests/minute per IP
     - Protects against credential stuffing and brute force attacks
     - Login, refresh token, password reset endpoints

   - **Command execution (`/api/v1/commands`):** 10 requests/minute per user
     - Prevents excessive vehicle command spam
     - Protects vehicle communication infrastructure
     - Per-user tracking (not per-IP) for authenticated endpoints

   - **General API endpoints:** 100 requests/minute per user
     - Vehicle listing, status checks, history queries
     - Reasonable limit for normal usage patterns

3. **Storage Backend:**
   - Use Redis for distributed rate limit counters
   - Enables scaling across multiple backend instances
   - Fast in-memory operations for minimal latency impact
   - Automatic expiration of counters using Redis TTL

4. **Response Format:**
   - HTTP Status: 429 Too Many Requests
   - Headers:
     - `Retry-After`: Seconds until limit resets
     - `X-RateLimit-Limit`: Maximum requests allowed
     - `X-RateLimit-Remaining`: Requests remaining in current window
     - `X-RateLimit-Reset`: Unix timestamp when limit resets
   - Body: JSON error response with error code "RATE_001"

5. **Admin Exemptions:**
   - Admin role users should bypass rate limits
   - Enables operational troubleshooting without restrictions
   - Identified via JWT token role claim

6. **Implementation Approach:**
   - Use slowapi library (FastAPI-compatible rate limiting)
   - Middleware-based approach for centralized enforcement
   - Per-route rate limit decorators for granular control
   - Graceful degradation if Redis unavailable (log warning, allow request)

### Context: Redis Integration

**Current Redis Usage:**
- WebSocket pub/sub for real-time response streaming
- Vehicle status caching (30-second TTL)
- Session storage (refresh tokens)

**Rate Limiting Requirements:**
- Reuse existing Redis connection from `app.config.REDIS_URL`
- Use separate key namespace: `ratelimit:{identifier}:{endpoint}`
- Key format examples:
  - `ratelimit:ip:192.168.1.100:/api/v1/auth/login`
  - `ratelimit:user:uuid-here:/api/v1/commands`

### Context: Middleware Architecture

**Current Middleware Stack (LIFO execution order):**
1. `LoggingMiddleware` (outermost - generates correlation_id)
2. `ErrorHandlingMiddleware` (catches exceptions, formats errors)
3. `CORSMiddleware` (handles cross-origin requests)
4. Route handlers (innermost)

**Rate Limiting Middleware Position:**
- Should be added AFTER LoggingMiddleware (so correlation_id available)
- Should be BEFORE ErrorHandlingMiddleware (so rate limit errors are caught and formatted)
- Registration order in main.py:
  ```python
  app.add_middleware(LoggingMiddleware)        # First (outermost)
  app.add_middleware(RateLimitingMiddleware)   # Second
  app.add_middleware(CORSMiddleware)           # Last (innermost)
  ```

### Context: Error Response Standards

**Rate Limit Error Response Format:**
Following the standardized error response pattern from I4.T5:

```json
{
  "error": {
    "code": "RATE_001",
    "message": "Rate limit exceeded. Please try again later.",
    "correlation_id": "uuid-here",
    "timestamp": "2025-10-30T15:00:00Z",
    "path": "/api/v1/auth/login",
    "retry_after": 45
  }
}
```

**Headers to Include:**
- `Retry-After: 45` (seconds)
- `X-RateLimit-Limit: 5`
- `X-RateLimit-Remaining: 0`
- `X-RateLimit-Reset: 1730300100` (Unix timestamp)

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/app/main.py`
- **Summary:** Main FastAPI application entry point. Currently registers LoggingMiddleware (line 80), ErrorHandlingMiddleware (implicit via exception handlers), and CORSMiddleware (lines 83-89). Includes Prometheus instrumentation (lines 99-100).
- **Recommendation:** You MUST add rate limiting middleware registration at line 81 (after LoggingMiddleware, before CORSMiddleware). Import the new middleware at the top with other middleware imports.
- **Middleware Order Pattern:** The current order is LoggingMiddleware → CORSMiddleware. Insert RateLimitingMiddleware between them.
- **Startup Hook:** Lines 134-146 define startup event. You MAY want to add Redis connection verification here for rate limiter initialization.

#### File: `backend/app/config.py`
- **Summary:** Configuration using pydantic-settings. Currently loads DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, LOG_LEVEL (lines 19-30).
- **Recommendation:** REDIS_URL is already available at `settings.REDIS_URL`. You SHOULD reuse this connection for rate limiting. No changes needed to this file.
- **Important:** Settings is a singleton instance (line 42), loaded once and reused throughout the application.

#### File: `backend/app/dependencies.py`
- **Summary:** Authentication and authorization dependencies. `get_current_user()` (lines 27-105) extracts and validates JWT tokens. `require_role()` factory (lines 108-158) creates role-based authorization checkers.
- **Recommendation:** You MUST use these dependencies to extract user information for rate limiting. For authenticated endpoints, use `current_user.user_id` as the rate limit key. For admin exemptions, check `current_user.role == "admin"`.
- **Key Pattern:** Dependencies return User object with fields: `user_id`, `username`, `role`, `is_active`.

#### File: `backend/app/api/v1/auth.py`
- **Summary:** Authentication endpoints including `/login`, `/refresh`, `/logout`, `/me`. Login endpoint (lines 41-46) is the primary target for rate limiting (5 req/min).
- **Recommendation:** Apply IP-based rate limiting to authentication endpoints (since users aren't authenticated yet). Extract client IP using `app.utils.request_utils.get_client_ip(request)`.
- **Pattern:** Authentication endpoints raise `HTTPException(status_code=401, detail="...")` on auth failure.

#### File: `backend/app/api/v1/websocket.py` (lines 148-150)
- **Summary:** WebSocket endpoint demonstrating Redis client creation: `redis.from_url(settings.REDIS_URL, decode_responses=True)`.
- **Recommendation:** You SHOULD use the same pattern to create Redis client in rate limiting middleware. Note the `decode_responses=True` parameter for string handling.
- **Redis Usage Pattern:** Already imports `redis.asyncio as redis`. WebSocket uses pub/sub; rate limiter will use GET/SET/EXPIRE commands.

#### File: `backend/requirements.txt`
- **Summary:** Production dependencies. Currently includes redis>=5.0.0 (line 14) for WebSocket and caching.
- **Recommendation:** You MUST add slowapi dependency. Add line after redis: `slowapi>=0.1.9`. Slowapi is a FastAPI-compatible port of Flask-Limiter.
- **Note:** Do NOT add flask-limiter as it's Flask-specific. Slowapi is the correct library for FastAPI.

#### File: `backend/tests/conftest.py` (lines 81-100)
- **Summary:** Test fixtures for database sessions and async HTTP client. Uses `app.dependency_overrides` pattern to inject test dependencies (line 97).
- **Recommendation:** You SHOULD create a similar override for Redis in rate limiting tests. Mock Redis client to avoid requiring Redis server during tests.
- **Testing Pattern:** Tests use `AsyncClient` fixture with base URL. Demonstrates how to override dependencies for testing.

#### File: `backend/app/middleware/logging_middleware.py`
- **Summary:** LoggingMiddleware generates correlation IDs, binds to structlog context, logs requests/responses. Uses middleware pattern with `__call__` method accepting `request: Request` and `call_next: RequestResponseEndpoint`.
- **Recommendation:** You MUST follow the same middleware class pattern. Your RateLimitingMiddleware should have `__init__(self, app: ASGIApp)` and `async def __call__(self, request: Request, call_next: RequestResponseEndpoint) -> Response`.
- **Key Pattern:** Uses try/finally to ensure cleanup. Accesses correlation_id from structlog contextvars for including in logs.

#### File: `backend/app/utils/error_codes.py`
- **Summary:** Error code definitions using Enum pattern. Defines error codes for AUTH, VAL, DB, VEH, SYS categories.
- **Recommendation:** You MUST add a new error code for rate limiting. Add to the ErrorCode enum: `RATE_LIMIT_EXCEEDED = "RATE_001"`. Add corresponding message to ERROR_MESSAGES dict.
- **Convention:** Error codes use category prefix (RATE) + 3-digit number (001).

### Implementation Tips & Notes

**Tip 1 - Slowapi Integration:**
Slowapi provides two integration approaches:
1. **Limiter instance with decorators:** Apply per-route with `@limiter.limit("5/minute")`
2. **Middleware approach:** Global rate limiting for all endpoints

For this task, use a HYBRID approach:
- Create Limiter instance in middleware file
- Apply default limit via middleware (`100/minute`)
- Override specific routes with decorators (`5/minute` for auth, `10/minute` for commands)

Example initialization:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,  # Default to IP-based
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window"
)
```

**Tip 2 - Custom Key Functions:**
Slowapi's `get_remote_address` only provides IP-based limiting. You MUST create custom key functions for user-based limiting:

```python
def get_user_id_or_ip(request: Request) -> str:
    """Extract user_id from JWT if authenticated, otherwise use IP."""
    # Try to extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        payload = verify_access_token(token)
        if payload and "user_id" in payload:
            user_id = payload["user_id"]
            # Check if admin (exempt from rate limits)
            if payload.get("role") == "admin":
                return f"admin:{user_id}"  # Special key for admins
            return f"user:{user_id}"

    # Fall back to IP address
    return f"ip:{get_client_ip(request)}"
```

**Tip 3 - Admin Exemption Strategy:**
Two approaches for admin exemptions:
1. **Key-based:** Return special key for admins (e.g., `admin:{user_id}`) and set very high limit
2. **Pre-check:** In middleware, check role before rate limiting and skip if admin

Recommended: Use **key-based approach** (approach 1) for consistency. Set admin limit to 10,000/minute (effectively unlimited but still tracked).

**Tip 4 - Rate Limit Response Headers:**
Slowapi automatically adds `X-RateLimit-*` headers, but you need to add `Retry-After` manually. Modify the rate limit exception handler:

```python
from slowapi.errors import RateLimitExceeded

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    # Extract time until reset
    retry_after = exc.retry_after  # Seconds until limit resets

    # Format standardized error response
    response = format_error_response(
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        status_code=429,
        request=request,
        additional_data={"retry_after": retry_after}
    )

    # Add Retry-After header
    response.headers["Retry-After"] = str(int(retry_after))

    return response
```

**Tip 5 - Per-Endpoint Rate Limits:**
Apply decorators to specific endpoints using FastAPI's dependency injection:

```python
# In auth.py
from app.middleware.rate_limiting_middleware import limiter

@router.post("/login")
@limiter.limit("5/minute", key_func=get_client_ip)  # IP-based for auth
async def login(...):
    ...

# In commands.py
@router.post("/commands")
@limiter.limit("10/minute", key_func=get_user_id_or_ip)  # User-based
async def submit_command(...):
    ...
```

**Warning - Redis Connection Handling:**
Rate limiting middleware will be called on EVERY request. Creating a new Redis connection per request is inefficient. You MUST:
1. Create Redis client once (module-level or in middleware __init__)
2. Reuse connection across all requests
3. Handle Redis connection errors gracefully (log error, allow request through)

Example pattern:
```python
# Module-level Redis client
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error("rate_limiter_redis_init_failed", error=str(e))
    redis_client = None  # Graceful degradation

# In middleware
if redis_client is None:
    logger.warning("rate_limiter_disabled_no_redis")
    return await call_next(request)
```

**Warning - Slowapi Middleware Registration:**
Slowapi requires special integration with FastAPI. You CANNOT use standard middleware registration (`app.add_middleware`). Instead:
1. Create Limiter instance
2. Register exception handler for RateLimitExceeded
3. Apply limits via decorators on routes
4. Optionally: Use `limiter.enabled = True/False` for testing

**Note - Testing Strategy:**
Rate limiting tests require mocking Redis or using fakeredis. Recommended approach:

```python
import pytest
from fakeredis import aioredis as fakeredis

@pytest.fixture
def mock_redis():
    """Provide fake Redis for testing."""
    return fakeredis.FakeRedis(decode_responses=True)

async def test_auth_rate_limit(async_client, mock_redis):
    """Test that 6th login attempt returns 429."""
    # Override Redis in limiter
    limiter.storage._storage = mock_redis

    # Make 5 successful attempts
    for i in range(5):
        response = await async_client.post("/api/v1/auth/login", json={...})
        assert response.status_code in [200, 401]  # Auth may fail, but not rate limited

    # 6th attempt should be rate limited
    response = await async_client.post("/api/v1/auth/login", json={...})
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert response.json()["error"]["code"] == "RATE_001"
```

**Note - Fixed Window vs Sliding Window:**
Slowapi supports two strategies:
- `fixed-window`: Simple counter that resets at interval boundary (e.g., every 60 seconds)
- `sliding-window`: More accurate, counts requests in sliding time window

Use `fixed-window` for simplicity. It's sufficient for the MVP and has lower Redis overhead.

**Best Practice - Correlation ID in Rate Limit Logs:**
Slowapi doesn't automatically include correlation IDs in logs. You SHOULD add custom logging when rate limits are hit:

```python
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        method=request.method,
        limit=exc.limit,
        retry_after=exc.retry_after
    )
    # ... rest of handler
```

**Best Practice - Rate Limit Configuration:**
Make rate limits configurable via environment variables (future enhancement). For now, hardcode in middleware but use constants:

```python
# At top of middleware file
RATE_LIMIT_AUTH = "5/minute"
RATE_LIMIT_COMMANDS = "10/minute"
RATE_LIMIT_GENERAL = "100/minute"
RATE_LIMIT_ADMIN = "10000/minute"  # Effectively unlimited
```

**Convention - Import Structure:**
Add rate limiting imports to relevant files:

```python
# In backend/app/middleware/rate_limiting_middleware.py
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import redis.asyncio as redis
from app.config import settings
from app.utils.error_codes import ErrorCode
from app.utils.request_utils import get_client_ip
```

**Testing Edge Cases:**
Your integration tests MUST cover:
1. **Auth rate limit:** 5 login attempts → 6th returns 429
2. **Command rate limit:** 10 command submissions → 11th returns 429
3. **General rate limit:** 100 general requests → 101st returns 429
4. **Admin exemption:** Admin user makes 20 requests → all succeed
5. **Limit reset:** Wait for window to expire → requests allowed again
6. **Retry-After header:** Verify header present and value reasonable (≤60 seconds)
7. **Error response format:** Verify JSON structure matches standardized format
8. **Multiple users:** User A hits limit → User B unaffected
9. **Unauthenticated vs authenticated:** IP-based limiting for auth endpoints, user-based for protected endpoints

**Environment Variable Documentation:**
Add to `.env.example`:
```
REDIS_URL=redis://localhost:6379/0  # Already exists, used for rate limiting
```

Update README to document rate limiting:
- Rate limit values (5/min auth, 10/min commands, 100/min general)
- Admin exemption behavior
- How to temporarily disable (set `limiter.enabled = False`)
- Redis requirement for rate limiting

**Integration with Error Handling Middleware:**
The RateLimitExceeded exception should be caught by the exception handler you register in main.py. The error response will automatically follow the standardized format from I4.T5 if you use `format_error_response()` helper.

**Code Quality Checklist:**
- [ ] Async/await used throughout (Redis operations are async)
- [ ] Type hints on all functions (`Request`, `Response`, `str`, etc.)
- [ ] Comprehensive docstrings (module, classes, functions)
- [ ] No linter errors (`ruff check`, `mypy`)
- [ ] Test coverage ≥80% (`pytest --cov`)
- [ ] Structured logging for rate limit events
- [ ] Graceful degradation if Redis unavailable

---

## 4. Additional Context from Codebase Survey

**Project Structure Observations:**
- Backend uses async/await throughout (AsyncSession, async Redis)
- Middleware pattern established (LoggingMiddleware as reference)
- Error handling centralized with standardized responses
- Testing comprehensive (95+ tests, high coverage)
- Redis already integrated for WebSocket pub/sub and caching

**Dependency Analysis:**
- redis>=5.0.0: Already available
- slowapi: **NOT YET INSTALLED** - must add to requirements.txt
- fakeredis: Recommend adding to requirements-dev.txt for testing

**Current Middleware Flow:**
```
Request → LoggingMiddleware (correlation_id, logging)
        → [Your RateLimitingMiddleware HERE]
        → CORSMiddleware
        → Route Handler
        → Response
```

**Redis Key Namespace Recommendation:**
Use consistent key naming:
- `ratelimit:ip:{ip_address}:{endpoint}` - For unauthenticated endpoints
- `ratelimit:user:{user_id}:{endpoint}` - For authenticated endpoints
- `ratelimit:admin:{user_id}:{endpoint}` - For admin users (high limits)

Example: `ratelimit:ip:192.168.1.100:/api/v1/auth/login`

**Existing Request Utilities:**
From `backend/app/utils/request_utils.py`:
- `get_client_ip(request: Request) -> str` - Extracts client IP with X-Forwarded-For support
- `get_user_agent(request: Request) -> str` - Extracts User-Agent header

You SHOULD reuse `get_client_ip()` for IP-based rate limiting.

---

## Summary

You are implementing a production-grade rate limiting system to protect the SOVD WebApp from abuse and ensure fair resource usage. Use slowapi (FastAPI-compatible rate limiting) with Redis backend for distributed rate limit counters. Configure three rate limit tiers: 5 req/min for authentication endpoints (IP-based), 10 req/min for command execution (user-based), and 100 req/min for general API endpoints. Implement admin exemptions by checking user role from JWT tokens. Return 429 status with Retry-After header and standardized error response format. Create comprehensive integration tests covering limit enforcement, reset behavior, admin exemptions, and multi-user scenarios. Follow the project's async patterns, middleware conventions, error handling standards, and maintain ≥80% test coverage.
