# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T3",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Enhance vehicle connector to simulate error scenarios: 1) Vehicle timeout (10% of commands, simulate 30 second delay then publish error event `{\"event\": \"error\", \"error_message\": \"Vehicle connection timeout\"}`), 2) Vehicle unreachable (5% of commands, immediately fail with error), 3) Invalid response format (3% of commands, send malformed data then error). Implement timeout logic: if vehicle doesn't respond within 30 seconds, mark command as failed, create audit log entry, publish error event to WebSocket. Implement error event publishing to Redis. Update command service to handle connector errors gracefully (update command status to `failed`, save error_message). Create sequence diagram `docs/diagrams/sequence_error_flow.puml` documenting vehicle timeout scenario (as specified in I2.T8, moved here for relevance). Write integration tests in `backend/tests/integration/test_error_scenarios.py` for timeout and error cases.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Reliability & Availability - Fault Tolerance); Section 2.3 (Known Risks - Vehicle Connectivity).",
  "target_files": [
    "backend/app/connectors/vehicle_connector.py",
    "backend/app/services/command_service.py",
    "docs/diagrams/sequence_error_flow.puml",
    "backend/tests/integration/test_error_scenarios.py"
  ],
  "input_files": [
    "backend/app/connectors/vehicle_connector.py",
    "backend/app/services/command_service.py"
  ],
  "deliverables": "Error simulation in mock connector; timeout handling; error event publishing; sequence diagram; integration tests.",
  "acceptance_criteria": "~10% of commands simulate timeout (configurable probability); Timeout commands update to status=`failed` after 30 seconds; Error message saved in command.error_message field; WebSocket clients receive error event: `{\"event\": \"error\", \"error_message\": \"...\"}`; Audit log created for failed commands (action=`command_failed`); `sequence_error_flow.puml` compiles and shows timeout flow; Integration tests verify: timeout behavior, error event delivery, command status update; Tests use mock timing (don't wait full 30 seconds, use time mocking); No linter errors",
  "dependencies": [
    "I3.T1",
    "I2.T7"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: fault-tolerance (from 05_Operational_Architecture.md)

```markdown
**Fault Tolerance Mechanisms**

**Health Checks:**
- **Liveness Probe**: `/health/live` (returns 200 if service is running)
- **Readiness Probe**: `/health/ready` (checks database, Redis connectivity)
- Kubernetes restarts unhealthy pods automatically

**Circuit Breaker Pattern:**
- Vehicle communication wrapped in circuit breaker (e.g., `tenacity` library)
- After 5 consecutive failures, circuit opens (fail fast)
- Periodic retry attempts to close circuit

**Retry Logic:**
- Vehicle communication retries (3 attempts with exponential backoff)
- Database operations retry on transient errors (connection loss)

**Graceful Degradation:**
- If Redis unavailable, fall back to database for sessions (slower but functional)
- If vehicle unreachable, return clear error (don't crash service)
- If database read replica fails, route to primary (higher load but available)

**Data Persistence:**
- Database backups: Daily automated snapshots (AWS RDS); 30-day retention
- Point-in-time recovery: Restore to any second within last 7 days
- Audit logs: Backed up to S3 (long-term retention)
```

### Context: risk-vehicle-connectivity (from 06_Rationale_and_Future.md)

```markdown
#### Risk 1: Vehicle Connectivity Reliability

**Risk:** Vehicles on cellular networks may have intermittent connectivity, causing command failures.

**Impact:** Poor user experience, low command success rate.

**Mitigation:**
- **Retry logic**: Exponential backoff, 3 retry attempts
- **Circuit breaker**: Fail fast when vehicle consistently unreachable
- **Timeout tuning**: Configurable timeout (default 30s, adjustable per command type)
- **Graceful error messages**: Clear UI feedback ("Vehicle offline. Last seen 5 minutes ago.")
- **Future**: Command queuing (vehicle pulls commands when it reconnects)

**Likelihood:** High | **Severity:** Medium
```

### Context: websocket-protocol (from 04_Behavior_and_Communication.md)

```markdown
**WebSocket Protocol**

Connection: wss://api.sovd.example.com/ws/responses/{command_id}?token={jwt}

Client → Server (subscribe):
{
  "action": "subscribe",
  "command_id": "uuid"
}

Server → Client (response event):
{
  "event": "response",
  "command_id": "uuid",
  "response": {
    "response_id": "uuid",
    "response_payload": { "dtcCode": "P0420", ... },
    "sequence_number": 1,
    "is_final": false,
    "received_at": "2025-10-28T10:00:01Z"
  }
}

Server → Client (status event):
{
  "event": "status",
  "command_id": "uuid",
  "status": "completed",
  "completed_at": "2025-10-28T10:00:01.5Z"
}

Server → Client (error event):
{
  "event": "error",
  "command_id": "uuid",
  "error_message": "Vehicle connection timeout"
}
```

### Context: event-driven-internal (from 04_Behavior_and_Communication.md)

```markdown
**3. Event-Driven (Internal via Redis Pub/Sub)**

Used internally between backend components:
- Vehicle Connector publishes response events → WebSocket Server consumes
- Decouples command execution from response delivery
- Enables horizontal scaling of both components

**Flow:**
1. Vehicle Connector receives response from vehicle
2. Publishes event to Redis channel: `response:{command_id}`
3. WebSocket Server (subscribed to channel) receives event
4. Pushes to connected WebSocket clients
```

### Context: error-handling-flow (from 04_Behavior_and_Communication.md)

```markdown
##### Description: Vehicle Timeout Scenario

This diagram illustrates graceful error handling when a vehicle fails to respond within the timeout period (e.g., 30 seconds):

1. Command is submitted and forwarded to vehicle
2. Vehicle does not respond (connection lost, vehicle offline, etc.)
3. Vehicle Connector detects timeout
4. Error is logged to database and audit log
5. Error event is published to WebSocket
6. User receives clear error message with suggested actions

##### Diagram (PlantUML)

@startuml

title Error Handling Flow - Vehicle Timeout

actor Engineer
participant WebApp
participant AppServer
participant Connector
participant Redis
participant WSServer
participant DB
participant Vehicle

Engineer -> WebApp : Submit command
WebApp -> AppServer : POST /api/v1/commands
AppServer -> DB : Insert command (status=pending)
AppServer -> Connector : Execute command
activate Connector
AppServer --> WebApp : 202 Accepted + command_id

Connector -> Vehicle : gRPC ExecuteCommand
activate Vehicle

... 30 seconds pass with no response ...

Vehicle --x Connector : (timeout - no response)
deactivate Vehicle

Connector -> Connector : Detect timeout, handle gracefully
Connector -> DB : Update command\nstatus=failed\nerror_message="Vehicle timeout"
Connector -> DB : Insert audit log (action=command_timeout)
Connector -> Redis : PUBLISH response:{command_id}\n{"event": "error", "error_message": "Vehicle connection timeout"}
deactivate Connector

Redis --> WSServer : Error event
WSServer -> WebApp : WS: {"event": "error", "error_message": "Vehicle connection timeout. Vehicle may be offline."}
WebApp -> Engineer : Display error notification\n"Command failed: Vehicle timeout. Please check vehicle connectivity."

@enduml
```

### Context: logging-monitoring (from 05_Operational_Architecture.md)

```markdown
**Logging Strategy: Structured Logging with Correlation**

**Framework:** `structlog` (Python) for structured, JSON-formatted logs

**Log Levels:**
- **DEBUG**: Detailed diagnostic info (disabled in production)
- **INFO**: General informational messages (command execution, API calls)
- **WARNING**: Unexpected but handled situations (vehicle timeout, retry attempts)
- **ERROR**: Errors requiring attention (failed commands, database errors)
- **CRITICAL**: System-level failures (database connection lost, service crash)

**Structured Log Format:**
{
  "timestamp": "2025-10-28T10:00:01.234Z",
  "level": "INFO",
  "logger": "sovd.command_service",
  "event": "command_executed",
  "correlation_id": "uuid",
  "user_id": "uuid",
  "vehicle_id": "uuid",
  "command_id": "uuid",
  "command_name": "ReadDTC",
  "duration_ms": 1234,
  "status": "completed"
}

**Correlation IDs:**
- Generated for each API request (X-Request-ID header)
- Propagated through all services (database queries, vehicle communication)
- Enables end-to-end request tracing in logs
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/connectors/vehicle_connector.py`
    *   **Summary:** This is the mock vehicle connector that simulates SOVD command execution. It already has **EXCELLENT** error simulation infrastructure in place! The file includes error probability constants (lines 28-31), error simulation logic (lines 350-395), and comprehensive error handling in the exception block (lines 527-599).
    *   **Recommendation:** **IMPORTANT - The error simulation logic is ALREADY IMPLEMENTED!** Lines 350-395 contain all three error scenarios: timeout (10%, line 352-360), unreachable (5%, line 362-368), and malformed response (3%, line 370-395). The timeout handling, error event publishing to Redis (lines 550-569), database status updates (lines 536-548), and audit logging (lines 572-592) are ALL already complete. **Your task is NOT to implement these from scratch, but to VERIFY they work correctly, ADD THE SEQUENCE DIAGRAM, and CREATE COMPREHENSIVE INTEGRATION TESTS.**
    *   **Critical Detail:** The timeout simulation uses `await asyncio.sleep(COMMAND_TIMEOUT_SECONDS + 1)` on line 359, then raises `TimeoutError`. The error handling block (lines 527-599) catches all exceptions, updates command status to `failed`, saves `error_message` (line 546), publishes error events to Redis (lines 551-569), and creates audit logs with `action="command_failed"` (lines 578-592).

*   **File:** `backend/app/services/command_service.py`
    *   **Summary:** This is the command service that handles command submission and lifecycle management. It validates vehicles (line 54), validates SOVD commands (lines 64-72), creates command records (lines 75-86), and triggers async execution via background tasks (lines 90-96).
    *   **Recommendation:** This service is already correctly implemented for error handling. It delegates all error scenarios to the vehicle connector's exception handling. **You do NOT need to modify this file** - the connector's try/except block handles all errors gracefully and updates the command status.
    *   **Note:** The command model (line 28-42) already has the `error_message` field (see command.py below), so no schema changes are needed.

*   **File:** `backend/app/models/command.py`
    *   **Summary:** The Command model with all necessary fields for tracking command lifecycle and errors.
    *   **Critical Fields:**
        - `status` (line 61-63): String field with server default `'pending'`, can be updated to `'in_progress'`, `'completed'`, or `'failed'`
        - `error_message` (line 64): Nullable Text field for storing error descriptions
        - `completed_at` (line 68): Nullable DateTime for tracking when command finished (successful or failed)
    *   **Recommendation:** **No changes needed.** The model already has the `error_message` field that the vehicle connector populates on failures (line 546 in vehicle_connector.py).

*   **File:** `backend/app/services/websocket_manager.py`
    *   **Summary:** WebSocket connection manager that tracks active connections by command_id and supports broadcasting.
    *   **Recommendation:** This is used by the WebSocket endpoint to push error events to clients. The vehicle connector already publishes error events to Redis (lines 551-569 in vehicle_connector.py), which the WebSocket server will consume and broadcast. **No changes needed here.**

### Implementation Tips & Notes

*   **Tip #1 - Error Simulation is Already Complete:** The vehicle connector (vehicle_connector.py) already implements all three error scenarios with the correct probabilities. Lines 350-395 contain:
    - **Timeout (10%)**: Lines 352-360 - Sleeps for 31 seconds, then raises `TimeoutError("Vehicle connection timeout")`
    - **Unreachable (5%)**: Lines 362-368 - Immediately raises `ConnectionError("Vehicle unreachable")`
    - **Malformed (3%)**: Lines 370-395 - Publishes invalid JSON to Redis, then raises `ValueError("Invalid response format from vehicle")`

*   **Tip #2 - Error Handling Flow is Already Implemented:** The exception block (lines 527-599) in `execute_command()` handles all errors comprehensively:
    1. Logs error with structlog (lines 528-533)
    2. Updates command status to `'failed'` with `error_message` (lines 536-548)
    3. Publishes Redis error event with correct format: `{"event": "error", "command_id": "...", "error_message": "..."}` (lines 551-569)
    4. Creates audit log with `action="command_failed"` (lines 572-592)

*   **Tip #3 - Create the Sequence Diagram:** You need to create `docs/diagrams/sequence_error_flow.puml`. Use the PlantUML code provided in the architecture context (Section error-handling-flow) as your template. The diagram must show the timeout flow from command submission through error handling to WebSocket delivery.

*   **Tip #4 - Integration Tests are the Main Deliverable:** Create `backend/tests/integration/test_error_scenarios.py` with comprehensive tests. **CRITICAL REQUIREMENT:** The acceptance criteria states "Tests use mock timing (don't wait full 30 seconds, use time mocking)". You MUST use `unittest.mock.patch` or similar to mock `asyncio.sleep` to avoid 30-second waits in tests. Test all three error scenarios (timeout, unreachable, malformed), verify database updates, Redis event publishing, and audit log creation.

*   **Tip #5 - Existing Test Infrastructure:** Check `backend/tests/integration/conftest.py` for test fixtures. You can reference `test_websocket.py` and `test_command_api.py` for examples of how to structure integration tests with database sessions and Redis mocking.

*   **Note #6 - Redis Event Format:** The error event format is already correct (lines 554-559): `{"event": "error", "command_id": "...", "error_message": "...", "failed_at": "..."}`. The WebSocket protocol documentation (in context above) confirms this is the expected format.

*   **Warning:** DO NOT remove or break the existing error simulation logic in vehicle_connector.py. The error probabilities are configurable via module-level constants (lines 28-31). Your integration tests should verify that these scenarios work as implemented, not replace them.

*   **Best Practice:** Use `structlog.get_logger(__name__)` for all logging (see line 24 in vehicle_connector.py as example). Log at WARNING level for simulated errors (already done on lines 354, 364, 376), and ERROR level for unexpected failures (line 528).

---

## 4. Additional Recommendations

### Integration Test Structure

Your `test_error_scenarios.py` should include at minimum:

1. **Test Timeout Scenario** (`test_command_timeout_scenario`):
   - Mock `asyncio.sleep` to return immediately instead of waiting 30+ seconds
   - Submit a command, ensure error simulation triggers timeout (may need to mock `random.random()` to force timeout)
   - Verify command status updated to `'failed'` with `error_message = "Vehicle connection timeout"`
   - Verify Redis error event published to channel `response:{command_id}`
   - Verify audit log created with `action="command_failed"`

2. **Test Unreachable Scenario** (`test_command_unreachable_scenario`):
   - Similar structure but mock to trigger unreachable error (5% probability)
   - Verify `ConnectionError` handled correctly
   - Verify error_message = "Vehicle unreachable"

3. **Test Malformed Response** (`test_command_malformed_response_scenario`):
   - Mock to trigger malformed response (3% probability)
   - Verify malformed JSON published to Redis (line 384)
   - Verify `ValueError` raised and handled
   - Verify error_message = "Invalid response format from vehicle"

4. **Test WebSocket Error Event Delivery** (Optional but recommended):
   - Establish WebSocket connection for command
   - Trigger timeout error
   - Verify WebSocket client receives: `{"event": "error", "command_id": "...", "error_message": "..."}`

### PlantUML Diagram Requirements

Create `docs/diagrams/sequence_error_flow.puml` with:
- Title: "Error Handling Flow - Vehicle Timeout"
- Actors: Engineer, WebApp, AppServer, Connector, Redis, WSServer, DB, Vehicle
- Show 30-second timeout with note: `... 30 seconds pass with no response ...`
- Show all error handling steps: DB update, audit log, Redis publish
- Use the template provided in the architecture context as a starting point
- Ensure diagram compiles with PlantUML (test with `plantuml -testdot` or online renderer)

### Acceptance Criteria Checklist

Use this to verify your implementation meets all requirements:

- [ ] ~10% of commands simulate timeout (configurable via ERROR_PROBABILITY_TIMEOUT constant) - **ALREADY DONE**
- [ ] Timeout commands update to status=`failed` after 30 seconds - **ALREADY DONE**
- [ ] Error message saved in command.error_message field - **ALREADY DONE**
- [ ] WebSocket clients receive error event: `{"event": "error", "error_message": "..."}` - **ALREADY DONE**
- [ ] Audit log created for failed commands (action=`command_failed`) - **ALREADY DONE**
- [ ] `sequence_error_flow.puml` compiles and shows timeout flow - **TODO: CREATE DIAGRAM**
- [ ] Integration tests verify timeout behavior - **TODO: CREATE TESTS**
- [ ] Integration tests verify error event delivery - **TODO: CREATE TESTS**
- [ ] Integration tests verify command status update - **TODO: CREATE TESTS**
- [ ] Tests use mock timing (don't wait full 30 seconds) - **TODO: IMPLEMENT MOCKING**
- [ ] No linter errors (`ruff check`, `mypy`, `black --check`) - **TODO: VERIFY**

---

**END OF BRIEFING PACKAGE**
