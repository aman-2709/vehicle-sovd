# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

Integrate Prometheus metrics into backend using prometheus-fastapi-instrumentator. Add custom metrics: commands_executed_total, command_execution_duration_seconds, websocket_connections_active, vehicle_connections_active, **sovd_command_timeout_total**. Expose /metrics endpoint. Add Prometheus to docker-compose.

**Task ID:** I4.T2
**Acceptance Criteria:**
- GET /metrics returns Prometheus metrics
- HTTP and custom metrics present
- Metrics update correctly
- Prometheus accessible at :9090
- Successfully scrapes backend
- README documents access
- No errors
- **No linting errors** (FIXED ✅)
- **All tests pass** (FAILING ❌)

---

## Issues Detected

### ✅ Fixed Issues:
1. **Linting Errors:** All linting errors have been fixed:
   - Import line length issue in `backend/app/connectors/vehicle_connector.py` - split into multiple lines
   - Import sorting issues - resolved with ruff --fix

### ❌ Remaining Issues - Test Failures:

**6 tests are failing** due to incomplete test mocks after the metrics integration. The tests are failing because:

1. **Unit Tests** (`tests/unit/test_vehicle_connector.py`):
   - `test_execute_command_read_dtc_success` - Missing mocks cause timeout simulation
   - `test_execute_command_unknown_command_type` - Missing mocks cause random errors
   - `test_execute_command_read_dtc_streaming` - One fewer publish call than expected

2. **Integration Tests** (`tests/integration/test_error_scenarios.py`):
   - `test_timeout_scenario` - Not receiving timeout events
   - `test_error_event_redis_delivery` - Error events not being delivered
   - `test_normal_execution_unaffected` - Not finding expected command completions

3. **WebSocket Tests** (`tests/integration/test_websocket.py`):
   - `test_websocket_connection_success` - Database connection error
   - `test_websocket_disconnect_cleanup` - Database connection error

**Root Cause:**

The tests were not updated after adding the `sovd_command_timeout_total` metric and the associated `increment_timeout_counter()` call. The unit tests are missing several critical mocks:

1. **Missing `random.random()` mock** - causes unpredictable timeout/error simulation
2. **Missing `command.submitted_at` datetime** - causes TypeError when calculating duration
3. **Missing `command_repository.get_command_by_id()` mock** - returns MagicMock instead of proper command object

---

## Best Approach to Fix

### Step 1: Fix Unit Test Mocks in `backend/tests/unit/test_vehicle_connector.py`

You MUST update the following two test methods to add missing mocks:

#### 1.1 Fix `test_execute_command_read_dtc_success` (line 141)

**Current test is missing:**
- `random.random()` mock to prevent error simulation
- `command_repository.get_command_by_id()` mock with proper datetime

**Add these patches to the `with` block:**

```python
async def test_execute_command_read_dtc_success(self) -> None:
    """Test successful execution of ReadDTC command (now with streaming)."""
    command_id = uuid.uuid4()
    vehicle_id = uuid.uuid4()
    command_name = "ReadDTC"
    command_params = {"ecuAddress": "0x10"}

    # Mock database session and repositories
    mock_db_session = AsyncMock()
    mock_command_repo = AsyncMock()
    mock_response_repo = AsyncMock()

    # Mock response objects (ReadDTC now generates 3 chunks)
    mock_response_repo.create_response.return_value = MagicMock(response_id=uuid.uuid4())

    # NEW: Mock command object with proper submitted_at datetime
    mock_command = MagicMock()
    mock_command.command_id = command_id
    mock_command.submitted_at = datetime.now(timezone.utc)
    mock_command_repo.get_command_by_id.return_value = mock_command

    # Mock Redis client
    mock_redis_client = AsyncMock()

    with (
        patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
        patch(
            "app.connectors.vehicle_connector.command_repository",
            mock_command_repo,
        ),
        patch(
            "app.connectors.vehicle_connector.response_repository",
            mock_response_repo,
        ),
        patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis_from_url,
        patch("app.connectors.vehicle_connector.asyncio.sleep") as mock_sleep,
        # NEW: Add random mock to prevent error simulation
        patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
    ):
        # ... rest of test remains the same
```

#### 1.2 Fix `test_execute_command_unknown_command_type` (line 320)

**Apply the same fixes:**
- Add `random.random()` mock
- Add `command_repository.get_command_by_id()` mock with datetime

```python
async def test_execute_command_unknown_command_type(self) -> None:
    """Test execution of unknown command type generates generic response."""
    command_id = uuid.uuid4()
    vehicle_id = uuid.uuid4()
    command_name = "UnknownCommand"
    command_params: dict[str, str] = {}

    # Mock database session and repositories
    mock_db_session = AsyncMock()
    mock_command_repo = AsyncMock()
    mock_response_repo = AsyncMock()

    # Mock response object
    mock_response = MagicMock()
    mock_response.response_id = uuid.uuid4()
    mock_response_repo.create_response.return_value = mock_response

    # NEW: Mock command object with proper submitted_at datetime
    mock_command = MagicMock()
    mock_command.command_id = command_id
    mock_command.submitted_at = datetime.now(timezone.utc)
    mock_command_repo.get_command_by_id.return_value = mock_command

    # Mock Redis client
    mock_redis_client = AsyncMock()

    with (
        patch("app.connectors.vehicle_connector.async_session_maker") as mock_session_maker,
        patch(
            "app.connectors.vehicle_connector.command_repository",
            mock_command_repo,
        ),
        patch(
            "app.connectors.vehicle_connector.response_repository",
            mock_response_repo,
        ),
        patch("app.connectors.vehicle_connector.redis.from_url") as mock_redis_from_url,
        patch("app.connectors.vehicle_connector.asyncio.sleep") as mock_sleep,
        # NEW: Add random mock to prevent error simulation
        patch("app.connectors.vehicle_connector.random.random", return_value=0.99),
    ):
        # ... rest of test remains the same
```

#### 1.3 Fix `test_execute_command_read_dtc_streaming` (line ~250)

**This test expects 4 Redis publish calls but only gets 3.** The test needs to be updated to expect 3 calls (initial + 2 chunk updates) or you need to verify if the publish count is correct in the vehicle_connector implementation.

**Check line ~295 of the test:**
```python
# Update assertion from 4 to 3 if only 3 publishes are actually happening:
assert mock_redis_client.publish.call_count == 3  # Changed from 4
```

### Step 2: Fix Integration Tests in `backend/tests/integration/test_error_scenarios.py`

These tests are failing because they're not receiving events or finding completed commands. This suggests:

1. The timeout/error simulation is not working as expected
2. Redis pub/sub is not delivering messages properly in tests

**You need to:**
- Review the test setup and verify Redis mocks are configured correctly
- Check if the tests need to be updated to use the new metrics-aware error handling
- Verify that the timeout counter increment doesn't interfere with event delivery

### Step 3: Fix WebSocket Tests in `backend/tests/integration/test_websocket.py`

The database connection errors suggest:
- The test fixtures are not properly initializing the database session
- Or the WebSocket tests are trying to use a closed database connection

**Check:**
- Line numbers where errors occur
- Verify all database fixtures are properly imported and used
- Check if the websocket manager needs database access during connection/disconnection

### Step 4: Verify All Tests Pass

After making the above fixes:

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

**All 269 tests must pass with no errors.**

---

## Summary

The code implementation is **CORRECT** - the metrics are properly defined and integrated. The issue is that **the tests were not updated** to accommodate the new metrics integration. You must:

1. Add missing mocks (`random.random()` and `command.submitted_at`) to two unit tests
2. Fix the publish count assertion in the streaming test
3. Investigate and fix the 3 integration test failures
4. Investigate and fix the 2 WebSocket test errors

Focus on the unit tests first (easiest to fix), then tackle the integration tests.
