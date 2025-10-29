# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Implement WebSocket endpoint in `backend/app/api/v1/websocket.py` at path `/ws/responses/{command_id}`. WebSocket connection requires JWT authentication via query parameter `?token={jwt}`. Implement connection lifecycle: 1) Validate JWT on connect (disconnect with error if invalid), 2) Subscribe to Redis Pub/Sub channel `response:{command_id}`, 3) Listen for response events from Redis, 4) Forward events to WebSocket client as JSON messages (format: `{"event": "response", "command_id": "...", "response": {...}}`), 5) Handle status change events (`{"event": "status", "status": "completed"}`), 6) Handle errors (`{"event": "error", "error_message": "..."}`), 7) Unsubscribe and close on client disconnect. Implement WebSocket connection manager in `backend/app/services/websocket_manager.py` to track active connections and handle broadcasting. Update mock vehicle connector (I2.T5) to publish response events to Redis channel. Write integration tests in `backend/tests/integration/test_websocket.py` using WebSocket test client.

---

## Issues Detected

### 1. Linting Errors

*   **Unused imports in `tests/integration/test_websocket.py`:**
    - Line 10: `AsyncMock` is imported but never used
    - Line 10: `patch` is imported but never used
    - Line 16: `AsyncClient` is imported but never used

### 2. Test Failures

*   **Test: `test_websocket_connection_inactive_user`**
    - **Error:** `asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "sovd_user"`
    - **Root Cause:** The test is using the `inactive_user` fixture which tries to connect to the actual PostgreSQL database instead of the test database (SQLite). The WebSocket endpoint is getting a database session from the real database dependency instead of the test fixture.
    - **Issue:** The `db: AsyncSession = Depends(get_db)` dependency in the WebSocket endpoint at `websocket.py:243` is using the real database connection, not the test database override from `conftest.py`.

*   **Test: `test_websocket_receives_response_event`**
    - **Error:** `anyio.EndOfStream` and `ClosedResourceError`
    - **Root Cause:** The WebSocket connection is closing before the test can receive the event. This is likely because the event is being published to Redis before the WebSocket has time to subscribe to the channel, or the TestClient's event loop is not compatible with the async Redis pub/sub pattern.
    - **Issue:** The test uses threading and a separate event loop to publish events, which may not be synchronizing correctly with the WebSocket's subscription timing.

*   **Test: `test_websocket_receives_status_event`**
    - **Error:** Same as above - `anyio.EndOfStream`

*   **Test: `test_websocket_receives_error_event`**
    - **Error:** Same as above - `anyio.EndOfStream`

*   **Test: `test_websocket_multiple_clients`**
    - **Error:** Same as above - `anyio.EndOfStream`

*   **Test: `test_websocket_no_event_on_different_command`**
    - **Error:** Same as above - `anyio.EndOfStream`

---

## Best Approach to Fix

### Fix 1: Remove Unused Imports

In `backend/tests/integration/test_websocket.py`:
- Remove the line `from unittest.mock import AsyncMock, patch` (line 10)
- Remove the line `from httpx import AsyncClient` (line 16)

### Fix 2: Fix Database Dependency Injection in Tests

The WebSocket endpoint needs to use the test database session instead of the real database. You have TWO options:

**Option A (Recommended):** Modify the test fixtures to properly override the `get_db` dependency for WebSocket tests.

In `backend/tests/integration/test_websocket.py`, add a new fixture that creates a TestClient with dependency overrides:

```python
@pytest_asyncio.fixture
async def ws_test_client(db_session: AsyncSession):
    """Create TestClient with database dependency override."""
    from app.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Then update ALL tests to use `ws_test_client` instead of `TestClient(app)`.

**Option B:** Use the existing `async_client` fixture pattern but extend it for WebSocket support. However, this may require refactoring the existing conftest.py.

### Fix 3: Fix Redis Event Publishing Timing

The current test implementation uses threading and separate event loops which creates race conditions. You need to ensure the WebSocket has subscribed BEFORE publishing events.

**Recommended Solution:** Instead of using threading, use `asyncio.create_task()` to publish events after a delay:

```python
async def publish_event_after_delay(command_id: str, event_data: dict, delay: float = 0.1):
    """Publish event to Redis after a short delay."""
    await asyncio.sleep(delay)
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        channel = f"response:{command_id}"
        await redis_client.publish(channel, json.dumps(event_data))
    finally:
        await redis_client.aclose()
```

However, since `TestClient` runs in a separate thread with its own event loop, you need a different approach:

**Better Solution:** Create a helper function that publishes to Redis synchronously in a thread-safe manner, but with a longer delay to ensure subscription:

```python
def publish_event_sync(command_id: str, event_data: dict):
    """Publish event to Redis synchronously."""
    import time
    time.sleep(1.0)  # Increase delay to ensure subscription completes

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        channel = f"response:{command_id}"
        loop.run_until_complete(redis_client.publish(channel, json.dumps(event_data)))
        loop.run_until_complete(redis_client.aclose())
    finally:
        loop.close()
```

Update ALL tests that publish events to use `time.sleep(1.0)` instead of `time.sleep(0.5)` to give more time for subscription.

### Fix 4: Add Timeout to `receive_json()` Calls

The tests should handle potential timeouts gracefully. However, `TestClient.websocket.receive_json()` doesn't have a timeout parameter. Instead, you should verify the connection is working before attempting to receive:

```python
# After connecting, first verify the WebSocket is alive
import time
time.sleep(0.5)  # Give connection time to establish

# Then attempt to receive with a try/except
try:
    data = websocket.receive_json()
    # ... assertions
except anyio.EndOfStream:
    pytest.fail("WebSocket closed before receiving event")
```

### Fix 5: Ensure Test Database is Used

Add debug logging to verify which database is being used. In the `authenticate_websocket` function, you could add:

```python
logger.info(f"Database session: {db}")
```

However, the real fix is to ensure the dependency override works correctly (Fix 2).

---

## Summary of Required Changes

1. **File: `backend/tests/integration/test_websocket.py`**
   - Remove unused imports: `AsyncMock`, `patch`, `AsyncClient`
   - Add `ws_test_client` fixture with database dependency override
   - Replace all `TestClient(app)` with `ws_test_client` fixture usage
   - Increase delay in all `publish_*_sync` functions from 0.5s to 1.0s
   - Add error handling for `anyio.EndOfStream` with proper pytest.fail messages

2. **File: `backend/tests/conftest.py`** (if choosing Option B)
   - Extend the existing fixtures to support WebSocket testing with dependency overrides

---

## Expected Outcome

After these fixes:
- All linting errors should be resolved (ruff check passes)
- All 11 WebSocket integration tests should pass
- Tests should verify: successful connection, auth rejection, event delivery (response/status/error events), multiple clients, and proper cleanup
- No database connection errors
- WebSocket events should be received correctly in all test scenarios
