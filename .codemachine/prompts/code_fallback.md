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

---

## Issues Detected

*   **Missing Metric:** The `sovd_command_timeout_total` Counter metric is **NOT defined** in `backend/app/utils/metrics.py`. This metric is explicitly required in the task description and architecture documentation (Section 3.8 - Monitoring Strategy - Custom Metrics).

---

## Best Approach to Fix

You MUST add the `sovd_command_timeout_total` Counter metric to `backend/app/utils/metrics.py` following the existing pattern:

1. **Define the metric** in `backend/app/utils/metrics.py` after the existing metrics (around line 38):
   ```python
   # Command timeout metric
   sovd_command_timeout_total = Counter(
       'sovd_command_timeout_total',
       'Total number of SOVD command timeouts (vehicle did not respond)'
   )
   ```

2. **Add a helper function** in the same file (around line 78):
   ```python
   def increment_timeout_counter() -> None:
       """Increment the command timeout counter."""
       sovd_command_timeout_total.inc()
   ```

3. **Import and use the helper function** in `backend/app/connectors/vehicle_connector.py`:
   - Add `increment_timeout_counter` to the import on line 23:
     ```python
     from app.utils.metrics import increment_command_counter, observe_command_duration, increment_timeout_counter
     ```
   - Call the function when a timeout occurs. Look for line 554 where `failure_status` is determined:
     ```python
     # Determine failure status (timeout vs failed)
     failure_status = "timeout" if isinstance(e, TimeoutError) else "failed"

     # Increment the timeout counter specifically for timeout errors
     if isinstance(e, TimeoutError):
         increment_timeout_counter()
     ```

4. **Verify the metric appears** in the `/metrics` endpoint by checking the test output or manually testing.

**IMPORTANT:** Do NOT modify any other files. Do NOT change the existing metrics. The task is 95% complete - you only need to add this one missing metric.
