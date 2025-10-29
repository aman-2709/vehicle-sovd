# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T1",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Implement WebSocket endpoint in `backend/app/api/v1/websocket.py` at path `/ws/responses/{command_id}`. WebSocket connection requires JWT authentication via query parameter `?token={jwt}`. Implement connection lifecycle: 1) Validate JWT on connect (disconnect with error if invalid), 2) Subscribe to Redis Pub/Sub channel `response:{command_id}`, 3) Listen for response events from Redis, 4) Forward events to WebSocket client as JSON messages (format: `{\"event\": \"response\", \"command_id\": \"...\", \"response\": {...}}`), 5) Handle status change events (`{\"event\": \"status\", \"status\": \"completed\"}`), 6) Handle errors (`{\"event\": \"error\", \"error_message\": \"...\"}`), 7) Unsubscribe and close on client disconnect. Implement WebSocket connection manager in `backend/app/services/websocket_manager.py` to track active connections and handle broadcasting. Update mock vehicle connector (I2.T5) to publish response events to Redis channel. Write integration tests in `backend/tests/integration/test_websocket.py` using WebSocket test client.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.7 (WebSocket Protocol); Section 3.8 (Communication Patterns - Event-Driven Internal).",
  "target_files": [
    "backend/app/api/v1/websocket.py",
    "backend/app/services/websocket_manager.py",
    "backend/app/connectors/vehicle_connector.py",
    "backend/tests/integration/test_websocket.py"
  ],
  "input_files": [
    "backend/app/dependencies.py",
    "backend/app/connectors/vehicle_connector.py"
  ],
  "deliverables": "Functional WebSocket endpoint with JWT auth; Redis Pub/Sub integration; connection manager; integration tests.",
  "acceptance_criteria": "WebSocket client can connect to `ws://localhost:8000/ws/responses/{command_id}?token={valid_jwt}`; Connection rejected if JWT invalid or missing (WebSocket close with error code); After submitting command via REST API, WebSocket client receives response events in real-time; Response events match format: `{\"event\": \"response\", \"response\": {...}, \"sequence_number\": 1}`; Status event received when command completes: `{\"event\": \"status\", \"status\": \"completed\"}`; Multiple WebSocket clients can subscribe to same command (verify with 2 concurrent connections); Client disconnect unsubscribes from Redis (no memory leak); Integration tests verify: successful connection, event delivery, auth rejection; No errors in logs during WebSocket operations; No linter errors",
  "dependencies": [
    "I2.T1",
    "I2.T5"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: WebSocket Protocol (from 04_Behavior_and_Communication.md)

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

### Context: Asynchronous Streaming Pattern (from 04_Behavior_and_Communication.md)

```markdown
**2. Asynchronous Streaming (WebSocket)**

Used for:
- Real-time command execution status updates
- Streaming command responses (multi-part responses from vehicle)
- Live vehicle connection status notifications

**Flow:**
1. Client establishes WebSocket connection with auth token
2. Client subscribes to specific channels (e.g., command response stream)
3. Server pushes updates as they arrive from vehicle
4. Client renders updates progressively
5. Connection remains open for multiple commands

**Example:** WebSocket at `wss://api.sovd.example.com/ws/responses/{command_id}`
```

### Context: Event-Driven Internal Communication (from 04_Behavior_and_Communication.md)

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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/dependencies.py`
    *   **Summary:** This file contains JWT authentication logic with `get_current_user()` dependency that validates JWT tokens and retrieves user records from the database. It uses FastAPI's `HTTPBearer` security scheme.
    *   **Recommendation:** You CANNOT directly use the existing `get_current_user()` dependency for WebSocket authentication because it expects tokens in the `Authorization` header, but WebSockets pass tokens via query parameters. You MUST create a new authentication function specifically for WebSocket that:
        1. Extracts the token from the query parameter `?token={jwt}`
        2. Calls the existing `verify_access_token()` function from `app.services.auth_service`
        3. Validates the user_id and fetches the user from the database
        4. Returns the User object or raises a WebSocket exception
    *   **Warning:** The existing `get_current_user()` dependency uses `HTTPAuthorizationCredentials` which won't work for WebSocket connections. You need to implement custom authentication logic.

*   **File:** `backend/app/connectors/vehicle_connector.py`
    *   **Summary:** This file already implements the mock vehicle connector with Redis publishing functionality. The `execute_command()` function publishes response events to Redis Pub/Sub on the channel `response:{command_id}` at line 233-243.
    *   **Recommendation:** The vehicle connector is ALREADY publishing events to Redis correctly. You DO NOT need to modify it for basic functionality. The event format includes:
        ```python
        {
            "event": "response",
            "command_id": str(command_id),
            "response_id": str(response.response_id),
            "response_payload": response_payload,
            "sequence_number": 1,
            "is_final": True,
        }
        ```
    *   **Note:** At line 254-263, the connector also updates command status to "completed". You MAY want to publish a status event to Redis here as well for the WebSocket to pick up and forward to clients.

*   **File:** `backend/app/config.py`
    *   **Summary:** Configuration module using Pydantic Settings. Contains `REDIS_URL`, `DATABASE_URL`, `JWT_SECRET`, and other settings.
    *   **Recommendation:** You MUST import `settings` from this module to access the Redis URL: `from app.config import settings`. Use `settings.REDIS_URL` when creating Redis connections.

*   **File:** `backend/app/main.py`
    *   **Summary:** FastAPI application entry point. Currently includes REST API routers for auth, vehicles, and commands (lines 46-48). Uses CORS middleware and logging middleware.
    *   **Recommendation:** You MUST register your WebSocket router in this file. Add the following after line 48:
        ```python
        from app.api.v1 import websocket
        app.include_router(websocket.router, tags=["websocket"])
        ```
    *   **Note:** WebSocket endpoints don't use the `/api/v1` prefix by convention. The endpoint should be at `/ws/responses/{command_id}`.

*   **File:** `backend/tests/conftest.py`
    *   **Summary:** Pytest configuration with fixtures for database sessions and async HTTP client. Uses SQLite for testing and mocks the audit service.
    *   **Recommendation:** You SHOULD reuse the existing `async_client` fixture pattern for WebSocket tests. However, for WebSocket testing, you'll need to use httpx's WebSocket support or FastAPI's `TestClient` with WebSocket mode.
    *   **Tip:** The `async_client` fixture already sets up dependency overrides for the database. You can extend this pattern for WebSocket tests.

*   **File:** `backend/requirements.txt`
    *   **Summary:** Contains all required dependencies including `redis>=5.0.0`, `fastapi>=0.104.0`, and `structlog>=23.2.0`.
    *   **Recommendation:** FastAPI 0.104.0+ includes native WebSocket support. You SHOULD use `from fastapi import WebSocket, WebSocketDisconnect` for WebSocket handling. You do NOT need to install additional libraries.
    *   **Note:** For Redis async support, use `redis.asyncio` module: `import redis.asyncio as redis`. This is already available with the `redis>=5.0.0` package.

### Implementation Tips & Notes

*   **Tip: WebSocket Authentication Pattern**
    ```python
    from fastapi import WebSocket, WebSocketDisconnect, status
    from app.services.auth_service import verify_access_token
    from app.repositories.user_repository import get_user_by_id

    async def authenticate_websocket(websocket: WebSocket, token: str | None, db: AsyncSession) -> User | None:
        """Authenticate WebSocket connection using JWT from query parameter."""
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        payload = verify_access_token(token)
        if not payload:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        user_id = uuid.UUID(payload.get("user_id"))
        user = await get_user_by_id(db, user_id)
        if not user or not user.is_active:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None

        return user
    ```

*   **Tip: Redis Pub/Sub Pattern**
    The Redis async client supports pub/sub with `pubsub()` method. Here's the recommended pattern:
    ```python
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"response:{command_id}")

    async for message in pubsub.listen():
        if message["type"] == "message":
            data = json.loads(message["data"])
            # Forward to WebSocket client
            await websocket.send_json(data)

    # Cleanup
    await pubsub.unsubscribe(f"response:{command_id}")
    await pubsub.close()
    await redis_client.close()
    ```

*   **Tip: WebSocket Connection Manager Pattern**
    You need to implement a connection manager to track active WebSocket connections. The manager should:
    1. Store connections in a dictionary keyed by `command_id`
    2. Support multiple clients subscribing to the same command
    3. Handle broadcasting events to all subscribed clients
    4. Clean up connections on disconnect

    Example structure:
    ```python
    class WebSocketManager:
        def __init__(self):
            self.active_connections: dict[str, list[WebSocket]] = {}

        async def connect(self, command_id: str, websocket: WebSocket):
            if command_id not in self.active_connections:
                self.active_connections[command_id] = []
            self.active_connections[command_id].append(websocket)

        async def disconnect(self, command_id: str, websocket: WebSocket):
            if command_id in self.active_connections:
                self.active_connections[command_id].remove(websocket)
                if not self.active_connections[command_id]:
                    del self.active_connections[command_id]

        async def broadcast(self, command_id: str, message: dict):
            if command_id in self.active_connections:
                for connection in self.active_connections[command_id]:
                    await connection.send_json(message)
    ```

*   **Tip: Structured Logging for WebSocket Events**
    The project uses `structlog` for logging. You SHOULD log key WebSocket events with structured context:
    ```python
    logger.info(
        "websocket_connection_established",
        command_id=str(command_id),
        user_id=str(user.user_id),
        username=user.username
    )
    ```

*   **Warning: Concurrent Task Handling**
    You'll need to handle two concurrent async tasks:
    1. Listening for Redis Pub/Sub messages
    2. Handling WebSocket disconnection (waiting for `WebSocketDisconnect`)

    Use `asyncio.create_task()` and `asyncio.gather()` or `asyncio.wait()` with `FIRST_COMPLETED` to handle both:
    ```python
    async def redis_listener():
        async for message in pubsub.listen():
            # Forward to WebSocket
            pass

    async def websocket_handler():
        try:
            while True:
                # This will raise WebSocketDisconnect when client disconnects
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    # Run both tasks concurrently
    await asyncio.gather(
        redis_listener(),
        websocket_handler()
    )
    ```

*   **Warning: Memory Leak Prevention**
    You MUST ensure proper cleanup of Redis connections when WebSocket disconnects. Use try/finally blocks:
    ```python
    try:
        # WebSocket and Redis logic
        pass
    finally:
        # Always cleanup
        await pubsub.unsubscribe(f"response:{command_id}")
        await pubsub.close()
        await redis_client.close()
        await manager.disconnect(command_id, websocket)
    ```

*   **Note: Status Event Publishing**
    Currently, the vehicle connector does NOT publish a status event when command completes (only response events). You have TWO options:
    1. **Recommended:** Modify `vehicle_connector.py` to publish a status event after updating command status (around line 263)
    2. **Alternative:** Have the WebSocket server query the database periodically to check status

    Option 1 is cleaner and more real-time. Add this after line 263:
    ```python
    # Publish status event to Redis
    status_event = {
        "event": "status",
        "command_id": str(command_id),
        "status": "completed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    await redis_client.publish(channel, json.dumps(status_event))
    ```

*   **Note: Testing Pattern**
    For WebSocket integration tests, use FastAPI's TestClient with WebSocket support:
    ```python
    from fastapi.testclient import TestClient

    def test_websocket_connection():
        with TestClient(app) as client:
            with client.websocket_connect(f"/ws/responses/{command_id}?token={valid_jwt}") as websocket:
                data = websocket.receive_json()
                assert data["event"] == "response"
    ```

*   **Tip: Error Event Format**
    When errors occur (timeout, vehicle unreachable, etc.), publish error events to Redis:
    ```python
    error_event = {
        "event": "error",
        "command_id": str(command_id),
        "error_message": "Vehicle connection timeout"
    }
    ```

### Project Conventions

*   **Logging:** Use `structlog` with structured fields. Import: `import structlog; logger = structlog.get_logger(__name__)`
*   **Type Hints:** Use Python 3.10+ type hints. Use `uuid.UUID` for UUIDs, `dict[str, Any]` for JSON objects
*   **Async/Await:** All database and I/O operations MUST be async. Use `async def` and `await`
*   **Error Handling:** Use try/except blocks with proper logging. Always include `exc_info=True` for exceptions
*   **Code Quality:** Code must pass `ruff check` and `mypy` (strict mode). No linting errors allowed
*   **Test Coverage:** Maintain ≥80% test coverage. Use pytest with pytest-asyncio

### Files to Create/Modify

1. **CREATE:** `backend/app/api/v1/websocket.py` - Main WebSocket endpoint implementation
2. **CREATE:** `backend/app/services/websocket_manager.py` - Connection manager service
3. **MODIFY:** `backend/app/connectors/vehicle_connector.py` - Add status event publishing (optional but recommended)
4. **MODIFY:** `backend/app/main.py` - Register WebSocket router
5. **CREATE:** `backend/tests/integration/test_websocket.py` - Comprehensive integration tests
