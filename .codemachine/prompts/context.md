# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I3.T7",
  "iteration_id": "I3",
  "iteration_goal": "Real-Time WebSocket Communication & Frontend Foundation",
  "description": "Create response viewer component `src/components/commands/ResponseViewer.tsx` that connects to WebSocket endpoint and displays real-time responses. Implement: 1) WebSocket client `src/api/websocket.ts` that connects to `/ws/responses/{command_id}?token={jwt}`, 2) Component receives command_id as prop, 3) On mount, establish WebSocket connection, 4) Listen for events: `response` (append to response list), `status` (update command status indicator), `error` (display error message), 5) Display responses in scrollable list (newest at bottom, auto-scroll), 6) Format response payload as JSON with syntax highlighting (use library like react-json-view), 7) Show connection status indicator (connected/disconnected), 8) Handle connection errors gracefully (retry with exponential backoff), 9) Clean up WebSocket connection on unmount. Integrate into CommandPage or create dedicated ResponsePage. Write component tests in `frontend/tests/components/ResponseViewer.test.tsx` using mock WebSocket.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Architecture Blueprint Section 3.7 (WebSocket Protocol); WebSocket implementation from I3.T1.",
  "target_files": [
    "frontend/src/components/commands/ResponseViewer.tsx",
    "frontend/src/api/websocket.ts",
    "frontend/src/pages/ResponsePage.tsx",
    "frontend/tests/components/ResponseViewer.test.tsx"
  ],
  "input_files": [
    "frontend/src/context/AuthContext.tsx"
  ],
  "deliverables": "WebSocket client module; response viewer component with real-time updates; connection status indicator; component tests.",
  "acceptance_criteria": "Response viewer component connects to WebSocket on mount; JWT token included in WebSocket connection query parameter; Responses appear in real-time as they're received (verify by submitting ReadDTC command and seeing DTC chunks appear sequentially); Response payload displayed as formatted JSON (syntax highlighting); Command status updates when final response received (e.g., \"Completed\" badge); Error events displayed prominently (red alert/banner); Connection status indicator shows \"Connected\" when active, \"Disconnected\" on close; Auto-scrolls to newest response; WebSocket closed and cleaned up on component unmount (verify no memory leak); Component tests verify: connection establishment, event handling, error scenarios; No console errors (except expected WebSocket close on unmount); No linter errors",
  "dependencies": ["I3.T1", "I3.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents.

### Context: WebSocket Protocol Specification

**WebSocket Endpoint**: `/ws/responses/{command_id}`

**Connection URL**: `ws://localhost:8000/ws/responses/{command_id}?token={jwt}`

**Protocol Flow** (from backend/app/api/v1/websocket.py):
1. Client connects with JWT token in query parameter
2. Server validates token and accepts connection (or closes with WS_1008_POLICY_VIOLATION)
3. Server subscribes to Redis Pub/Sub channel: `response:{command_id}`
4. Server forwards all events from Redis to WebSocket client
5. Connection closes when command completes, error occurs, or client disconnects

**Event Types** sent to client (JSON messages):

1. **Response Event** (streaming data chunks):
   ```json
   {
     "event": "response",
     "command_id": "uuid-string",
     "response": {
       "dtcCode": "P0420",
       "description": "Catalyst System Efficiency Below Threshold"
     },
     "sequence_number": 1
   }
   ```

2. **Status Event** (command completion):
   ```json
   {
     "event": "status",
     "command_id": "uuid-string",
     "status": "completed",
     "completed_at": "2025-10-28T12:34:56Z"
   }
   ```

3. **Error Event** (execution failure):
   ```json
   {
     "event": "error",
     "command_id": "uuid-string",
     "error_message": "Vehicle connection timeout"
   }
   ```

### Context: Backend WebSocket Implementation Details

From **backend/app/api/v1/websocket.py** (lines 238-366):

**Authentication**:
- JWT token passed via query parameter `?token={jwt}`
- Server validates token and fetches user from database
- Rejects with WS_1008_POLICY_VIOLATION if token missing, invalid, or user inactive
- Logs all auth events with structlog

**Connection Lifecycle**:
- Server accepts WebSocket connection first (line 277)
- Authenticates user (lines 286-289)
- Registers connection with websocket_manager (line 299)
- Creates Redis client for Pub/Sub (lines 302-304)
- Spawns two async tasks (lines 310-315):
  - `redis_listener`: Listens to Redis and forwards events to client
  - `websocket_receiver`: Detects client disconnection
- Uses `asyncio.wait` with FIRST_COMPLETED to handle either task finishing
- Cleanup: unsubscribes from Redis, closes connections, logs closure

**Event Processing** (redis_listener, lines 135-170):
- Subscribes to channel `response:{command_id}`
- Parses JSON messages from Redis
- Forwards to WebSocket client via `websocket.send_json(event_data)`
- Auto-stops listening after "status:completed" or "error" events
- Handles JSON decode errors and WebSocket send failures

### Context: Response Data Format

From **backend/app/schemas/response.py**:

**ResponseDetail Schema**:
```python
response_id: UUID
command_id: UUID
response_payload: dict[str, Any]  # Arbitrary JSON data from vehicle
sequence_number: int              # Incrementing number for ordering
is_final: bool                    # True for last chunk
received_at: datetime
```

**Mock Vehicle Response Examples** (from connector):
- **ReadDTC**: `{"dtcCode": "P0420", "description": "..."}`
- **ClearDTC**: `{"success": true, "cleared_count": 2}`
- **ReadDataByID**: `{"dataId": "0x1234", "value": "..."}`

Responses are streamed in 2-3 chunks with ~0.5s intervals between chunks.

### Context: Frontend Authentication Integration

From **frontend/src/context/AuthContext.tsx**:

**Token Management**:
- Access token stored in memory (via `setAccessToken()` in api/client.ts)
- Access token retrievable via `getAccessToken()` export
- JWT expires in 15 minutes, auto-refreshes on 401

**Usage Pattern**:
```typescript
import { getAccessToken } from '../api/client';

// In component
const token = getAccessToken();
const wsUrl = `ws://localhost:8000/ws/responses/${commandId}?token=${token}`;
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/api/v1/websocket.py` (lines 238-366)
    *   **Summary:** Complete WebSocket server implementation with JWT auth, Redis Pub/Sub integration, dual-task async coordination, and comprehensive error handling.
    *   **Recommendation:** Study lines 135-170 (redis_listener) to understand the exact event format you'll receive. Note that events are already JSON-parsed objects when sent via `websocket.send_json()`.
    *   **Key Insight:** WebSocket closes automatically after receiving "status:completed" or "error" event. Your client MUST handle this graceful closure.

*   **File:** `frontend/src/api/client.ts` (lines 55-61)
    *   **Summary:** Exports `getAccessToken()` function to retrieve current JWT from memory.
    *   **Recommendation:** You MUST use this function to get the token for WebSocket authentication. DO NOT access localStorage directly.
    *   **Example:**
        ```typescript
        import { getAccessToken } from '../api/client';
        const token = getAccessToken();
        ```

*   **File:** `frontend/src/context/AuthContext.tsx` (lines 122-140)
    *   **Summary:** Provides authentication state via `useAuth()` hook.
    *   **Recommendation:** You CAN use `const { isAuthenticated } = useAuth()` to check auth state before connecting, but getting the actual token requires `getAccessToken()` from api/client.ts.

*   **File:** `frontend/src/pages/VehiclesPage.tsx` (lines 1-110)
    *   **Summary:** Example page component using React Query, useState, MUI components, and child component integration.
    *   **Recommendation:** Use this as your TEMPLATE for ResponsePage.tsx structure:
        - React Query for initial data fetching (command details)
        - useState for component state (connection status, responses)
        - MUI Container, Paper, Typography for layout
        - Pass props to child component (ResponseViewer)

*   **File:** `frontend/src/components/vehicles/VehicleList.tsx` (lines 1-100)
    *   **Summary:** Presentational component with loading/error/empty states, TypeScript interface for props, MUI components.
    *   **Recommendation:** Follow this PATTERN for ResponseViewer:
        - Clear TypeScript interface for props (commandId, onStatusChange?, etc.)
        - Separate handling of loading, error, empty states
        - Consistent MUI component usage (Box, Typography, Alert, Chip)

*   **File:** `frontend/src/types/command.ts` (lines 49-63)
    *   **Summary:** TypeScript interfaces matching backend schemas. CommandResponse includes command_id, status, etc.
    *   **Recommendation:** Create `frontend/src/types/response.ts` for WebSocket event types. Define interfaces for ResponseEvent, StatusEvent, ErrorEvent matching the JSON formats documented in Section 2.

*   **File:** `frontend/src/pages/CommandPage.tsx` (lines 1-141)
    *   **Summary:** Complete page with vehicle selector, command form, React Query mutation, success/error handling.
    *   **Recommendation:** You will need to MODIFY this file to integrate ResponseViewer. After successful command submission (line 32-34), either:
        - Option A: Navigate to ResponsePage with command_id
        - Option B: Show ResponseViewer inline on same page

*   **File:** `frontend/package.json`
    *   **Summary:** Current dependencies include React 18, MUI 5, React Query, axios.
    *   **Recommendation:** You MUST install `react-json-view` for JSON syntax highlighting:
        ```bash
        cd frontend && npm install react-json-view
        ```
    *   **Note:** Check if @types/react-json-view is needed (may be bundled).

### Implementation Tips & Notes

*   **CRITICAL - Missing Dependency:** The task requires `react-json-view` for JSON formatting. You MUST install it:
    ```bash
    cd frontend && npm install react-json-view @types/react-json-view
    ```

*   **Tip - WebSocket Base URL:** Use environment variable or derive from API base URL:
    ```typescript
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const WS_BASE_URL = API_BASE_URL.replace('http', 'ws'); // ws://localhost:8000
    ```

*   **Tip - Auto-Scroll Implementation:** Use a ref to scroll to bottom when new responses arrive:
    ```typescript
    const responseEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      responseEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [responses]);
    ```

*   **Tip - Reconnection with Exponential Backoff:** Implement retry logic:
    ```typescript
    const [retryCount, setRetryCount] = useState(0);
    const delay = Math.min(1000 * Math.pow(2, retryCount), 30000); // Max 30s

    setTimeout(() => connectWebSocket(), delay);
    ```
    Limit retries to 5 attempts to avoid infinite loops.

*   **Tip - Connection Status State:** Use enum for clarity:
    ```typescript
    type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
    ```

*   **Tip - Event Type Discrimination:** Use type guards for event handling:
    ```typescript
    interface ResponseEvent { event: 'response'; command_id: string; response: any; sequence_number: number; }
    interface StatusEvent { event: 'status'; command_id: string; status: string; completed_at?: string; }
    interface ErrorEvent { event: 'error'; command_id: string; error_message: string; }
    type WebSocketEvent = ResponseEvent | StatusEvent | ErrorEvent;

    const handleMessage = (event: WebSocketEvent) => {
      if (event.event === 'response') { /* ... */ }
      else if (event.event === 'status') { /* ... */ }
      else if (event.event === 'error') { /* ... */ }
    };
    ```

*   **Tip - Cleanup on Unmount:** Use useEffect cleanup function:
    ```typescript
    useEffect(() => {
      const ws = connectWebSocket();
      return () => {
        ws?.close();
      };
    }, [commandId]);
    ```

*   **Warning - WebSocket Close Events:** Normal closure (code 1000) is expected. Only log errors for unexpected codes (1006, 1008).

*   **Warning - Multiple Re-renders:** Be careful with state updates in WebSocket message handlers. Batch updates or use useReducer if state becomes complex.

*   **Note - react-json-view Usage:**
    ```typescript
    import ReactJson from 'react-json-view';

    <ReactJson
      src={response.response}
      theme="monokai"
      collapsed={false}
      displayDataTypes={false}
      displayObjectSize={false}
    />
    ```

*   **Note - Integration with CommandPage:** After successful command submission, you have two options:
    1. **Navigate to ResponsePage**: Use React Router navigate
    2. **Inline display**: Conditionally render ResponseViewer in CommandPage

    For MVP simplicity, I recommend Option 2 (inline).

*   **Note - Test Mocking Strategy:** For tests, mock WebSocket constructor:
    ```typescript
    const mockWebSocket = {
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    global.WebSocket = vi.fn(() => mockWebSocket) as any;
    ```

### Key Files You Will Create/Modify

1. **CREATE** `frontend/src/types/response.ts` - WebSocket event type definitions
2. **CREATE** `frontend/src/api/websocket.ts` - WebSocket client connection manager
3. **CREATE** `frontend/src/components/commands/ResponseViewer.tsx` - Main viewer component
4. **CREATE** `frontend/src/pages/ResponsePage.tsx` - Dedicated page for viewing responses
5. **MODIFY** `frontend/src/pages/CommandPage.tsx` - Integrate ResponseViewer after submission
6. **CREATE** `frontend/tests/components/ResponseViewer.test.tsx` - Component test suite
7. **MODIFY** `frontend/package.json` - Add react-json-view dependency

### Recommended Implementation Order

1. **Install dependencies**: `cd frontend && npm install react-json-view @types/react-json-view`
2. **Create** `frontend/src/types/response.ts` (event type definitions)
3. **Create** `frontend/src/api/websocket.ts` (connection logic with retry)
4. **Create** `frontend/src/components/commands/ResponseViewer.tsx` (component skeleton with connection status)
5. **Test WebSocket connection** (manual testing with browser console)
6. **Add event handling** (response/status/error events)
7. **Add response list rendering** (with react-json-view)
8. **Add auto-scroll** (ref-based scrolling)
9. **Add error handling and retry logic** (exponential backoff)
10. **Create** `frontend/src/pages/ResponsePage.tsx` (optional dedicated page)
11. **Modify** `frontend/src/pages/CommandPage.tsx` (integrate ResponseViewer)
12. **Create** `frontend/tests/components/ResponseViewer.test.tsx` (comprehensive tests)
13. **Manual E2E testing** (submit ReadDTC, verify streaming)

### Acceptance Criteria Checklist

- [ ] ResponseViewer component connects to WebSocket on mount
- [ ] JWT token included in WebSocket URL query parameter
- [ ] Responses appear in real-time (verify with ReadDTC command)
- [ ] Response payloads displayed as formatted JSON with syntax highlighting
- [ ] Command status updates when final response received (badge/chip indicator)
- [ ] Error events displayed prominently (MUI Alert with severity="error")
- [ ] Connection status indicator visible (Chip: green=connected, red=disconnected)
- [ ] Auto-scrolls to newest response
- [ ] WebSocket closed on component unmount (cleanup verified)
- [ ] Component tests verify: connection, event handling, errors
- [ ] No console errors (except expected close on unmount)
- [ ] No linter errors

### WebSocket Connection Example

Here's a reference implementation snippet for the WebSocket client:

```typescript
// src/api/websocket.ts
export const createWebSocketConnection = (
  commandId: string,
  token: string,
  onMessage: (event: WebSocketEvent) => void,
  onStatusChange: (status: ConnectionStatus) => void
): WebSocket => {
  const wsBaseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace('http', 'ws');
  const url = `${wsBaseUrl}/ws/responses/${commandId}?token=${token}`;

  const ws = new WebSocket(url);

  ws.onopen = () => {
    console.log('WebSocket connected:', commandId);
    onStatusChange('connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onStatusChange('error');
  };

  ws.onclose = (event) => {
    console.log('WebSocket closed:', event.code, event.reason);
    onStatusChange('disconnected');
  };

  return ws;
};
```

Good luck! Follow the patterns from VehicleList and CommandPage, and the implementation will be straightforward. The WebSocket server is fully functional and tested, so focus on client-side event handling and UI presentation.
