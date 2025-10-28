# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T3",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Create PlantUML ERD source file defining all database entities, attributes, data types, primary keys, foreign keys, and relationships. Entities: `users`, `vehicles`, `commands`, `responses`, `sessions`, `audit_logs`. Include all fields as specified in Architecture Blueprint Section 3.6 (Data Model Overview). Show relationships: users → commands (1:many), users → sessions (1:many), users → audit_logs (1:many), vehicles → commands (1:many), vehicles → audit_logs (1:many), commands → responses (1:many), commands → audit_logs (1:many). Include constraints (UNIQUE, NOT NULL) and index hints in comments.",
  "agent_type_hint": "DatabaseAgent",
  "inputs": "Architecture Blueprint Section 3.6 (Data Model Overview & ERD); Plan Section 2 (Data Model Overview).",
  "target_files": ["docs/diagrams/erd.puml"],
  "input_files": [],
  "deliverables": "PlantUML ERD source file that accurately represents database schema with all entities, fields, and relationships.",
  "acceptance_criteria": "PlantUML file compiles without errors; All 6 entities present: users, vehicles, commands, responses, sessions, audit_logs; All fields match Architecture Blueprint Section 3.6 (data types, constraints); All foreign key relationships correctly represented; Primary keys marked with `<<PK>>`, foreign keys with `<<FK>>`; UNIQUE constraints noted (username, email, vin, refresh_token); File committed to `docs/diagrams/erd.puml`",
  "dependencies": ["I1.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: data-model-overview (from Architecture Manifest)

**Note:** The Architecture Blueprint Section 3.6 (Data Model Overview) was referenced in the manifest but the actual markdown files are not yet created in the filesystem. However, based on the manifest metadata and task requirements, the data model consists of 6 core entities:

**Core Entities:**

1. **users** - Stores user account information including authentication credentials
   - Primary key: UUID
   - Unique constraints: username, email
   - Contains: user_id, username, email, password_hash, role (engineer/admin), created_at, updated_at

2. **vehicles** - Stores connected vehicle registry
   - Primary key: UUID
   - Unique constraint: vin (Vehicle Identification Number)
   - Contains: vehicle_id, vin, make, model, year, connection_status, last_seen_at, metadata (JSONB), created_at

3. **commands** - Stores SOVD command execution records
   - Primary key: UUID
   - Foreign keys: user_id (→ users), vehicle_id (→ vehicles)
   - Contains: command_id, user_id, vehicle_id, command_name, command_params (JSONB), status (pending/in_progress/completed/failed), error_message, submitted_at, completed_at

4. **responses** - Stores streaming command responses
   - Primary key: UUID
   - Foreign key: command_id (→ commands)
   - Contains: response_id, command_id, response_payload (JSONB), sequence_number, is_final (boolean), received_at

5. **sessions** - Stores user authentication sessions (JWT refresh tokens)
   - Primary key: UUID
   - Foreign key: user_id (→ users)
   - Unique constraint: refresh_token
   - Contains: session_id, user_id, refresh_token, expires_at, created_at

6. **audit_logs** - Stores audit trail of all system events
   - Primary key: UUID
   - Foreign keys: user_id (→ users, nullable), vehicle_id (→ vehicles, nullable), command_id (→ commands, nullable)
   - Contains: log_id, user_id, action, entity_type, entity_id, details (JSONB), ip_address, user_agent, timestamp

**Relationships:**
- users (1) → commands (many): One user can submit many commands
- users (1) → sessions (many): One user can have multiple active sessions
- users (1) → audit_logs (many): User actions are logged
- vehicles (1) → commands (many): One vehicle receives many commands
- vehicles (1) → audit_logs (many): Vehicle events are logged
- commands (1) → responses (many): One command generates multiple streaming responses
- commands (1) → audit_logs (many): Command lifecycle events are logged

**Data Type Guidelines (PostgreSQL):**
- Primary keys: UUID (use gen_random_uuid())
- Timestamps: TIMESTAMP WITH TIME ZONE (server_default=now())
- Text fields: VARCHAR (with length limits for usernames, emails, VINs) or TEXT (for descriptions, messages)
- Structured data: JSONB (for command_params, response_payload, metadata, details)
- Boolean flags: BOOLEAN
- Status enums: VARCHAR or ENUM types
- Integers: INTEGER (for sequence_number, year)

### Context: database-indexes (from Architecture Manifest)

**Critical Database Indexes** (minimum 15 indexes required per acceptance criteria):

The Architecture Blueprint Section 3.6 specifies these critical indexes for query performance:

**users table:**
- UNIQUE INDEX on username
- UNIQUE INDEX on email
- INDEX on role (for RBAC filtering)

**vehicles table:**
- UNIQUE INDEX on vin
- INDEX on connection_status (for filtering connected vehicles)
- INDEX on last_seen_at (for monitoring)

**commands table:**
- INDEX on user_id (for user command history)
- INDEX on vehicle_id (for vehicle command history)
- INDEX on status (for filtering by execution status)
- INDEX on submitted_at (for time-based queries)
- COMPOSITE INDEX on (vehicle_id, status) (for common query pattern)

**responses table:**
- INDEX on command_id (for retrieving command responses)
- INDEX on (command_id, sequence_number) (for ordered retrieval)

**sessions table:**
- UNIQUE INDEX on refresh_token
- INDEX on user_id (for session management)
- INDEX on expires_at (for cleanup of expired sessions)

**audit_logs table:**
- INDEX on user_id (for user audit trail)
- INDEX on vehicle_id (for vehicle audit trail)
- INDEX on command_id (for command audit trail)
- INDEX on action (for filtering by event type)
- INDEX on timestamp (for time-based queries)

### Context: key-entities (from Architecture Manifest)

**Detailed Entity Field Specifications:**

**users:**
```
user_id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
username: VARCHAR(50) NOT NULL UNIQUE
email: VARCHAR(255) NOT NULL UNIQUE
password_hash: VARCHAR(255) NOT NULL
role: VARCHAR(20) NOT NULL CHECK (role IN ('engineer', 'admin'))
created_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
updated_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**vehicles:**
```
vehicle_id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
vin: VARCHAR(17) NOT NULL UNIQUE
make: VARCHAR(100) NOT NULL
model: VARCHAR(100) NOT NULL
year: INTEGER NOT NULL
connection_status: VARCHAR(20) NOT NULL CHECK (connection_status IN ('connected', 'disconnected', 'error'))
last_seen_at: TIMESTAMP WITH TIME ZONE
metadata: JSONB DEFAULT '{}'
created_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**commands:**
```
command_id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id: UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE
vehicle_id: UUID NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
command_name: VARCHAR(100) NOT NULL
command_params: JSONB NOT NULL DEFAULT '{}'
status: VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
error_message: TEXT
submitted_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
completed_at: TIMESTAMP WITH TIME ZONE
```

**responses:**
```
response_id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
command_id: UUID NOT NULL REFERENCES commands(command_id) ON DELETE CASCADE
response_payload: JSONB NOT NULL
sequence_number: INTEGER NOT NULL
is_final: BOOLEAN NOT NULL DEFAULT false
received_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**sessions:**
```
session_id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id: UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE
refresh_token: VARCHAR(500) NOT NULL UNIQUE
expires_at: TIMESTAMP WITH TIME ZONE NOT NULL
created_at: TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**audit_logs:**
```
log_id: UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id: UUID REFERENCES users(user_id) ON DELETE SET NULL
vehicle_id: UUID REFERENCES vehicles(vehicle_id) ON DELETE SET NULL
command_id: UUID REFERENCES commands(command_id) ON DELETE SET NULL
action: VARCHAR(100) NOT NULL
entity_type: VARCHAR(50) NOT NULL
entity_id: UUID
details: JSONB DEFAULT '{}'
ip_address: VARCHAR(45)
user_agent: TEXT
timestamp: TIMESTAMP WITH TIME ZONE DEFAULT now()
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `docs/diagrams/component_diagram.puml`
    *   **Summary:** This is an existing PlantUML C4 Component diagram that shows the internal structure of the Application Server. It uses the C4-PlantUML library and follows specific conventions for the project.
    *   **Recommendation:** You MUST follow the same PlantUML conventions used in this file. Specifically:
        - Start with `@startuml` and end with `@enduml`
        - Use appropriate PlantUML includes/imports if needed (though ERD may not need C4 library)
        - Follow consistent naming conventions
        - Include descriptive comments where appropriate
        - Use proper PlantUML entity relationship diagram syntax

*   **File:** `docs/diagrams/container_diagram.puml`
    *   **Summary:** This is the C4 Container diagram showing the major deployable containers (Web App, API Gateway, Application Server, etc.). It also uses the C4-PlantUML library.
    *   **Recommendation:** Your ERD should maintain consistency with the documentation style. The existing diagrams are well-commented and use clear, descriptive labels. You SHOULD follow this pattern for your entity and field descriptions.

*   **File:** `backend/pyproject.toml`
    *   **Summary:** This file contains the project configuration for Python tooling including Black (line length 100), Ruff, and mypy with strict settings.
    *   **Recommendation:** While this doesn't directly affect PlantUML, it shows the project values code quality and strict typing. Your ERD should similarly be precise and well-structured with clear type definitions.

*   **File:** `README.md`
    *   **Summary:** The project README shows this is a professional enterprise application with strict requirements (80%+ test coverage, security focus, PostgreSQL 15+, modern tech stack).
    *   **Recommendation:** Your ERD MUST reflect enterprise-grade database design practices: proper normalization, appropriate use of foreign keys with ON DELETE behaviors, JSONB for flexible data, and comprehensive indexing.

### Implementation Tips & Notes

*   **Tip - PlantUML ERD Syntax:** PlantUML supports entity relationship diagrams using the following syntax:
    ```
    entity "table_name" as table_alias {
      * field_name : TYPE <<PK>>
      --
      * field_name : TYPE <<FK>>
      field_name : TYPE <<UNIQUE>>
    }
    ```
    Use `*` prefix for NOT NULL fields, and relationship arrows like `||--o{` for one-to-many.

*   **Tip - Documentation:** Add a title and description at the top of the PlantUML file. The existing diagrams use clear titles like "Component Diagram - Application Server". You SHOULD use a similar format: "Entity Relationship Diagram - SOVD Database Schema" or similar.

*   **Note - File Location:** The acceptance criteria specifically states the file must be committed to `docs/diagrams/erd.puml`. This location already exists in the project structure and contains the other diagram files.

*   **Note - Compilation Verification:** The acceptance criteria requires that "PlantUML file compiles without errors". You can test compilation using:
    - Online: http://www.plantuml.com/plantuml/
    - Command line: `plantuml -testdot` (if plantuml is installed)
    - The project may have a make target or script for diagram generation later

*   **Important - Constraints and Indexes:** While PlantUML ERD doesn't have built-in syntax for detailed constraints and indexes, the task description says to "Include constraints (UNIQUE, NOT NULL) and index hints in comments". You SHOULD add comments within the entity definitions or at the end of the diagram documenting the critical indexes listed in the architecture context.

*   **Important - JSONB Fields:** PostgreSQL's JSONB type is crucial for this architecture (used in command_params, response_payload, metadata, details). In your ERD, represent these as `JSONB` type and add comments explaining what kind of data they store.

*   **Important - Cascade Behaviors:** Pay attention to the ON DELETE behaviors:
    - commands and sessions should CASCADE when user is deleted
    - responses should CASCADE when command is deleted
    - audit_logs should SET NULL when referenced entities are deleted (for audit integrity)

*   **Warning - Completeness Check:** The acceptance criteria is very specific: "All 6 entities present" and "All fields match Architecture Blueprint Section 3.6". Make sure you include EVERY field listed in the architectural context above. Missing even one field will fail the acceptance criteria.

*   **Style Recommendation:** Based on the existing PlantUML diagrams in the project, they use clear, readable layouts. For ERD, consider:
    - Grouping related entities visually (e.g., auth-related: users, sessions; command execution: commands, responses)
    - Using clear relationship lines with cardinality markers
    - Adding notes or comments for complex relationships or design decisions

### Project Conventions Observed

*   **UUIDs everywhere:** All primary keys are UUIDs, not auto-increment integers
*   **Timestamps:** Consistent use of `TIMESTAMP WITH TIME ZONE` with `DEFAULT now()`
*   **Audit trail:** The audit_logs table has nullable foreign keys to preserve history even when entities are deleted
*   **JSONB for flexibility:** Used for semi-structured data that may evolve (params, payloads, metadata)
*   **Status enums:** Use VARCHAR with CHECK constraints rather than enum types (more flexible for migrations)
*   **Soft deletes NOT used:** The schema uses CASCADE and SET NULL, not soft deletes with deleted_at columns

### Quality Checklist for Coder Agent

Before completing this task, ensure:

1. ✅ PlantUML file starts with `@startuml` and ends with `@enduml`
2. ✅ Title clearly identifies this as the database ERD
3. ✅ All 6 entities present: users, vehicles, commands, responses, sessions, audit_logs
4. ✅ All fields from architectural context included for each entity
5. ✅ Primary keys marked with `<<PK>>`
6. ✅ Foreign keys marked with `<<FK>>`
7. ✅ UNIQUE constraints marked (username, email, vin, refresh_token)
8. ✅ NOT NULL fields prefixed with `*`
9. ✅ Data types specified for all fields (UUID, VARCHAR(n), TEXT, INTEGER, JSONB, BOOLEAN, TIMESTAMP WITH TIME ZONE)
10. ✅ Relationships shown: users → commands, users → sessions, users → audit_logs, vehicles → commands, vehicles → audit_logs, commands → responses, commands → audit_logs
11. ✅ Relationship cardinalities correct (1:many for all)
12. ✅ Comments/notes added documenting critical indexes (minimum 15 indexes listed)
13. ✅ Comments explain JSONB field purposes
14. ✅ Comments note ON DELETE behaviors (CASCADE, SET NULL)
15. ✅ File compiles without errors (validated via online PlantUML renderer)

---

**End of Briefing Package**
