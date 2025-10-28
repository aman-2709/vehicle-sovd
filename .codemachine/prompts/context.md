# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T4",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Write complete SQL DDL script to create all database tables, indexes, and constraints as defined in ERD. Include CREATE TABLE statements for all 6 entities with proper data types (PostgreSQL syntax: UUID, VARCHAR, TEXT, TIMESTAMP, JSONB, BOOLEAN, INTEGER). Add all indexes specified in Architecture Blueprint Section 3.6 (Database Indexes). Include comments explaining design choices. Add basic seed data: one admin user (username: `admin`, password: `admin123` bcrypt-hashed), one engineer user (username: `engineer`, password: `engineer123` bcrypt-hashed), two sample vehicles (VIN: `TESTVIN0000000001`, `TESTVIN0000000002`). Use UUIDs with `gen_random_uuid()` for primary keys.",
  "agent_type_hint": "DatabaseAgent",
  "inputs": "ERD from I1.T3; Architecture Blueprint Section 3.6 (Database Indexes).",
  "target_files": [
    "docs/api/initial_schema.sql",
    "scripts/init_db.sh"
  ],
  "input_files": [
    "docs/diagrams/erd.puml"
  ],
  "deliverables": "SQL DDL script with all tables, indexes, constraints; seed data script; initialization shell script.",
  "acceptance_criteria": "SQL script executes without errors in PostgreSQL 15+; All 6 tables created with correct schema; All indexes from Architecture Blueprint Section 3.6 created (minimum 15 indexes); Seed data inserted: 2 users (admin, engineer), 2 vehicles; `init_db.sh` script successfully initializes database when run against PostgreSQL container; Password hashes use bcrypt algorithm (can be generated using Python `passlib`); Files committed to `docs/api/` and `scripts/` directories",
  "dependencies": [
    "I1.T3"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Data Model Overview (from ERD PlantUML file - I1.T3 output)

The ERD has been fully created and provides the complete database schema specification. Here are the key aspects extracted from the ERD:

**Core Entities (6 tables required):**

1. **users** - User account information and authentication
   - Primary key: user_id (UUID)
   - Unique constraints: username, email
   - Fields: user_id, username, email, password_hash, role, created_at, updated_at
   - Note: role CHECK (role IN ('engineer', 'admin'))

2. **vehicles** - Connected vehicle registry
   - Primary key: vehicle_id (UUID)
   - Unique constraint: vin
   - Fields: vehicle_id, vin, make, model, year, connection_status, last_seen_at, metadata (JSONB), created_at
   - Note: connection_status CHECK (status IN ('connected', 'disconnected', 'error'))
   - Note: metadata JSONB stores flexible vehicle-specific attributes

3. **commands** - SOVD command execution records
   - Primary key: command_id (UUID)
   - Foreign keys: user_id → users, vehicle_id → vehicles
   - Fields: command_id, user_id, vehicle_id, command_name, command_params (JSONB), status, error_message, submitted_at, completed_at
   - Note: status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
   - Note: command_params JSONB stores command-specific parameters
   - Note: ON DELETE CASCADE for user_id and vehicle_id

4. **responses** - Streaming command responses
   - Primary key: response_id (UUID)
   - Foreign key: command_id → commands
   - Fields: response_id, command_id, response_payload (JSONB), sequence_number, is_final, received_at
   - Note: response_payload JSONB stores streaming response data
   - Note: ON DELETE CASCADE for command_id

5. **sessions** - User authentication sessions (JWT refresh tokens)
   - Primary key: session_id (UUID)
   - Foreign key: user_id → users
   - Unique constraint: refresh_token
   - Fields: session_id, user_id, refresh_token, expires_at, created_at
   - Note: ON DELETE CASCADE for user_id

6. **audit_logs** - Audit trail of all system events
   - Primary key: log_id (UUID)
   - Foreign keys (nullable): user_id → users, vehicle_id → vehicles, command_id → commands
   - Fields: log_id, user_id, vehicle_id, command_id, action, entity_type, entity_id, details (JSONB), ip_address, user_agent, timestamp
   - Note: Foreign keys are nullable to preserve audit history
   - Note: details JSONB stores event-specific information
   - Note: ON DELETE SET NULL for user_id, vehicle_id, command_id

**Relationships:**
- users ||--o{ commands : "submits"
- users ||--o{ sessions : "has"
- users ||--o{ audit_logs : "generates"
- vehicles ||--o{ commands : "receives"
- vehicles ||--o{ audit_logs : "triggers"
- commands ||--o{ responses : "produces"
- commands ||--o{ audit_logs : "logs"

### Context: Database Indexes (from ERD - Critical Indexes section)

The ERD specifies **21 total critical indexes** (exceeds minimum of 15 required):

**users table indexes:**
1. UNIQUE INDEX on username
2. UNIQUE INDEX on email
3. INDEX on role (for RBAC filtering)

**vehicles table indexes:**
4. UNIQUE INDEX on vin
5. INDEX on connection_status (for filtering connected vehicles)
6. INDEX on last_seen_at (for monitoring)

**commands table indexes:**
7. INDEX on user_id (for user command history)
8. INDEX on vehicle_id (for vehicle command history)
9. INDEX on status (for filtering by execution status)
10. INDEX on submitted_at (for time-based queries)
11. COMPOSITE INDEX on (vehicle_id, status) (common query pattern)

**responses table indexes:**
12. INDEX on command_id (for retrieving command responses)
13. COMPOSITE INDEX on (command_id, sequence_number) (ordered retrieval)

**sessions table indexes:**
14. UNIQUE INDEX on refresh_token
15. INDEX on user_id (for session management)
16. INDEX on expires_at (for cleanup of expired sessions)

**audit_logs table indexes:**
17. INDEX on user_id (for user audit trail)
18. INDEX on vehicle_id (for vehicle audit trail)
19. INDEX on command_id (for command audit trail)
20. INDEX on action (for filtering by event type)
21. INDEX on timestamp (for time-based queries)

### Context: Data Type Specifications (PostgreSQL 15+)

**PostgreSQL-specific syntax requirements:**

- **Primary Keys:** `UUID PRIMARY KEY DEFAULT gen_random_uuid()`
  - Note: Requires pgcrypto extension or PostgreSQL 13+ built-in support

- **Timestamps:** `TIMESTAMP WITH TIME ZONE DEFAULT now()`
  - Always use timezone-aware timestamps

- **Text Fields:**
  - `VARCHAR(n)` for constrained text (usernames, emails, VINs, etc.)
  - `TEXT` for unlimited text (error messages, user agents, etc.)

- **JSONB:** Use `JSONB` (not JSON) for better performance and indexing support
  - Used in: command_params, response_payload, metadata, details
  - Default: `DEFAULT '{}'::jsonb` or `DEFAULT '{}'`

- **Booleans:** `BOOLEAN DEFAULT false`

- **Enums:** Use `VARCHAR with CHECK constraints` instead of ENUM types
  - More migration-friendly
  - Examples: role CHECK (role IN ('engineer', 'admin'))

**Complete Field Specifications (from ERD):**

**users table:**
```sql
user_id UUID PRIMARY KEY DEFAULT gen_random_uuid()
username VARCHAR(50) NOT NULL UNIQUE
email VARCHAR(255) NOT NULL UNIQUE
password_hash VARCHAR(255) NOT NULL
role VARCHAR(20) NOT NULL CHECK (role IN ('engineer', 'admin'))
created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**vehicles table:**
```sql
vehicle_id UUID PRIMARY KEY DEFAULT gen_random_uuid()
vin VARCHAR(17) NOT NULL UNIQUE
make VARCHAR(100) NOT NULL
model VARCHAR(100) NOT NULL
year INTEGER NOT NULL
connection_status VARCHAR(20) NOT NULL CHECK (connection_status IN ('connected', 'disconnected', 'error'))
last_seen_at TIMESTAMP WITH TIME ZONE
metadata JSONB DEFAULT '{}'
created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**commands table:**
```sql
command_id UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE
vehicle_id UUID NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE
command_name VARCHAR(100) NOT NULL
command_params JSONB NOT NULL DEFAULT '{}'
status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed'))
error_message TEXT
submitted_at TIMESTAMP WITH TIME ZONE DEFAULT now()
completed_at TIMESTAMP WITH TIME ZONE
```

**responses table:**
```sql
response_id UUID PRIMARY KEY DEFAULT gen_random_uuid()
command_id UUID NOT NULL REFERENCES commands(command_id) ON DELETE CASCADE
response_payload JSONB NOT NULL
sequence_number INTEGER NOT NULL
is_final BOOLEAN NOT NULL DEFAULT false
received_at TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**sessions table:**
```sql
session_id UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE
refresh_token VARCHAR(500) NOT NULL UNIQUE
expires_at TIMESTAMP WITH TIME ZONE NOT NULL
created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
```

**audit_logs table:**
```sql
log_id UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id UUID REFERENCES users(user_id) ON DELETE SET NULL
vehicle_id UUID REFERENCES vehicles(vehicle_id) ON DELETE SET NULL
command_id UUID REFERENCES commands(command_id) ON DELETE SET NULL
action VARCHAR(100) NOT NULL
entity_type VARCHAR(50) NOT NULL
entity_id UUID
details JSONB DEFAULT '{}'
ip_address VARCHAR(45)
user_agent TEXT
timestamp TIMESTAMP WITH TIME ZONE DEFAULT now()
```

### Context: Seed Data Requirements

**User Seed Data (2 users):**
1. **Admin User:**
   - username: `admin`
   - email: `admin@sovd.example.com` (inferred)
   - password: `admin123` → bcrypt hash
   - role: `admin`

2. **Engineer User:**
   - username: `engineer`
   - email: `engineer@sovd.example.com` (inferred)
   - password: `engineer123` → bcrypt hash
   - role: `engineer`

**Vehicle Seed Data (2 vehicles):**
1. **Vehicle 1:**
   - vin: `TESTVIN0000000001`
   - make, model, year: (You can choose reasonable values like "Tesla", "Model 3", 2023)
   - connection_status: `connected` (for testing)

2. **Vehicle 2:**
   - vin: `TESTVIN0000000002`
   - make, model, year: (Different from vehicle 1, e.g., "BMW", "X5", 2022)
   - connection_status: `disconnected` (for testing different states)

**Password Hashing:**
- MUST use bcrypt algorithm
- Can be generated using Python `passlib` library
- Example command: `python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('admin123'))"`
- The task acceptance criteria explicitly states passwords must be bcrypt-hashed

### Context: Design Principles (from ERD notes)

**Database Design Principles:**
1. All primary keys use UUID with gen_random_uuid()
2. All timestamps use TIMESTAMP WITH TIME ZONE
3. JSONB used for flexible semi-structured data
4. VARCHAR with CHECK constraints for enums (migration-friendly)
5. Cascade deletes maintain referential integrity
6. Audit logs use SET NULL to preserve history
7. No soft deletes; hard deletes with proper cascade behavior

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `docs/diagrams/erd.puml`
    *   **Summary:** This is the complete Entity Relationship Diagram created in I1.T3. It contains the definitive schema specification with all 6 entities, all fields with data types, all relationships with cardinality, and all 21 critical indexes documented.
    *   **Recommendation:** You MUST use this file as your PRIMARY source of truth for the SQL DDL script. Every table, field, constraint, and index defined in this ERD MUST be included in your SQL script. Do NOT deviate from this specification.
    *   **Critical:** The ERD includes detailed notes about:
        - CHECK constraints for role and status enums
        - ON DELETE CASCADE vs ON DELETE SET NULL behaviors
        - JSONB usage for flexible data
        - Complete index specifications
    *   **Action Required:** Read this file line-by-line and convert each entity definition into a CREATE TABLE statement, ensuring perfect fidelity to the specification.

*   **File:** `docs/diagrams/component_diagram.puml`
    *   **Summary:** This diagram shows the application architecture and demonstrates the project's documentation quality standards. It includes clear titles, comments, and descriptions.
    *   **Recommendation:** Your SQL script SHOULD follow similar documentation practices:
        - Include a header comment block describing the purpose, database version, and creation date
        - Add comments before each CREATE TABLE statement explaining the entity's purpose
        - Add inline comments for complex constraints or design decisions
        - Structure the file logically with clear sections

*   **File:** `backend/pyproject.toml`
    *   **Summary:** This file configures Python tooling with strict quality standards (Black line-length 100, Ruff linting, mypy strict mode, pytest with 80%+ coverage requirement).
    *   **Recommendation:** While this is for Python, it demonstrates the project values **precision, quality, and automated verification**. Your SQL script should similarly:
        - Be precise and correct (no syntax errors)
        - Be well-formatted and readable
        - Include verification mechanisms (the init_db.sh script should verify successful execution)
        - Follow PostgreSQL best practices

*   **File:** `README.md`
    *   **Summary:** The README shows this is a **production-grade enterprise application** targeting PostgreSQL 15+, with Docker deployment, 80%+ test coverage requirements, and security focus.
    *   **Recommendation:** Your SQL script MUST:
        - Use PostgreSQL 15+ specific syntax (gen_random_uuid() is built-in from PG 13+)
        - Include appropriate security measures (password hashes, not plaintext)
        - Be compatible with Docker-based deployment (the init_db.sh will run in a container)
        - Follow enterprise-grade database design (proper normalization, referential integrity, comprehensive indexing)

*   **File:** `Makefile`
    *   **Summary:** The Makefile provides high-level commands (`make up`, `make down`, `make test`, `make lint`) for managing the project.
    *   **Recommendation:** Your `init_db.sh` script SHOULD be designed to integrate with this workflow:
        - It will likely be called during `make up` or by docker-compose
        - It should be idempotent (safe to run multiple times)
        - It should provide clear output indicating success/failure
        - It should exit with appropriate status codes (0 for success, non-zero for failure)

*   **File:** `docker-compose.yml`
    *   **Summary:** Currently a placeholder (will be implemented in I1.T5), but shows the project uses Docker Compose for local development.
    *   **Recommendation:** Your `init_db.sh` script MUST be compatible with PostgreSQL running in a Docker container. It will need to:
        - Accept database connection parameters (host, port, database name, user, password) as environment variables or arguments
        - Use `psql` or similar PostgreSQL client tools
        - Handle connection errors gracefully
        - Work when executed from within the container or from the host

### Implementation Tips & Notes

*   **Tip - SQL File Structure:** Organize your `initial_schema.sql` file with clear sections:
    ```sql
    -- ============================================================================
    -- SOVD Command WebApp - Initial Database Schema
    -- Database: PostgreSQL 15+
    -- Created: [Date]
    -- Description: Creates all tables, indexes, and seed data for the SOVD platform
    -- ============================================================================

    -- Section 1: Extensions and Setup
    -- Section 2: Table Creation (in dependency order: users, vehicles, commands, responses, sessions, audit_logs)
    -- Section 3: Index Creation (grouped by table)
    -- Section 4: Seed Data Insertion
    ```

*   **Tip - Table Creation Order:** IMPORTANT! You MUST create tables in the correct order to satisfy foreign key dependencies:
    1. **First:** `users` and `vehicles` (no foreign key dependencies)
    2. **Second:** `commands` (depends on users and vehicles)
    3. **Third:** `responses` (depends on commands)
    4. **Fourth:** `sessions` (depends on users)
    5. **Fifth:** `audit_logs` (depends on users, vehicles, commands - but all nullable)

*   **Tip - Password Hash Generation:** You need to generate bcrypt hashes for the seed data. The task says you CAN use Python `passlib`. Here's how:
    ```python
    from passlib.hash import bcrypt
    admin_hash = bcrypt.hash('admin123')
    engineer_hash = bcrypt.hash('engineer123')
    ```
    Include the generated hashes directly in your SQL INSERT statements. **DO NOT** include the Python code in the SQL file; generate the hashes beforehand and hardcode them.

*   **Tip - gen_random_uuid():** PostgreSQL 13+ includes `gen_random_uuid()` as a built-in function (no extension needed). However, for PostgreSQL 12 and earlier, you would need:
    ```sql
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
    ```
    Since the requirement specifies PostgreSQL 15+, you **do not need** the pgcrypto extension, but adding it defensively won't hurt and ensures backward compatibility.

*   **Tip - Seed Data UUIDs:** For seed data, you have two options:
    1. Let PostgreSQL generate UUIDs automatically (`DEFAULT gen_random_uuid()`)
    2. Hardcode specific UUIDs for predictable testing (e.g., `'00000000-0000-0000-0000-000000000001'`)

    **Recommendation:** Use hardcoded UUIDs for seed data to make testing easier (engineers can know the admin user ID is always a specific value).

*   **Tip - JSONB Defaults:** When inserting seed data with JSONB columns that should be empty:
    ```sql
    -- Both work:
    metadata = '{}'::jsonb
    metadata = DEFAULT  -- Uses the DEFAULT '{}' from table definition
    ```

*   **Note - init_db.sh Script:** The shell script should:
    1. Check if PostgreSQL is ready (wait for connection)
    2. Execute the SQL file using `psql`
    3. Verify tables were created (e.g., count tables in schema)
    4. Verify seed data was inserted (e.g., count rows in users and vehicles)
    5. Print success message or error and exit with appropriate code

    Example structure:
    ```bash
    #!/bin/bash
    # Wait for PostgreSQL to be ready
    # Execute initial_schema.sql
    # Verify tables exist
    # Verify seed data exists
    # Print results
    ```

*   **Note - File Locations:** The acceptance criteria specifies:
    - SQL DDL: `docs/api/initial_schema.sql`
    - Shell script: `scripts/init_db.sh`

    These directories already exist in the project structure. Make sure to create files in the EXACT locations specified.

*   **Important - Index Naming:** Use descriptive, consistent index names:
    - Format: `idx_{table}_{column(s)}` or `unq_{table}_{column}` for unique indexes
    - Examples:
        - `idx_users_username` (unique)
        - `idx_commands_vehicle_id_status` (composite)
        - `idx_audit_logs_timestamp`

*   **Important - Comments in SQL:** Add comments explaining:
    - Why certain indexes are needed (query performance for specific access patterns)
    - Why CHECK constraints are used instead of ENUMs (migration flexibility)
    - Why audit_logs uses SET NULL (preserve audit trail even when entities deleted)
    - Why JSONB is used for certain fields (flexible semi-structured data)

*   **Warning - ON DELETE Behaviors:** Pay careful attention to the cascade behaviors specified in the ERD:
    - `commands.user_id` and `commands.vehicle_id`: **CASCADE** (if user/vehicle deleted, their commands are deleted)
    - `responses.command_id`: **CASCADE** (if command deleted, responses deleted)
    - `sessions.user_id`: **CASCADE** (if user deleted, sessions deleted)
    - `audit_logs.user_id/vehicle_id/command_id`: **SET NULL** (preserve audit trail)

    Getting these wrong will fail the acceptance criteria.

*   **Warning - Completeness:** The acceptance criteria states "All 6 tables created with correct schema" and "All indexes from Architecture Blueprint Section 3.6 created (minimum 15 indexes)". The ERD specifies 21 indexes. You MUST create ALL 21 indexes listed in the ERD, not just the minimum 15.

*   **Warning - PostgreSQL Version:** The requirement specifies PostgreSQL 15+. Ensure you:
    - Don't use deprecated syntax
    - Don't use features not available in PG 15
    - Test the script against PostgreSQL 15 (or use the docker-compose PostgreSQL image once available)

### Project Conventions Observed

*   **Strict Type Safety:** The project uses mypy strict mode for Python, suggesting a culture of type safety. Apply similar rigor to SQL with explicit data types and constraints.

*   **Comprehensive Testing:** 80%+ test coverage requirement. Your init_db.sh script should include verification steps to ensure the schema was created correctly.

*   **Security First:** JWT authentication, bcrypt password hashing, RBAC. Never include plaintext passwords in seed data.

*   **Enterprise-Grade Documentation:** All existing files (ERD, component diagram, README) are well-documented. Follow this standard in your SQL file with thorough comments.

*   **Automation:** Makefile targets, Docker Compose, CI/CD. The init_db.sh script should be fully automated, requiring no manual intervention.

### Quality Checklist for Coder Agent

Before completing this task, ensure:

#### SQL DDL File (initial_schema.sql):

1. ✅ Header comment block with title, database version, date, description
2. ✅ All 6 tables created: users, vehicles, commands, responses, sessions, audit_logs
3. ✅ Tables created in correct dependency order (users/vehicles → commands → responses/sessions/audit_logs)
4. ✅ All fields from ERD included for each table with correct data types
5. ✅ All PRIMARY KEY constraints defined with UUID and DEFAULT gen_random_uuid()
6. ✅ All UNIQUE constraints defined (username, email, vin, refresh_token)
7. ✅ All FOREIGN KEY constraints defined with correct ON DELETE behaviors (CASCADE vs SET NULL)
8. ✅ All CHECK constraints defined (role, connection_status, status)
9. ✅ All NOT NULL constraints applied to required fields
10. ✅ All DEFAULT values defined (timestamps with now(), JSONB with '{}', status with 'pending', is_final with false)
11. ✅ All 21 indexes created with descriptive names
12. ✅ Composite indexes created correctly (vehicle_id + status, command_id + sequence_number)
13. ✅ Seed data: 2 users (admin, engineer) with bcrypt-hashed passwords
14. ✅ Seed data: 2 vehicles (TESTVIN0000000001, TESTVIN0000000002)
15. ✅ Comments explaining design choices, constraints, JSONB usage, cascade behaviors
16. ✅ File is well-formatted, readable, and follows PostgreSQL best practices
17. ✅ File executes without errors in PostgreSQL 15+ (test before committing)

#### Initialization Script (init_db.sh):

1. ✅ Shebang line: `#!/bin/bash`
2. ✅ Set script to exit on errors: `set -e`
3. ✅ Header comment describing purpose
4. ✅ Read database connection parameters from environment variables (DATABASE_URL or individual params)
5. ✅ Wait for PostgreSQL to be ready (e.g., using `pg_isready` or retry loop)
6. ✅ Execute initial_schema.sql using `psql`
7. ✅ Verify tables were created (e.g., query information_schema or use `\dt`)
8. ✅ Verify seed data exists (e.g., SELECT COUNT(*) from users, vehicles)
9. ✅ Print clear success/failure messages
10. ✅ Exit with status code 0 on success, non-zero on failure
11. ✅ Script is idempotent (safe to run multiple times - consider DROP TABLE IF EXISTS or check before creating)
12. ✅ Script has executable permissions: `chmod +x scripts/init_db.sh`
13. ✅ Script is compatible with Docker environment
14. ✅ Script includes error handling for connection failures

#### General:

1. ✅ Files created in exact locations: `docs/api/initial_schema.sql` and `scripts/init_db.sh`
2. ✅ Both files committed to repository
3. ✅ SQL file is syntactically valid (no parse errors)
4. ✅ Script executes successfully against PostgreSQL 15+ container
5. ✅ All acceptance criteria met

---

**End of Briefing Package**
