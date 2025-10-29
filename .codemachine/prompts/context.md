# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I2.T7",
  "iteration_id": "I2",
  "iteration_goal": "Core Backend APIs - Authentication, Vehicles, Commands",
  "description": "Implement `backend/app/services/audit_service.py` with function: `log_audit_event(user_id, action, entity_type, entity_id, details, ip_address, user_agent, db_session)` (inserts record into audit_logs table). Integrate audit logging into auth and command services: log events for `user_login`, `user_logout`, `command_submitted`, `command_completed`, `command_failed`. Extract user IP and user-agent from FastAPI Request object. Configure structlog in `backend/app/utils/logging.py` for structured JSON logging with fields: timestamp, level, logger, event, correlation_id, user_id (if available). Add middleware in `backend/app/middleware/logging_middleware.py` to generate correlation ID (X-Request-ID header) for each request and inject into logs. Write unit tests in `backend/tests/unit/test_audit_service.py`.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Logging & Monitoring); Data Model (audit_logs table).",
  "target_files": [
    "backend/app/services/audit_service.py",
    "backend/app/utils/logging.py",
    "backend/app/middleware/logging_middleware.py",
    "backend/app/services/auth_service.py",
    "backend/app/services/command_service.py",
    "backend/app/main.py",
    "backend/tests/unit/test_audit_service.py"
  ],
  "input_files": [
    "backend/app/models/audit_log.py",
    "backend/app/services/auth_service.py",
    "backend/app/services/command_service.py"
  ],
  "deliverables": "Audit service with database logging; structured logging with correlation IDs; middleware for request tracking; integration into auth and command flows.",
  "acceptance_criteria": "`POST /api/v1/auth/login` creates audit_log record with action=`user_login`; `POST /api/v1/commands` creates audit_log record with action=`command_submitted`; Command completion (via mock connector) creates audit_log with action=`command_completed`; Audit logs include user_id, ip_address, user_agent, timestamp; All logs output as structured JSON (parseable); Each request has unique correlation_id in logs (verify in log output); Correlation ID passed through service calls (appears in all logs for same request); Unit tests verify audit log creation for each event type; Test coverage ≥ 80%; No linter errors",
  "dependencies": [
    "I2.T1",
    "I2.T3",
    "I2.T5"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents.

### Context: Logging & Monitoring Strategy

**Source:** Architecture Blueprint Section 3.8 (Operational Architecture)

The system requires comprehensive logging and monitoring capabilities with structured JSON logs and audit trails for security-relevant events.

---

### Context: AuditLog Data Model

**Source:** `backend/app/models/audit_log.py`

The `AuditLog` model schema:
- `log_id` (UUID, PK)
- `user_id` (UUID, FK, nullable)
- `vehicle_id` (UUID, FK, nullable)
- `command_id` (UUID, FK, nullable)
- `action` (VARCHAR(100), NOT NULL)
- `entity_type` (VARCHAR(50), NOT NULL)
- `entity_id` (UUID, nullable)
- `details` (JSONB, default '{}')
- `ip_address` (VARCHAR(45), nullable)
- `user_agent` (TEXT, nullable)
- `timestamp` (TIMESTAMP WITH TIMEZONE, default CURRENT_TIMESTAMP)

---

## 3. Codebase Analysis & Strategic Guidance

### Relevant Existing Code

#### File: `backend/app/models/audit_log.py`
- **Summary:** Fully implemented SQLAlchemy ORM model with all required fields
- **Recommendation:** Import `AuditLog` from this module when creating audit records

#### File: `backend/app/services/auth_service.py`
- **Summary:** Authentication logic including token generation and user authentication
- **Recommendation:** Add audit logging after login/logout operations

#### File: `backend/app/services/command_service.py`
- **Summary:** Command lifecycle management with vehicle connector integration
- **Recommendation:** Add audit logging after command creation

#### File: `backend/app/dependencies.py`
- **Summary:** FastAPI dependencies for auth/authorization using structlog
- **Recommendation:** Follow same structlog pattern in new files

#### File: `backend/app/main.py`
- **Summary:** FastAPI entry point with CORS middleware
- **Recommendation:** Register logging middleware here before API routers

---

### Implementation Tips

**Tip 1:** Create `backend/app/repositories/audit_repository.py` following existing repository pattern

**Tip 2:** Accept `db_session` as parameter in audit service - don't create new sessions

**Tip 3:** Wrap audit calls in try-except - never let audit failures break the app

**Tip 4:** Extract IP/user-agent at API layer (where Request exists) and pass to services

**Tip 5:** Import logging config at top of `main.py` before creating loggers

**Tip 6:** Use `structlog.testing.capture_logs()` to test correlation ID propagation

**Warning:** Pass correlation_id explicitly to background tasks - request context is lost

---

### File Structure Checklist

**New Files:**
1. `backend/app/services/audit_service.py`
2. `backend/app/utils/logging.py`
3. `backend/app/middleware/logging_middleware.py`
4. `backend/tests/unit/test_audit_service.py`

**Modified Files:**
5. `backend/app/services/auth_service.py`
6. `backend/app/services/command_service.py`
7. `backend/app/main.py`

**Recommended:**
8. `backend/app/repositories/audit_repository.py`
9. `backend/app/utils/request_utils.py`

---

### Dependencies Verification

- ✅ **I2.T1 (Auth Service)**: Complete
- ✅ **I2.T3 (Command Service)**: Complete
- ✅ **I2.T5 (Mock Vehicle Connector)**: Complete

All dependencies satisfied - proceed with implementation.
