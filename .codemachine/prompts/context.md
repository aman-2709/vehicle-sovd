# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T2",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Integrate Prometheus metrics into backend using prometheus-fastapi-instrumentator. Add custom metrics: commands_executed_total, command_execution_duration_seconds, websocket_connections_active, vehicle_connections_active. Expose /metrics endpoint. Add Prometheus to docker-compose.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Monitoring - Metrics).",
  "target_files": [
    "backend/app/utils/metrics.py",
    "backend/app/main.py",
    "backend/app/services/command_service.py",
    "infrastructure/docker/prometheus.yml",
    "docker-compose.yml",
    "README.md"
  ],
  "input_files": [
    "backend/app/main.py",
    "backend/app/services/command_service.py",
    "backend/app/services/websocket_manager.py"
  ],
  "deliverables": "Prometheus metrics exporter with custom SOVD metrics; Prometheus server in docker-compose; documentation.",
  "acceptance_criteria": "GET /metrics returns Prometheus metrics; HTTP and custom metrics present; Metrics update correctly; Prometheus accessible at :9090; Successfully scrapes backend; README documents access; No errors",
  "dependencies": ["I2.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Logging & Monitoring (from 05_Operational_Architecture.md)

<!-- anchor: logging-monitoring -->
#### Logging & Monitoring

<!-- anchor: logging-strategy -->
**Logging Strategy: Structured Logging with Correlation**

**Framework:** `structlog` (Python) for structured, JSON-formatted logs

**Log Levels:**
- **DEBUG**: Detailed diagnostic info (disabled in production)
- **INFO**: General informational messages (command execution, API calls)
- **WARNING**: Unexpected but handled situations (vehicle timeout, retry attempts)
- **ERROR**: Errors requiring attention (failed commands, database errors)
- **CRITICAL**: System-level failures (database connection lost, service crash)

**Structured Log Format:**
```json
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
```

**Correlation IDs:**
- Generated for each API request (X-Request-ID header)
- Propagated through all services (database queries, vehicle communication)
- Enables end-to-end request tracing in logs

**Log Destinations:**
- **Development**: Console output (pretty-printed for readability)
- **Production**:
  - AWS CloudWatch Logs (primary, searchable, alerting)
  - ELK Stack (Elasticsearch, Logstash, Kibana) for advanced analytics (optional)

**Log Retention:**
- Application logs: 30 days
- Audit logs: 7 years (compliance requirement for automotive industry)

<!-- anchor: monitoring-strategy -->
**Monitoring Strategy: Metrics & Alerting**

**Metrics Framework:** Prometheus (time-series database)

**Key Metrics Collected:**

**Application Metrics:**
- `http_requests_total{method, endpoint, status}`: Counter of HTTP requests
- `http_request_duration_seconds{method, endpoint}`: Histogram of request latency
- `websocket_connections_active`: Gauge of active WebSocket connections
- `commands_executed_total{status}`: Counter of commands (completed, failed)
- `command_execution_duration_seconds`: Histogram of command round-trip time
- `vehicle_connections_active`: Gauge of connected vehicles
- `response_size_bytes`: Histogram of response payload sizes

**System Metrics:**
- CPU utilization, memory usage (via node-exporter)
- Database connections (active, idle, max)
- Redis connections and memory usage

**Custom Metrics:**
- `sovd_command_timeout_total`: Counter of vehicle timeouts
- `sovd_response_chunks_total`: Counter of streaming response chunks
- `sovd_authentication_failures_total`: Counter of failed logins

**Alerting Rules (Prometheus Alertmanager):**
- Command success rate < 90% over 5 minutes → Page on-call engineer
- 95th percentile response time > 3 seconds → Slack notification
- Database connection pool exhaustion → Page on-call
- Vehicle connection drop > 20% in 5 minutes → Email alert

**Dashboards (Grafana):**
- **Operations Dashboard**: Request rate, error rate, latency (RED metrics)
- **Command Dashboard**: Commands/minute, success rate, avg execution time
- **Vehicle Dashboard**: Active connections, connection stability, command distribution
- **System Health Dashboard**: CPU, memory, disk, network

### Context: NFR Maintainability (from 01_Context_and_Drivers.md)

<!-- anchor: nfr-maintainability -->
#### Maintainability
- **Code Quality**: 80%+ test coverage, automated linting and formatting
- **Documentation**: OpenAPI/Swagger for APIs, inline code documentation
- **Modularity**: Clear separation of concerns, loosely coupled components
- **Observability**: Structured logging, distributed tracing, metrics collection

**Architectural Impact**: Layered architecture, dependency injection, standardized logging framework, observability stack (e.g., ELK or equivalent).

### Context: Task I4.T2 Specification (from 02_Iteration_I4.md)

<!-- anchor: task-i4-t2 -->
**Task 4.2: Implement Prometheus Metrics Exporter**

**Task ID:** `I4.T2`

**Description:** Integrate Prometheus metrics into backend application. Use `prometheus-fastapi-instrumentator` library to automatically instrument FastAPI app with HTTP metrics (request count, duration, status codes). Add custom metrics in `backend/app/utils/metrics.py`:
1. `commands_executed_total{status}` (Counter for commands by status)
2. `command_execution_duration_seconds` (Histogram for command round-trip time)
3. `websocket_connections_active` (Gauge for active WebSocket connections)
4. `vehicle_connections_active` (Gauge for connected vehicles)
5. `sovd_command_timeout_total` (Counter for vehicle timeouts)

Increment counters and update gauges in appropriate services (command_service, websocket_manager, vehicle_service). Expose metrics at `/metrics` endpoint (Prometheus scrape target). Configure Prometheus server in `infrastructure/docker/prometheus.yml` (scrape config for backend:8000/metrics). Add Prometheus to docker-compose.yml (service: `prometheus`, image: `prom/prometheus`, port 9090, volume mount for prometheus.yml). Write README documentation for accessing metrics.

**Acceptance Criteria:**
- `GET http://localhost:8000/metrics` returns Prometheus-formatted metrics
- HTTP metrics present: `http_requests_total`, `http_request_duration_seconds`
- Custom metrics present: `commands_executed_total`, `command_execution_duration_seconds`, `websocket_connections_active`
- Metrics update correctly: submitting command increments `commands_executed_total{status="completed"}`
- Prometheus server accessible at `http://localhost:9090`
- Prometheus successfully scrapes backend metrics (verify in Prometheus UI: Status → Targets)
- Metrics queryable in Prometheus UI (e.g., query `commands_executed_total`)
- README includes instructions for accessing Prometheus and example queries
- No errors in Prometheus logs
- No linter errors

**Dependencies:** `I2` (backend services to instrument)

**Parallelizable:** Yes (monitoring infrastructure independent of features)

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/app/utils/metrics.py`
**Summary:** This file already exists and contains the complete implementation of custom Prometheus metrics! It defines all required metrics using `prometheus_client`:
- `commands_executed_total` - Counter with status label
- `command_execution_duration_seconds` - Histogram with pre-configured buckets
- `websocket_connections_active` - Gauge for WebSocket connections
- `vehicle_connections_active` - Gauge for vehicle connections

**Recommendation:** You DO NOT need to create this file or add metrics definitions. The metrics are already defined and ready to use. Helper functions are also implemented: `increment_command_counter()`, `observe_command_duration()`, `increment_websocket_connections()`, `decrement_websocket_connections()`, `set_vehicle_connections()`.

**WARNING:** The task description mentions adding `sovd_command_timeout_total` but this metric is NOT currently defined in the file. You SHOULD add this counter metric following the same pattern as the existing metrics.

#### File: `backend/app/main.py`
**Summary:** The main FastAPI application entry point. It already includes Prometheus instrumentation setup on lines 52-54:
```python
# Setup Prometheus instrumentation
# This automatically creates metrics for HTTP requests and exposes /metrics endpoint
Instrumentator().instrument(app).expose(app)
```

**Recommendation:** The Prometheus FastAPI instrumentator is already configured and the `/metrics` endpoint is already exposed! You DO NOT need to add this code again. The HTTP metrics (`http_requests_total`, `http_request_duration_seconds`) are automatically generated by this library.

**Status:** Lines 16 imports `prometheus_fastapi_instrumentator`, line 54 instruments the app, and line 100 documents the metrics endpoint. This task requirement is ALREADY COMPLETE.

#### File: `backend/requirements.txt`
**Summary:** Python dependencies file. Line 32 shows:
```
prometheus-fastapi-instrumentator>=6.1.0
```

**Recommendation:** The required dependency is already installed. You DO NOT need to add it to requirements.txt.

#### File: `backend/app/services/websocket_manager.py`
**Summary:** WebSocket connection manager that handles real-time response streaming. Lines 11 and 43-44 show it's already integrated with metrics:
```python
from app.utils.metrics import decrement_websocket_connections, increment_websocket_connections
# ... in connect() method:
increment_websocket_connections()
# ... in disconnect() method:
decrement_websocket_connections()
```

**Recommendation:** WebSocket metrics are ALREADY INSTRUMENTED. The gauge is incremented on connection and decremented on disconnection. No changes needed here.

#### File: `backend/app/connectors/vehicle_connector.py`
**Summary:** Mock vehicle connector that simulates command execution. Line 23 shows it already imports and uses metrics:
```python
from app.utils.metrics import increment_command_counter, observe_command_duration
```

**Recommendation:** The vehicle connector is already instrumented to track command execution metrics. The `increment_command_counter()` and `observe_command_duration()` functions are called during command execution. You SHOULD review the actual usage locations in this file to ensure they're called correctly.

**Note:** Error simulation probabilities are defined at the top (lines 29-32) including `ERROR_PROBABILITY_TIMEOUT = 0.10`. This is where timeout scenarios are simulated.

#### File: `infrastructure/docker/prometheus.yml`
**Summary:** Prometheus configuration file that is already complete and correctly configured. It includes:
- Global scrape interval of 15s
- Scrape job named 'sovd-backend' targeting 'backend:8000'
- Metrics path '/metrics'
- 10s scrape interval for development

**Recommendation:** This file is ALREADY COMPLETE and correct. No changes needed.

#### File: `docker-compose.yml`
**Summary:** Docker Compose orchestration file. Lines 110-133 define the Prometheus service:
- Image: `prom/prometheus:latest`
- Container name: `sovd-prometheus`
- Port mapping: 9090:9090
- Volume mount for prometheus.yml configuration
- Persistent volume: `prometheus-data`
- Depends on backend service

Lines 136-164 also define a Grafana service (bonus - already done for future task I4.T3!).

**Recommendation:** Prometheus service is ALREADY ADDED to docker-compose.yml. No changes needed. The configuration is complete and ready to use.

#### File: `README.md`
**Summary:** Project documentation. Lines 80-82 already document:
```
- Prometheus Metrics: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090
- Grafana Dashboards: http://localhost:3001 (credentials: admin/admin)
```

Line 45 also lists Prometheus + Grafana in the Infrastructure section.

**Recommendation:** Basic Prometheus documentation already exists. You SHOULD enhance it with more detailed instructions on:
1. How to access and use Prometheus UI
2. Example Prometheus queries for SOVD-specific metrics
3. How to verify metrics are being scraped correctly
4. Troubleshooting tips

### Implementation Tips & Notes

#### Tip 1: Task is 90% Complete
**Analysis:** Based on my codebase review, this task is approximately 90% complete! The core infrastructure is all in place:
- ✅ Prometheus instrumentator installed and configured
- ✅ /metrics endpoint exposed
- ✅ Custom metrics defined in utils/metrics.py
- ✅ WebSocket metrics instrumented
- ✅ Command metrics instrumented (in vehicle_connector)
- ✅ Prometheus service in docker-compose.yml
- ✅ Prometheus configuration file created
- ✅ Basic README documentation

**What's Missing:**
1. ❌ `sovd_command_timeout_total` metric not defined
2. ❌ Enhanced README documentation with examples
3. ❌ Verification that metrics are actually being updated correctly

**Recommendation:** Focus your implementation on:
1. Adding the missing `sovd_command_timeout_total` counter to metrics.py
2. Instrumenting the timeout scenario in vehicle_connector.py to increment this counter
3. Writing comprehensive README documentation for Prometheus
4. Testing the entire metrics pipeline end-to-end

#### Tip 2: The `sovd_command_timeout_total` Metric
**Location:** This metric should be added to `backend/app/utils/metrics.py` following the pattern of `commands_executed_total`.

**Usage:** In `backend/app/connectors/vehicle_connector.py`, look for the timeout simulation logic (around line 29: `ERROR_PROBABILITY_TIMEOUT = 0.10`). You need to find where timeout errors are actually triggered and increment this counter there.

**Pattern:**
```python
# In metrics.py
sovd_command_timeout_total = Counter(
    'sovd_command_timeout_total',
    'Total number of SOVD command timeouts (vehicle did not respond)'
)

# Helper function
def increment_timeout_counter() -> None:
    """Increment the command timeout counter."""
    sovd_command_timeout_total.inc()
```

#### Tip 3: README Enhancement Structure
**Recommendation:** Add a new section to README.md titled "## Monitoring and Observability" with subsections:

1. **Accessing Prometheus**
   - URL and basic navigation
   - How to check target status
   - How to verify metrics are being scraped

2. **Available Metrics**
   - List all custom SOVD metrics with descriptions
   - Explain what each metric tracks
   - Include expected values/ranges

3. **Example Prometheus Queries**
   - Commands executed in last 5 minutes: `rate(commands_executed_total[5m])`
   - Command success rate: `rate(commands_executed_total{status="completed"}[5m])`
   - Average command execution time: `rate(command_execution_duration_seconds_sum[5m]) / rate(command_execution_duration_seconds_count[5m])`
   - Active WebSocket connections: `websocket_connections_active`
   - Timeout rate: `rate(sovd_command_timeout_total[5m])`

4. **Troubleshooting**
   - What to do if metrics endpoint returns 404
   - How to check if Prometheus is scraping successfully
   - Common configuration errors

#### Tip 4: Testing the Metrics Pipeline
**Important:** To fully satisfy the acceptance criteria, you MUST verify:

1. **Metrics Endpoint Works:**
   ```bash
   curl http://localhost:8000/metrics | grep commands_executed_total
   ```

2. **Prometheus Scrapes Successfully:**
   - Start services: `docker-compose up -d`
   - Access Prometheus UI: http://localhost:9090
   - Navigate to Status → Targets
   - Verify 'sovd-backend' target shows as UP
   - Check Last Scrape time is recent

3. **Metrics Update Correctly:**
   - Submit a test command via API
   - Query Prometheus: `commands_executed_total`
   - Verify the counter increased
   - Check WebSocket connections gauge by opening WebSocket connection

4. **No Errors in Logs:**
   ```bash
   docker-compose logs prometheus | grep -i error
   ```

#### Warning 1: Prometheus Client Library
**Note:** The metrics are defined using `prometheus_client` library (imported in metrics.py line 12), NOT `prometheus-fastapi-instrumentator`.

- `prometheus-fastapi-instrumentator` is used ONLY in main.py to auto-instrument HTTP metrics and expose the endpoint
- `prometheus_client` is used to define custom application metrics

These are two different libraries that work together. Make sure you understand the distinction.

#### Warning 2: Metric Naming Convention
**Important:** Prometheus metric names should follow these conventions:
- Use snake_case (not camelCase)
- Include units in the name (e.g., `_seconds`, `_total`, `_bytes`)
- Counters should end with `_total`
- Don't repeat the namespace (already using `sovd_` prefix for custom metrics)

The existing metrics follow these conventions correctly. Maintain consistency when adding the timeout metric.

#### Warning 3: Docker Service Names
**Critical:** In Prometheus configuration, the backend service MUST be referenced as `backend:8000`, NOT `localhost:8000`. This is because Prometheus runs inside Docker and needs to use Docker's internal networking (service name resolution).

The current configuration already does this correctly. Do not change it to localhost.

#### Note: Grafana is a Bonus
**Context:** The docker-compose.yml file already includes a Grafana service (task I4.T3). While this isn't required for I4.T2, it means:
- Grafana will start automatically with `docker-compose up`
- You can optionally verify metrics in Grafana UI as an extra validation step
- If you encounter any Grafana-related errors during testing, you can ignore them for this task (they'll be addressed in I4.T3)

### Summary of Work Needed

Based on my analysis, here's what you need to do to complete this task:

1. **Add Missing Metric (10% of work):**
   - Add `sovd_command_timeout_total` Counter to `backend/app/utils/metrics.py`
   - Add helper function `increment_timeout_counter()`
   - Import and use this function in `vehicle_connector.py` where timeouts occur

2. **Enhance Documentation (60% of work):**
   - Add comprehensive "Monitoring and Observability" section to README.md
   - Include Prometheus access instructions
   - List and explain all custom metrics
   - Provide example Prometheus queries
   - Add troubleshooting guide

3. **Testing and Verification (30% of work):**
   - Start docker-compose services
   - Verify /metrics endpoint returns all expected metrics
   - Check Prometheus UI shows backend target as UP
   - Submit test commands and verify metrics update
   - Test WebSocket connections and verify gauge changes
   - Trigger timeout scenario and verify timeout counter increments
   - Check for errors in Prometheus logs
   - Run linters and fix any issues

This should result in 100% task completion and satisfy all acceptance criteria.
