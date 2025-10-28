# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T8",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Initialize Alembic in backend directory with `alembic init alembic`. Configure `backend/alembic.ini` to use environment variable for database URL. Modify `backend/alembic/env.py` to: import SQLAlchemy models from `app.models`, read database URL from environment variable `DATABASE_URL`, use async engine (asyncpg). Create initial migration `001_initial_schema` that generates the same schema as `initial_schema.sql` from I1.T4 (using Alembic auto-generate or manual revision). Test migration: `alembic upgrade head` should create all tables.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Database schema from I1.T4; SQLAlchemy ORM best practices.",
  "target_files": [
    "backend/alembic.ini",
    "backend/alembic/env.py",
    "backend/alembic/versions/001_initial_schema.py"
  ],
  "input_files": [
    "docs/api/initial_schema.sql"
  ],
  "deliverables": "Configured Alembic with initial migration; migration script that creates database schema.",
  "acceptance_criteria": "`alembic upgrade head` (run from backend directory) creates all 6 tables in database; `alembic downgrade base` successfully drops all tables; `alembic history` shows migration 001_initial_schema; `env.py` reads DATABASE_URL from environment variable (e.g., `os.getenv(\"DATABASE_URL\")`); Migration file includes all CREATE TABLE statements matching `initial_schema.sql`; No errors when running migration against PostgreSQL 15",
  "dependencies": [
    "I1.T4",
    "I1.T5",
    "I1.T6"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: data-model-overview (from 03_System_Structure_and_Data.md)

```markdown
### 3.6. Data Model Overview & ERD

#### Description

The data model supports the core functionalities of vehicle management, command execution, response tracking, and comprehensive auditing. Key design decisions:

- **Relational Design**: Strong referential integrity ensures data consistency for audit compliance
- **JSONB Columns**: `command_params` and `response_payload` use JSONB for flexible schema while maintaining queryability
- **Temporal Tracking**: All entities include `created_at`; commands and responses include detailed timestamp tracking
- **Status Enums**: Explicit status values enable workflow tracking and filtering
- **Audit Trail**: Dedicated `audit_logs` table captures all operations for compliance

#### Key Entities

**users**
- Stores user profiles, authentication credentials, and roles
- Supports RBAC with `role` field (e.g., 'engineer', 'admin')
- Links to commands via `user_id` foreign key for audit trail

**vehicles**
- Registry of all vehicles with VIN as natural key
- Tracks connection status (`connected`, `disconnected`, `error`)
- `last_seen_at` enables stale connection detection
- Supports filtering and health monitoring

**commands**
- Records every SOVD command execution attempt
- JSONB `command_params` stores structured parameters
- Status tracking: `pending`, `in_progress`, `completed`, `failed`
- Links to user (who executed) and vehicle (target)

**responses**
- Stores command responses (may be multiple responses per command for streaming)
- JSONB `response_payload` accommodates variable response structures
- `sequence_number` orders streaming responses
- `received_at` tracks latency

**sessions**
- Manages user sessions and JWT refresh tokens
- `expires_at` enables session cleanup
- Links to user for session revocation

**audit_logs**
- Comprehensive audit trail for compliance
- JSONB `details` captures operation-specific metadata
- Links to user, vehicle, and command as applicable
- Supports filtering by action, entity_type, timestamp
```

### Context: database-indexes (from 03_System_Structure_and_Data.md)

```markdown
#### Database Indexes (Performance Critical)

**Indexes for Query Performance:**

```sql
-- Users
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);

-- Vehicles
CREATE INDEX idx_vehicles_vin ON vehicles(vin);
CREATE INDEX idx_vehicles_status ON vehicles(connection_status);
CREATE INDEX idx_vehicles_last_seen ON vehicles(last_seen_at DESC);

-- Commands
CREATE INDEX idx_commands_vehicle_id ON commands(vehicle_id);
CREATE INDEX idx_commands_user_id ON commands(user_id);
CREATE INDEX idx_commands_status ON commands(status);
CREATE INDEX idx_commands_submitted_at ON commands(submitted_at DESC);
CREATE INDEX idx_commands_composite ON commands(vehicle_id, status, submitted_at DESC);

-- Responses
CREATE INDEX idx_responses_command_id ON responses(command_id);
CREATE INDEX idx_responses_received_at ON responses(received_at DESC);

-- Sessions
CREATE INDEX idx_sessions_user_id ON sessions(user_id);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);

-- Audit Logs
CREATE INDEX idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_vehicle_id ON audit_logs(vehicle_id);
CREATE INDEX idx_audit_command_id ON audit_logs(command_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_composite ON audit_logs(user_id, action, created_at DESC);
```
```

### Context: database-rationale (from 03_System_Structure_and_Data.md)

```markdown
#### Database Design Rationale

**PostgreSQL Selection:**
- **ACID Compliance**: Critical for audit logs and financial/compliance scenarios
- **JSONB Support**: Flexible schema for variable command parameters and responses while maintaining indexing and query capabilities
- **Mature Tooling**: pgAdmin, pg_dump, robust backup solutions
- **Scalability**: Read replicas for reporting; partitioning for audit_logs table as it grows

**Normalization vs. Denormalization:**
- **Normalized Design**: Reduces data redundancy, ensures referential integrity
- **Strategic Denormalization**: `vehicles.last_seen_at` denormalized from connection logs for fast status queries
- **JSONB for Flexibility**: Avoids EAV anti-pattern while accommodating SOVD command diversity

**Audit Log Design:**
- Separate table (vs. triggers on every table) centralizes audit logic
- JSONB `details` captures full before/after state
- Indexed by user, action, timestamp for compliance queries
- Future: Consider partitioning by month for long-term retention
```

### Context: task-i1-t8 (from 02_Iteration_I1.md)

```markdown
*   **Task 1.8: Initialize Alembic for Database Migrations**
    *   **Task ID:** `I1.T8`
    *   **Description:** Initialize Alembic in backend directory with `alembic init alembic`. Configure `backend/alembic.ini` to use environment variable for database URL. Modify `backend/alembic/env.py` to: import SQLAlchemy models from `app.models`, read database URL from environment variable `DATABASE_URL`, use async engine (asyncpg). Create initial migration `001_initial_schema` that generates the same schema as `initial_schema.sql` from I1.T4 (using Alembic auto-generate or manual revision). Test migration: `alembic upgrade head` should create all tables.
    *   **Agent Type Hint:** `BackendAgent` or `DatabaseAgent`
    *   **Inputs:** Database schema from I1.T4; SQLAlchemy ORM best practices.
    *   **Input Files:** [`docs/api/initial_schema.sql`]
    *   **Target Files:**
        *   `backend/alembic.ini`
        *   `backend/alembic/env.py`
        *   `backend/alembic/versions/001_initial_schema.py` (migration file)
    *   **Deliverables:** Configured Alembic with initial migration; migration script that creates database schema.
    *   **Acceptance Criteria:**
        *   `alembic upgrade head` (run from backend directory) creates all 6 tables in database
        *   `alembic downgrade base` successfully drops all tables
        *   `alembic history` shows migration 001_initial_schema
        *   `env.py` reads DATABASE_URL from environment variable (e.g., `os.getenv("DATABASE_URL")`)
        *   Migration file includes all CREATE TABLE statements matching `initial_schema.sql`
        *   No errors when running migration against PostgreSQL 15
    *   **Dependencies:** `I1.T4` (schema definition), `I1.T5` (docker-compose with database), `I1.T6` (Alembic dependency installed)
    *   **Parallelizable:** No (requires database to be running)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `docs/api/initial_schema.sql`
    *   **Summary:** This is the complete SQL DDL script that defines all 6 database tables (users, vehicles, commands, responses, sessions, audit_logs) with proper PostgreSQL 15 syntax, including extensions (pgcrypto), all indexes (21 total), constraints, comments, and seed data (2 users, 2 vehicles).
    *   **Recommendation:** You MUST ensure your Alembic migration creates the EXACT same schema as this file. The migration should generate CREATE TABLE statements that match this schema precisely, including data types (UUID, VARCHAR lengths, JSONB, TIMESTAMP WITH TIME ZONE), constraints (CHECK, UNIQUE, NOT NULL, CASCADE), and all indexes. You can reference this file directly when creating the migration.
    *   **Critical Detail:** The schema includes the pgcrypto extension for UUID generation (`gen_random_uuid()`). Your migration must create this extension first.
    *   **Seed Data Note:** The SQL file includes seed data INSERT statements. For now, you may EXCLUDE the seed data from the Alembic migration (as it's typically managed separately), but ensure the tables are ready to accept that data structure.

*   **File:** `backend/requirements.txt`
    *   **Summary:** Contains all production dependencies including `alembic>=1.12.0`, `sqlalchemy>=2.0.0`, and `asyncpg>=0.29.0` (the async PostgreSQL driver).
    *   **Recommendation:** These dependencies are already installed. You MUST use SQLAlchemy 2.0 async syntax throughout your implementation, particularly `create_async_engine` and async session management in `env.py`.

*   **File:** `backend/pyproject.toml`
    *   **Summary:** Contains strict type checking and linting configurations (mypy in strict mode, ruff, black).
    *   **Recommendation:** Your generated code MUST pass `mypy --strict`, `ruff check`, and `black` without errors. Pay special attention to type hints in your `env.py` file.

*   **File:** `docker-compose.yml`
    *   **Summary:** Defines the local development environment with PostgreSQL 15 accessible at `localhost:5432` (from host) or `db:5432` (from containers). Database credentials are: `sovd_user` / `sovd_pass` / `sovd` database name. The backend service has `DATABASE_URL=postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd` environment variable.
    *   **Recommendation:** Your `alembic.ini` and `env.py` MUST read the DATABASE_URL from the environment. Do NOT hardcode the connection string. The format must be `postgresql+asyncpg://` for async support.

*   **File:** `backend/app/main.py`
    *   **Summary:** Basic FastAPI application with placeholder health check and CORS middleware. Currently has no database integration.
    *   **Recommendation:** You do NOT need to modify this file for the current task. Your Alembic setup should be independent and executed via the `alembic` CLI tool.

*   **File:** `docs/diagrams/erd.puml`
    *   **Summary:** PlantUML ERD that visually documents all 6 entities, their fields, data types, constraints, foreign key relationships, and indexes. This is the visual representation of the schema defined in `initial_schema.sql`.
    *   **Recommendation:** Use this diagram as a reference to understand the entity relationships and verify your migration creates all foreign keys correctly. The diagram explicitly shows CASCADE behavior for foreign keys.

*   **File:** `scripts/init_db.sh`
    *   **Summary:** Comprehensive bash script that initializes the database using the `initial_schema.sql` file. It includes health checks, verification, and detailed output.
    *   **Recommendation:** This script is an ALTERNATIVE to Alembic for initial database setup. Your Alembic migration should produce the same result as running this script. You can use this script's verification logic (checking table count, index count, seed data) as a guide for testing your migration.

### Implementation Tips & Notes

*   **Tip:** When you run `alembic init alembic`, Alembic will create the `alembic/` directory with `env.py`, `script.py.mako`, and `alembic.ini`. You will need to HEAVILY modify `env.py` to support async SQLAlchemy 2.0.
*   **Critical:** The `env.py` file MUST use `create_async_engine` and `AsyncConnection` from SQLAlchemy 2.0. DO NOT use the default synchronous engine. The default `env.py` template uses sync code - you must replace it with async patterns.
*   **Note:** Since no SQLAlchemy ORM models exist yet (task I1.T9 creates them), you will NOT be able to use Alembic's auto-generate feature for this initial migration. You should create a MANUAL migration using `alembic revision --rev-id="001" -m "initial_schema"` and write the `upgrade()` and `downgrade()` functions by hand based on `initial_schema.sql`.
*   **Warning:** The project uses SQLAlchemy 2.0 with type hints (`Mapped[]` syntax). When you eventually integrate models (in I1.T9), ensure your `env.py` imports `target_metadata` from the models' Base, but for THIS task, you can set `target_metadata = None` since you're doing a manual migration.
*   **Async Pattern:** Your `env.py` should have two functions: `run_migrations_offline()` (for generating SQL without DB connection) and `run_migrations_online()` (for executing against a live DB). The `run_migrations_online()` function MUST use `async with connectable.begin() as connection:` and `await connection.run_sync(do_run_migrations)`.
*   **Environment Variable:** Use `os.getenv("DATABASE_URL")` or `config.get_main_option("sqlalchemy.url")` with a fallback to the environment variable. The `alembic.ini` file should have a placeholder like `sqlalchemy.url = ${DATABASE_URL}` but this doesn't work directly - you need to programmatically read it in `env.py`.
*   **Testing:** After creating your migration, test it by running:
    1. `docker-compose up -d db redis` (start only the database)
    2. `cd backend`
    3. `export DATABASE_URL=postgresql+asyncpg://sovd_user:sovd_pass@localhost:5432/sovd`
    4. `alembic upgrade head` (should create tables)
    5. `alembic downgrade base` (should drop tables)
    6. Verify with `psql` that tables exist after upgrade and are gone after downgrade
*   **Index Creation:** Your migration MUST create all 21 indexes from `initial_schema.sql`. Use `op.create_index()` statements or raw `CREATE INDEX` statements via `op.execute()`.
*   **Extension Creation:** Your migration MUST create the pgcrypto extension at the beginning of the `upgrade()` function: `op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')`
*   **Comments:** While SQL comments (COMMENT ON TABLE/COLUMN) are nice to have, they are OPTIONAL for this task. Focus on getting the table structure and indexes correct first.
*   **Downgrade:** Your `downgrade()` function should drop all tables in reverse dependency order: audit_logs, sessions, responses, commands, vehicles, users. Use `op.drop_table()` and ensure you also drop indexes if needed (though CASCADE should handle most cleanup).

### Common Pitfalls to Avoid

*   **DO NOT** use the default synchronous `engine.connect()` pattern in `env.py` - it won't work with `postgresql+asyncpg://` URLs
*   **DO NOT** try to use Alembic's `--autogenerate` for this initial migration - you don't have ORM models yet
*   **DO NOT** hardcode the DATABASE_URL in `alembic.ini` or `env.py` - always read from environment
*   **DO NOT** forget to create the pgcrypto extension before creating tables (UUIDs won't work without it)
*   **DO NOT** forget to drop the extension in your `downgrade()` function
*   **DO NOT** create tables in the wrong order - respect foreign key dependencies (users and vehicles first, then commands, then responses)

### Success Criteria Checklist

Use this checklist to verify your implementation:

- [ ] `alembic init alembic` executed successfully
- [ ] `backend/alembic.ini` exists with DATABASE_URL configuration documented
- [ ] `backend/alembic/env.py` uses async SQLAlchemy 2.0 patterns
- [ ] `backend/alembic/env.py` reads DATABASE_URL from environment variable
- [ ] Migration `001_initial_schema.py` created in `versions/` directory
- [ ] Migration creates pgcrypto extension
- [ ] Migration creates all 6 tables with exact schema from `initial_schema.sql`
- [ ] Migration creates all 21+ indexes
- [ ] Migration includes proper `downgrade()` function
- [ ] `alembic upgrade head` completes without errors
- [ ] All 6 tables exist after upgrade
- [ ] `alembic downgrade base` completes without errors
- [ ] All tables dropped after downgrade
- [ ] `alembic history` shows the migration
- [ ] No mypy, ruff, or black errors in generated code
- [ ] Migration works with PostgreSQL 15

```json
{
  "task_id": "I1.T7",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Initialize frontend as React + TypeScript project using Vite. Create `frontend/package.json` with dependencies: `react@^18.2.0`, `react-dom@^18.2.0`, `react-router-dom@^6.20.0`, `@mui/material@^5.14.0`, `@mui/icons-material@^5.14.0`, `@emotion/react@^11.11.0`, `@emotion/styled@^11.11.0`, `@tanstack/react-query@^5.8.0` (React Query), `axios@^1.6.0` (HTTP client). DevDependencies: `@vitejs/plugin-react@^4.2.0`, `typescript@^5.3.0`, `vite@^5.0.0`, `vitest@^1.0.0`, `@testing-library/react@^14.1.0`, `@testing-library/jest-dom@^6.1.0`, `eslint@^8.54.0`, `eslint-plugin-react@^7.33.0`, `prettier@^3.1.0`. Create `frontend/tsconfig.json` with strict TypeScript configuration. Create `frontend/vite.config.ts` with React plugin. Create `frontend/.eslintrc.json` and `frontend/.prettierrc`.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Technology Stack from Plan Section 2.",
  "target_files": [
    "frontend/package.json",
    "frontend/tsconfig.json",
    "frontend/vite.config.ts",
    "frontend/.eslintrc.json",
    "frontend/.prettierrc"
  ],
  "input_files": [],
  "deliverables": "Complete frontend package.json with all dependencies; TypeScript and Vite configurations; ESLint and Prettier configurations.",
  "acceptance_criteria": "`npm install` (in frontend directory) succeeds without errors; All dependencies from Technology Stack included; `npm run dev` starts Vite dev server (can show blank page, acceptable); `npm run lint` runs ESLint without errors (on empty src directory); `npm run format` runs Prettier successfully; `npm run test` runs Vitest (can show no tests found, acceptable); `tsconfig.json` has `\"strict\": true`; `vite.config.ts` includes React plugin configuration",
  "dependencies": [
    "I1.T1"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: technology-stack (from 02_Architecture_Overview.md)

```markdown
<!-- anchor: technology-stack -->
### 3.2. Technology Stack Summary

<!-- anchor: stack-overview -->
#### Technology Selection Matrix

| **Layer/Concern** | **Technology** | **Justification** |
|-------------------|----------------|-------------------|
| **Frontend Framework** | React 18 + TypeScript | Industry-standard component model; TypeScript provides type safety; extensive ecosystem; strong community support; meets requirement. |
| **Frontend State Management** | React Context + React Query | React Query for server state (caching, sync); Context for auth/global UI state; avoids Redux complexity for this scale. |
| **Frontend Build** | Vite | Fast dev server and build times; superior to CRA; excellent TypeScript support; optimized production bundles. |
| **Frontend UI Library** | Material-UI (MUI) | Comprehensive component library; automotive industry precedent; accessibility built-in; professional appearance. |
| **Backend Framework** | Python FastAPI | Modern async framework; automatic OpenAPI generation (requirement); excellent WebSocket support; superior performance for I/O-bound operations; type hints align with TypeScript frontend. |
| **Backend Language** | Python 3.11+ | FastAPI requirement; strong async/await support; extensive library ecosystem; type hints for maintainability. |
| **API Style** | REST (OpenAPI 3.1)| Requirements explicitly request OpenAPI/Swagger docs; RESTful design well-understood; mature tooling. |
| **Real-Time Communication** | WebSocket | Requirement for streaming responses; bidirectional; well-supported in browsers and FastAPI. |
| **Database** | PostgreSQL 15+ | Required by spec; ACID compliance for audit logs; excellent JSON support (JSONB for command params/responses); proven scalability; robust backup/replication. |
| **Database ORM** | SQLAlchemy 2.0 + Alembic | Industry-standard Python ORM; async support; type-safe; Alembic for migrations. |
| **Authentication** | JWT (JSON Web Tokens) | Stateless; scalable; industry standard; supported by FastAPI middleware. |
| **Auth Library** | python-jose + passlib | JWT encoding/decoding; secure password hashing (bcrypt); widely adopted. |
| **Vehicle Communication** | gRPC (primary) + WebSocket (fallback) | gRPC for efficiency and strong typing (protobuf); WebSocket fallback for firewall compatibility; both support streaming. |
| **API Gateway/Proxy** | Nginx (production) + Uvicorn (dev) | Nginx for TLS termination, static file serving, load balancing; Uvicorn ASGI server for FastAPI. |
| **Containerization** | Docker + Docker Compose | Required by spec; industry standard; excellent local dev experience. |
| **Container Orchestration** | Kubernetes (K8s) | Cloud-agnostic; auto-scaling; health checks; self-healing; strong AWS EKS integration. |
| **Logging** | structlog + JSON formatter | Structured logging for machine parsing; integrates with ELK/CloudWatch; correlation IDs for tracing. |
| **Monitoring** | Prometheus + Grafana | Open-source; excellent Kubernetes integration; custom metrics for SOVD operations; alerting. |
| **Distributed Tracing** | OpenTelemetry + Jaeger | Cloud-agnostic; trace requests across frontend → backend → vehicle; performance analysis. |
| **Secrets Management** | AWS Secrets Manager (cloud) + Docker secrets (local) | Automatic rotation; IAM integration; audit logs; encrypted storage. |
| **CI/CD** | GitHub Actions | Requirements specify CI pipeline; free for public repos; excellent Docker integration; marketplace actions. |
| **Testing - Backend** | pytest + pytest-asyncio + httpx | Standard Python testing; async test support; FastAPI test client based on httpx. |
| **Testing - Frontend** | Vitest + React Testing Library | Vite-native; fast; compatible with Jest patterns; RTL for component testing. |
| **E2E Testing** | Playwright | Modern E2E testing; multi-browser; excellent debugging; auto-wait reduces flakiness. |
| **Code Quality - Frontend** | ESLint + Prettier + TypeScript | Requirements specified; catches errors; consistent formatting; type safety. |
| **Code Quality - Backend** | Ruff + Black + mypy | Requirements specified Ruff (linter); Black (formatter); mypy (type checking). |
| **API Documentation** | Swagger UI (auto-generated) | Requirement; FastAPI generates automatically; interactive testing; OpenAPI 3.1 spec. |
| **Cloud Platform (Primary)** | AWS | Strong automotive industry adoption; comprehensive service catalog; mature Kubernetes (EKS); IoT Core for vehicle connectivity. |
| **Cloud Services - Compute** | EKS (Elastic Kubernetes Service) | Managed Kubernetes; auto-scaling; integrates with ALB, IAM, CloudWatch. |
| **Cloud Services - Database** | RDS for PostgreSQL | Managed database; automated backups; read replicas; encryption at rest. |
| **Cloud Services - Load Balancer** | ALB (Application Load Balancer) | Layer 7 LB; WebSocket support; TLS termination; health checks; AWS WAF integration. |
| **Cloud Services - Object Storage** | S3 | Backup storage for audit log exports; static asset hosting (frontend build). |
| **Cloud Services - Networking** | VPC + Private Subnets | Secure network isolation; NAT Gateway for outbound vehicle communication. |
```

### Context: stack-rationale (from 02_Architecture_Overview.md)

```markdown
<!-- anchor: stack-rationale -->
#### Key Technology Decisions

**FastAPI over Node.js/Express:**
- Superior async/await model for handling concurrent vehicle connections
- Automatic OpenAPI generation saves development time
- Native WebSocket support crucial for streaming responses
- Type hints improve maintainability and align with TypeScript frontend philosophy
- Performance benchmarks show FastAPI competitive with Node.js for I/O-bound operations

**PostgreSQL over NoSQL:**
- Requirements suggest relational data (vehicles, commands, responses with foreign keys)
- ACID compliance critical for audit logs
- JSONB columns provide flexibility for variable command parameters while maintaining query capability
- Mature ecosystem for backups, replication, and monitoring

**gRPC for Vehicle Communication:**
- Efficient binary protocol reduces bandwidth (important for cellular connections)
- Strong typing with protobuf prevents protocol errors
- Native support for streaming (server-streaming for responses)
- HTTP/2 multiplexing reduces connection overhead
- WebSocket fallback handles restrictive firewall scenarios

**Kubernetes over Simpler Orchestration:**
- Future-proof: can scale from single instance to multi-region
- Cloud-agnostic (can migrate between AWS EKS, GCP GKE, Azure AKS)
- Rich ecosystem (Helm charts, operators, service mesh options)
- Auto-scaling based on load
- Self-healing for reliability

**Prometheus/Grafana over Cloud-Native Monitoring:**
- Cloud-agnostic (avoid vendor lock-in)
- Powerful query language (PromQL) for custom SOVD metrics
- Grafana provides automotive-specific dashboards
- Open-source reduces costs
- Can still integrate with CloudWatch for AWS-specific metrics
```

### Context: technology-stack (from 01_Plan_Overview_and_Setup.md)

```markdown
<!-- anchor: technology-stack -->
*   **Technology Stack:**
    *   **Frontend:** React 18, TypeScript, Material-UI (MUI), React Query (state management), Vite (build tool)
    *   **Backend:** Python 3.11+, FastAPI, Uvicorn (ASGI server), SQLAlchemy 2.0 (ORM), Alembic (migrations)
    *   **Database:** PostgreSQL 15+ (with JSONB for flexible command/response storage)
    *   **Caching/Messaging:** Redis 7 (session storage, Pub/Sub for real-time events, caching)
    *   **Vehicle Communication:** gRPC (primary) with WebSocket fallback for SOVD command transmission
    *   **API Gateway:** Nginx (production - TLS termination, load balancing, static files)
    *   **Authentication:** JWT (python-jose library, passlib for password hashing)
    *   **Containerization:** Docker, Docker Compose (local), Kubernetes/Helm (production)
    *   **CI/CD:** GitHub Actions
    *   **Monitoring:** Prometheus + Grafana, structlog for structured logging
    *   **Tracing:** OpenTelemetry + Jaeger
    *   **Secrets Management:** Docker secrets (local), AWS Secrets Manager (production)
    *   **Testing:** pytest + pytest-asyncio + httpx (backend), Vitest + React Testing Library (frontend), Playwright (E2E)
    *   **Code Quality:** Ruff + Black + mypy (backend), ESLint + Prettier + TypeScript (frontend)
    *   **Deployment:** AWS EKS (primary cloud target), with cloud-agnostic design
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/package.json`
    *   **Summary:** Currently contains minimal dependencies (React 18.2.0, React-DOM 18.2.0) with basic scripts (dev, build, preview, lint, test). DevDependencies include Vite, TypeScript, ESLint, and Vitest. The package is named "sovd-frontend" and marked as private.
    *   **Recommendation:** You MUST update this file to add ALL the missing production dependencies listed in the task description: `react-router-dom`, `@mui/material`, `@mui/icons-material`, `@emotion/react`, `@emotion/styled`, `@tanstack/react-query`, and `axios`. You MUST also add missing devDependencies: `@testing-library/react`, `@testing-library/jest-dom`, `eslint-plugin-react`, and `prettier`. PRESERVE the existing scripts structure but you MAY need to add a `format` script for Prettier.

*   **File:** `frontend/tsconfig.json`
    *   **Summary:** Existing TypeScript configuration already has `"strict": true` enabled, which meets one of the acceptance criteria. It uses ES2020 target, bundler module resolution, and react-jsx transform.
    *   **Recommendation:** This file is ALREADY compliant with task requirements. You do NOT need to modify it unless you want to ensure it aligns perfectly with TypeScript 5.3+ best practices. The strict mode is already enabled, which is critical.

*   **File:** `frontend/vite.config.ts`
    *   **Summary:** Vite configuration already includes the React plugin (`@vitejs/plugin-react`) and configures the dev server to run on host 0.0.0.0:3000 with HMR enabled.
    *   **Recommendation:** This file is ALREADY compliant with task requirements. The React plugin configuration is present, which satisfies the acceptance criteria. You do NOT need to modify this file.

*   **File:** `frontend/src/main.tsx` and `frontend/src/App.tsx`
    *   **Summary:** Minimal placeholder components are already in place. The app is functional and renders a basic UI showing the project status.
    *   **Recommendation:** These files are NOT part of your task's target files, so you should LEAVE THEM UNCHANGED. They are working correctly and will be enhanced in future tasks.

*   **File:** `backend/pyproject.toml`
    *   **Summary:** Contains Python tool configurations for Black, Ruff, mypy, pytest, and coverage. Uses 100 character line length, Python 3.11 target, and strict type checking.
    *   **Recommendation:** This file demonstrates the PROJECT STANDARD for code quality tool configuration. You SHOULD follow similar patterns when creating ESLint and Prettier configurations for the frontend. Note the strict settings and comprehensive coverage configuration.

*   **File:** `docker-compose.yml`
    *   **Summary:** Defines the complete local development environment with db, redis, backend, and frontend services. The frontend service is configured to run on port 3000 with volume mounting for hot reload and environment variable `VITE_API_URL=http://localhost:8000`.
    *   **Recommendation:** This file shows that the frontend development environment is ALREADY SET UP in Docker. After you complete your task, developers will use `npm install` inside the container to install the new dependencies. Ensure your package.json changes are compatible with the Docker setup.

### Implementation Tips & Notes

*   **Tip: Version Pinning Strategy**
    The task specifies exact version patterns like `^18.2.0` for dependencies. This uses caret (^) for compatible version ranges, which allows patch and minor version updates but not major version changes. You MUST preserve this pattern for consistency with the existing package.json structure.

*   **Tip: ESLint Configuration Pattern**
    Based on the backend's strict linting (Ruff with multiple rule sets), you SHOULD create an ESLint configuration that enforces TypeScript best practices. Include rules for React hooks, TypeScript type safety, and code consistency. Consider extending from `eslint:recommended`, `plugin:@typescript-eslint/recommended`, and `plugin:react/recommended`.

*   **Tip: Prettier Configuration Alignment**
    The backend uses Black with 100 character line length. For frontend consistency across the monorepo, you SHOULD configure Prettier with similar settings: `printWidth: 100`, `semi: true`, `singleQuote: true`, `tabWidth: 2`, and `trailingComma: 'es5'`.

*   **Tip: Testing Library Setup**
    The task requires `@testing-library/react` and `@testing-library/jest-dom`. These work with Vitest (already in devDependencies). You SHOULD ensure Vitest is configured to use jsdom environment for React component testing. This may require a `vitest.config.ts` or configuration in `vite.config.ts`.

*   **Note: Existing Scripts Analysis**
    Current package.json has:
    - `dev`: Uses Vite with `--host 0.0.0.0 --port 3000` (Docker compatible)
    - `build`: Standard Vite production build
    - `preview`: Vite preview server
    - `lint`: Runs ESLint with `.ts,.tsx` extensions
    - `test`: Runs Vitest

    You SHOULD add a `format` script that runs Prettier: `"format": "prettier --write \"src/**/*.{ts,tsx,json,css,md}\""` to meet the acceptance criteria that `npm run format` must work.

*   **Note: MUI Dependencies**
    Material-UI v5 requires both `@emotion/react` and `@emotion/styled` as peer dependencies. The task correctly includes these. Ensure the versions are compatible with `@mui/material@^5.14.0`.

*   **Warning: Node Modules in Docker**
    The docker-compose configuration mounts `./frontend:/app` which means node_modules will be inside the container. After you update package.json, the container will need to run `npm install` to install the new dependencies. This is normal and expected.

*   **Note: Acceptance Criteria Validation**
    The acceptance criteria states:
    - `npm install` must succeed → Test this inside the Docker container
    - `npm run dev` must start server → Already works, your changes shouldn't break this
    - `npm run lint` must run ESLint → Requires `.eslintrc.json` creation
    - `npm run format` must run Prettier → Requires adding script and `.prettierrc` creation
    - `npm run test` must run Vitest → Already works, should continue working
    - `tsconfig.json` must have `"strict": true` → Already satisfied
    - `vite.config.ts` must include React plugin → Already satisfied

### Missing Files That MUST Be Created

*   **frontend/.eslintrc.json** - Currently MISSING
    You MUST create this file with a comprehensive ESLint configuration that includes TypeScript support and React plugin.

*   **frontend/.prettierrc** - Currently MISSING
    You MUST create this file with Prettier formatting rules aligned with the project's backend formatting standards (100 character line length).

### Project Conventions Observed

1. **Documentation Comments:** All configuration files in the project include detailed comments explaining their purpose and configuration. You SHOULD follow this pattern when creating new config files.

2. **Strict Type Checking:** Both backend (mypy strict mode) and frontend (tsconfig strict: true) enforce strict type checking. This is a PROJECT STANDARD.

3. **100 Character Line Length:** The backend uses 100 characters (Black, Ruff). You SHOULD use the same for frontend Prettier configuration for consistency.

4. **Comprehensive Testing:** The project requires 80%+ test coverage. Your configuration should support this with proper testing library setup.

5. **Development Experience Focus:** The project prioritizes hot reload, fast builds (Vite), and developer productivity. Your configurations should not compromise these features.
