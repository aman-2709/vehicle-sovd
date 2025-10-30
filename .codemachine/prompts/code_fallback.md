# Code Refinement Task

The previous code submission did not pass verification. The task has not been completed - no rate limiting implementation was found.

---

## Original Task Description

**Task ID:** I4.T6
**Description:** Implement rate limiting using slowapi with Redis backend. Configure different limits: auth (5/min), commands (10/min), general (100/min). Return 429 with Retry-After. Add admin exemptions. Write integration tests.

**Acceptance Criteria:**
- 6th login request in 1min returns 429
- Response includes Retry-After header
- 11th command returns 429
- Admins exceed limits without being rate limited
- Limits reset after time window
- Tests verify enforcement, reset, exemption
- Coverage ≥80%
- No linting errors

---

## Issues Detected

* **Missing Implementation:** No rate limiting code was created. The following required files do not exist:
  * `backend/app/middleware/rate_limiting_middleware.py` - Rate limiting middleware not created
  * `backend/tests/integration/test_rate_limiting.py` - Integration tests not created
* **Missing Dependency:** The `slowapi>=0.1.9` dependency has not been added to `backend/requirements.txt`
* **Missing Integration:** Rate limiting middleware has not been registered in `backend/app/main.py`
* **Missing Error Code:** The error code `RATE_001` for rate limit exceeded has not been added to `backend/app/utils/error_codes.py`

---

## Best Approach to Fix

You MUST implement the complete rate limiting system from scratch. Follow these steps carefully:

### Step 1: Add slowapi Dependency

Add `slowapi>=0.1.9` to `backend/requirements.txt` after the redis line (after line 14).

### Step 2: Add Rate Limit Error Code

Edit `backend/app/utils/error_codes.py`:
- Add `RATE_LIMIT_EXCEEDED = "RATE_001"` to the `ErrorCode` enum
- Add the corresponding error message to `ERROR_MESSAGES`: `"RATE_001": "Rate limit exceeded. Please try again later."`

### Step 3: Create Rate Limiting Middleware

Create `backend/app/middleware/rate_limiting_middleware.py` with the following components:

**Required Implementation:**
1. **Limiter Instance:** Create a slowapi Limiter instance with Redis backend using `settings.REDIS_URL`
2. **Custom Key Functions:**
   - `get_client_ip_key(request)`: Returns `f"ip:{get_client_ip(request)}"` for IP-based limiting
   - `get_user_id_key(request)`: Extracts user_id from JWT token, returns `f"user:{user_id}"` for authenticated users, or `f"admin:{user_id}"` for admins (to exempt them), or falls back to IP if not authenticated
3. **Rate Limit Constants:**
   ```python
   RATE_LIMIT_AUTH = "5/minute"
   RATE_LIMIT_COMMANDS = "10/minute"
   RATE_LIMIT_GENERAL = "100/minute"
   RATE_LIMIT_ADMIN = "10000/minute"  # Effectively unlimited
   ```
4. **Limiter Configuration:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(
       key_func=get_remote_address,
       storage_uri=settings.REDIS_URL,
       strategy="fixed-window"
   )
   ```

**Important Notes:**
- Use `from app.utils.request_utils import get_client_ip` to extract client IP addresses
- For JWT token parsing in `get_user_id_key()`, you can import and use the token verification from `app.dependencies` or parse the token manually using `jwt.decode()`
- Handle token parsing errors gracefully (fall back to IP-based limiting if token is invalid)
- Use structured logging to log rate limit events

### Step 4: Register Rate Limit Exception Handler

Edit `backend/app/main.py`:
1. Import the limiter and exception:
   ```python
   from slowapi import _rate_limit_exceeded_handler
   from slowapi.errors import RateLimitExceeded
   from app.middleware.rate_limiting_middleware import limiter
   ```
2. Add the limiter to the FastAPI app state (after creating the app, around line 42):
   ```python
   app.state.limiter = limiter
   ```
3. Register the exception handler (after other exception handlers, around line 76):
   ```python
   @app.exception_handler(RateLimitExceeded)
   async def rate_limit_exception_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
       """Handle rate limit exceeded errors."""
       from app.middleware.error_handling_middleware import format_error_response
       from app.utils.error_codes import ErrorCode

       # Calculate retry_after
       retry_after = int(exc.detail.split("Retry after ")[1].split(" ")[0]) if "Retry after" in exc.detail else 60

       # Format standardized error response
       response = format_error_response(
           error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
           status_code=429,
           request=request,
           additional_data={"retry_after": retry_after}
       )

       # Add Retry-After header
       response.headers["Retry-After"] = str(retry_after)

       # Add rate limit headers
       response.headers["X-RateLimit-Limit"] = str(exc.limit)
       response.headers["X-RateLimit-Remaining"] = "0"

       return response
   ```

### Step 5: Apply Rate Limits to Specific Endpoints

**For Authentication Endpoints** (edit `backend/app/api/v1/auth.py`):
- Import: `from app.middleware.rate_limiting_middleware import limiter, get_client_ip_key, RATE_LIMIT_AUTH`
- Apply decorator to login endpoint:
  ```python
  @router.post("/login")
  @limiter.limit(RATE_LIMIT_AUTH, key_func=get_client_ip_key)
  async def login(...):
  ```

**For Command Endpoints** (edit `backend/app/api/v1/commands.py`):
- Import: `from app.middleware.rate_limiting_middleware import limiter, get_user_id_key, RATE_LIMIT_COMMANDS`
- Apply decorator to command submission endpoint:
  ```python
  @router.post("/commands")
  @limiter.limit(RATE_LIMIT_COMMANDS, key_func=get_user_id_key)
  async def submit_command(...):
  ```

**For General Endpoints** (edit `backend/app/api/v1/vehicles.py`):
- Import: `from app.middleware.rate_limiting_middleware import limiter, get_user_id_key, RATE_LIMIT_GENERAL`
- Apply decorator to vehicle listing endpoint:
  ```python
  @router.get("/vehicles")
  @limiter.limit(RATE_LIMIT_GENERAL, key_func=get_user_id_key)
  async def list_vehicles(...):
  ```

### Step 6: Create Integration Tests

Create `backend/tests/integration/test_rate_limiting.py` with comprehensive tests:

**Required Test Cases:**
1. `test_auth_rate_limit_enforcement`: Make 6 login requests, verify 6th returns 429 with Retry-After header
2. `test_command_rate_limit_enforcement`: Submit 11 commands, verify 11th returns 429
3. `test_general_rate_limit_enforcement`: Make 101 general requests, verify 101st returns 429
4. `test_admin_exemption`: Admin user makes 20 login requests, all succeed (no rate limit)
5. `test_rate_limit_reset`: Hit rate limit, wait for window to expire, verify requests allowed again
6. `test_rate_limit_error_format`: Verify error response follows standardized format with error code "RATE_001"
7. `test_retry_after_header`: Verify Retry-After header is present and reasonable (≤60 seconds)
8. `test_multiple_users_isolated`: User A hits limit, User B unaffected
9. `test_unauthenticated_vs_authenticated`: Verify IP-based limiting for auth endpoints, user-based for protected endpoints

**Testing Approach:**
- Use pytest fixtures from `conftest.py` (`async_client`, `test_session`, `auth_headers_admin`, `auth_headers_user`)
- For testing rate limit reset, use `time.sleep()` or mock time
- Mock or use fakeredis to avoid requiring Redis server during tests
- Verify response status codes, headers, and JSON body structure
- Ensure test coverage ≥80%

**Example Test Structure:**
```python
import pytest
from httpx import AsyncClient

class TestAuthRateLimiting:
    """Test rate limiting on authentication endpoints."""

    @pytest.mark.asyncio
    async def test_auth_rate_limit_enforcement(self, async_client: AsyncClient):
        """Test that 6th login attempt returns 429."""
        # Make 5 login attempts
        for i in range(5):
            response = await async_client.post(
                "/api/v1/auth/login",
                json={"username": "testuser", "password": "wrongpass"}
            )
            assert response.status_code in [200, 401]  # May fail auth, but not rate limited

        # 6th attempt should be rate limited
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "wrongpass"}
        )
        assert response.status_code == 429
        assert "Retry-After" in response.headers
        error = response.json()["error"]
        assert error["code"] == "RATE_001"
        assert "retry_after" in error
```

### Step 7: Run Tests and Fix Linting

After implementation:
1. Run `pytest backend/tests/integration/test_rate_limiting.py -v` to verify all tests pass
2. Run `pytest --cov=backend/app/middleware/rate_limiting_middleware --cov-report=term-missing` to verify ≥80% coverage
3. Run `ruff check backend/app/middleware/` to ensure no linting errors
4. Run `mypy backend/app/middleware/rate_limiting_middleware.py` to ensure type checking passes

---

## Critical Requirements

1. **Use slowapi, not Flask-Limiter** - slowapi is FastAPI-compatible
2. **Reuse existing Redis connection** - Use `settings.REDIS_URL` from config
3. **Follow middleware patterns** - Reference `LoggingMiddleware` for structure
4. **Follow error handling standards** - Use `format_error_response()` from error_handling_middleware
5. **Admin exemption via high limit** - Return `f"admin:{user_id}"` key with 10000/minute limit
6. **IP-based for auth, user-based for protected** - Use appropriate key functions
7. **Comprehensive tests** - Cover all 9 test cases listed above
8. **Structured logging** - Log rate limit events with correlation_id
9. **Graceful degradation** - If Redis unavailable, log warning and allow request
10. **Type hints and docstrings** - All functions must have type hints and comprehensive docstrings

---

## Files to Create/Modify

**Create:**
- `backend/app/middleware/rate_limiting_middleware.py`
- `backend/tests/integration/test_rate_limiting.py`

**Modify:**
- `backend/requirements.txt` (add slowapi)
- `backend/app/utils/error_codes.py` (add RATE_001)
- `backend/app/main.py` (register exception handler and add limiter to app state)
- `backend/app/api/v1/auth.py` (apply rate limit decorator to login)
- `backend/app/api/v1/commands.py` (apply rate limit decorator to submit_command)
- `backend/app/api/v1/vehicles.py` (apply rate limit decorator to list_vehicles)

---

## Success Criteria

Verification will pass when:
1. All required files exist
2. slowapi dependency is in requirements.txt
3. Rate limiting middleware is properly implemented
4. Rate limit exception handler is registered in main.py
5. Rate limits are applied to auth, command, and vehicle endpoints
6. All 9 integration tests pass
7. Test coverage ≥80%
8. No linting errors (ruff check)
9. No type errors (mypy)
10. Admin users can exceed rate limits
11. Error responses follow standardized format with RATE_001 error code
