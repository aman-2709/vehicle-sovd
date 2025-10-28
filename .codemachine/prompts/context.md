# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T5",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Create complete `docker-compose.yml` for local development environment. Services: `db` (postgres:15 image, environment variables for database name `sovd`, user `sovd_user`, password `sovd_pass`, volume mount for persistence `db_data`), `redis` (redis:7 image, port 6379 exposed), `backend` (build from `./backend`, depends_on db and redis, environment variables for DATABASE_URL and REDIS_URL, volume mount `./backend:/app` for hot reload, port 8000 exposed), `frontend` (build from `./frontend`, volume mount `./frontend:/app`, port 3000 exposed). Configure health checks for db and redis. Add comments explaining each service configuration.",
  "agent_type_hint": "SetupAgent",
  "inputs": "Plan Section 3 (Directory Structure); Architecture Blueprint Section 3.9 (Deployment View - Development Environment).",
  "target_files": [
    "docker-compose.yml",
    "backend/Dockerfile",
    "frontend/Dockerfile"
  ],
  "input_files": [],
  "deliverables": "Functional docker-compose.yml with all services; minimal Dockerfiles for backend and frontend (development mode); documented environment variables.",
  "acceptance_criteria": "`docker-compose up` starts all 4 services without errors (db, redis, backend, frontend); PostgreSQL accessible on localhost:5432 with credentials from docker-compose.yml; Redis accessible on localhost:6379; Backend service can connect to database and redis (verified by logs); Volume mounts enable hot reload (changing files reflects without rebuild); Health checks pass for db and redis; `make up` in Makefile executes `docker-compose up -d`; `make down` executes `docker-compose down`",
  "dependencies": [
    "I1.T1",
    "I1.T4"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: deployment-view (from Architecture Blueprint Section 3.9)

Based on the Architecture Manifest, the Deployment View section covers the target environment, deployment strategy for development and production, and CI/CD pipeline details.

**Key Requirements for Development Environment:**

1. **Docker Compose orchestration** for local development
2. **Four core services:**
   - **PostgreSQL 15+** - Primary relational database
   - **Redis 7** - Cache and Pub/Sub messaging
   - **Backend (FastAPI)** - Application server with hot reload
   - **Frontend (React+Vite)** - Development server with HMR

3. **Service Configuration Requirements:**
   - Database: postgres:15 image, sovd database, sovd_user/sovd_pass credentials
   - Redis: redis:7 image, port 6379, persistence enabled
   - Backend: Built from ./backend, depends on db+redis, env vars for connections, port 8000
   - Frontend: Built from ./frontend, port 3000, Vite dev server

4. **Development Features:**
   - Volume mounts for hot reload (backend: ./backend:/app, frontend: ./frontend:/app)
   - Health checks for db and redis to ensure service readiness
   - Network isolation via Docker networks
   - Persistent volumes for database data

### Context: technology-stack (from Architecture Blueprint Section 2)

**Backend Stack:**
- Python 3.11+
- FastAPI (async web framework)
- Uvicorn (ASGI server)
- SQLAlchemy 2.0 (ORM)
- Asyncpg (PostgreSQL async driver)
- Redis Python client

**Frontend Stack:**
- React 18
- TypeScript
- Vite (build tool with HMR)
- Node 20

**Infrastructure:**
- PostgreSQL 15+ (primary database)
- Redis 7 (caching, session storage, Pub/Sub)
- Docker/Docker Compose (local development)
- Kubernetes/Helm (production deployment)

### Context: directory-structure (from Plan Section 3)

**Root Directory Structure:**
```
sovd-command-webapp/
├── backend/               # Python FastAPI backend
│   ├── app/              # Application code
│   ├── tests/            # Backend tests
│   ├── Dockerfile        # Development Dockerfile
│   ├── requirements.txt  # Python dependencies
│   └── pyproject.toml    # Python project config
├── frontend/             # React TypeScript frontend
│   ├── src/              # Source code
│   ├── public/           # Static assets
│   ├── tests/            # Frontend tests
│   ├── Dockerfile        # Development Dockerfile
│   └── package.json      # Node.js dependencies
├── infrastructure/       # Deployment configs
├── docs/                # Documentation
├── scripts/             # Utility scripts
├── tests/               # E2E tests
├── docker-compose.yml   # Development orchestration
├── Makefile            # Build automation
└── README.md           # Project documentation
```

### Context: communication-patterns (from Architecture Blueprint Section 3.7)

**Internal Service Communication:**
- Backend ↔ Database: PostgreSQL wire protocol over TCP
- Backend ↔ Redis: Redis protocol over TCP
- Frontend ↔ Backend: HTTP/REST over port 8000
- Backend internal: Redis Pub/Sub for event-driven communication

**Connection Requirements:**
- DATABASE_URL format: `postgresql+asyncpg://user:password@host:port/database`
- REDIS_URL format: `redis://host:port/db`
- All connections must be configurable via environment variables

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `docker-compose.yml` (Line 1-24)
- **Summary:** This file currently contains a placeholder configuration with a single "hello-world" service. It includes the correct version (3.8), network definition (sovd-network), and volume definition (db_data).
- **Recommendation:** You MUST replace the placeholder service with the four required services (db, redis, backend, frontend) while preserving the existing network and volume configurations.
- **Important Notes:**
  - The comments on lines 12-16 list exactly the services you need to add
  - The network "sovd-network" is already defined and should be used by all services
  - The volume "db_data" is already defined and should be mounted to PostgreSQL

#### File: `backend/Dockerfile` (Line 1-62)
- **Summary:** This is a well-structured development Dockerfile for the FastAPI backend. It uses python:3.11-slim base image, installs PostgreSQL client tools, sets up hot reload with uvicorn, and includes comprehensive health checks.
- **Recommendation:** This Dockerfile is ALREADY COMPLETE and suitable for the task. You do NOT need to modify it. Reference it in docker-compose.yml with `build: ./backend` and `dockerfile: Dockerfile`.
- **Key Features Already Implemented:**
  - Hot reload enabled (line 61: `--reload` flag)
  - Volume mount ready (watches /app directory)
  - Health check configured (line 50-51)
  - Port 8000 exposed (line 46)
  - PostgreSQL and Redis client libraries supported (line 22-27)

#### File: `frontend/Dockerfile` (Line 1-57)
- **Summary:** This is a well-configured development Dockerfile for the React frontend using Node 20 Alpine. It includes Vite dev server setup, HMR support, and health checks.
- **Recommendation:** This Dockerfile is ALREADY COMPLETE and ready for use. Reference it in docker-compose.yml with `build: ./frontend` and `dockerfile: Dockerfile`.
- **Key Features Already Implemented:**
  - Vite dev server with HMR (line 56)
  - Host 0.0.0.0 for Docker networking (line 56)
  - Port 3000 exposed (line 42)
  - Health check configured (line 46-47)
  - Volume mount ready (watches /app directory)

#### File: `Makefile` (Line 1-41)
- **Summary:** The Makefile contains predefined targets for common operations. The `up` and `down` targets are already configured correctly.
- **Recommendation:** You MUST ensure your docker-compose.yml works with the existing Makefile commands. Specifically:
  - Line 14: `make up` runs `docker-compose up -d` (detached mode)
  - Line 18: `make down` runs `docker-compose down`
- **Important:** The -d flag means services should run in background. Ensure your services are configured to handle this properly.

#### File: `scripts/init_db.sh` (Line 1-364)
- **Summary:** This is a comprehensive database initialization script that connects to PostgreSQL, executes the schema SQL file, and verifies the setup. It supports both individual connection parameters and DATABASE_URL.
- **Recommendation:** Your docker-compose.yml MUST provide the correct PostgreSQL connection parameters that this script expects. The script defaults are:
  - POSTGRES_HOST: localhost (line 31)
  - POSTGRES_PORT: 5432 (line 32)
  - POSTGRES_DB: sovd (line 33)
  - POSTGRES_USER: postgres (line 34)
  - POSTGRES_PASSWORD: [required via env] (line 35)
- **Critical:** The script looks for the SQL file at `$PROJECT_ROOT/docs/api/initial_schema.sql` (line 44). This file EXISTS and is ready.

#### File: `docs/api/initial_schema.sql` (Line 1-367)
- **Summary:** This is a complete, production-ready SQL schema with 6 tables (users, vehicles, commands, responses, sessions, audit_logs), 21 indexes, and seed data for 2 users and 2 vehicles.
- **Recommendation:** This schema is ready for use. Your docker-compose.yml should ensure PostgreSQL is running with the correct database name (sovd) so this script can be executed successfully.
- **Important:** The seed data includes:
  - Admin user: admin/admin123 (UUID: 00000000-0000-0000-0000-000000000001)
  - Engineer user: engineer/engineer123 (UUID: 00000000-0000-0000-0000-000000000002)
  - Two test vehicles with VINs: TESTVIN0000000001, TESTVIN0000000002

#### File: `README.md` (Line 53-241)
- **Summary:** The README contains detailed documentation about the expected docker-compose setup, including service descriptions, ports, credentials, and usage examples.
- **Recommendation:** You MUST ensure your docker-compose.yml matches ALL the specifications documented in the README, particularly:
  - Database credentials: sovd_user / sovd_pass (line 80, 91)
  - Database name: sovd (line 90)
  - Port mappings: frontend:3000, backend:8000, db:5432, redis:6379 (lines 77-81)
  - Volume names: sovd-db-data, sovd-redis-data (lines 92, 98)
  - Service names: db, redis, backend, frontend (lines 87-107)
- **Critical:** Lines 87-111 provide the EXACT service specifications you must implement.

### Implementation Tips & Notes

#### Tip #1: Environment Variable Configuration
Your docker-compose.yml MUST set the following environment variables for the backend service:
- `DATABASE_URL`: Should be in the format `postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd`
- `REDIS_URL`: Should be in the format `redis://redis:6379/0`
- `PYTHONUNBUFFERED`: Set to `1` (already in Dockerfile but can be reinforced)

Note: Use the Docker service name (`db`, `redis`) as hostnames, NOT `localhost`. Docker Compose creates a network where services can reference each other by name.

#### Tip #2: Service Dependencies and Health Checks
The README documentation (lines 87-111) specifies that:
- Backend depends on: db, redis (line 104)
- Frontend depends on: backend (line 110)

You MUST use `depends_on` with health check conditions to ensure proper startup order:
```yaml
depends_on:
  db:
    condition: service_healthy
  redis:
    condition: service_healthy
```

This ensures the backend waits for db and redis to be healthy before starting.

#### Tip #3: Volume Mounts for Hot Reload
The Dockerfiles are configured to watch the /app directory for changes. Your docker-compose.yml MUST mount:
- Backend: `./backend:/app` (enables uvicorn --reload to detect changes)
- Frontend: `./frontend:/app` (enables Vite HMR to detect changes)

IMPORTANT: Mount only the application directory, not the entire project root. This prevents unnecessary file watching and improves performance.

#### Tip #4: PostgreSQL Configuration
Based on the init_db.sh script analysis:
- The database must be created by PostgreSQL on startup
- Use the `POSTGRES_DB` environment variable to auto-create the database
- The credentials MUST match what's expected: sovd_user / sovd_pass
- The database name MUST be: sovd

PostgreSQL official image automatically creates a database if you provide these environment variables:
- `POSTGRES_DB=sovd`
- `POSTGRES_USER=sovd_user`
- `POSTGRES_PASSWORD=sovd_pass`

#### Tip #5: Redis Persistence
The README mentions "AOF persistence enabled" (line 97). You SHOULD add Redis command arguments to enable AOF:
```yaml
command: redis-server --appendonly yes
```

This ensures Redis data is persisted to the sovd-redis-data volume.

#### Tip #6: Health Check Configuration
Both Dockerfiles include health checks, but docker-compose.yml needs its own health check definitions for dependency management:

For PostgreSQL (db service):
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U sovd_user -d sovd"]
  interval: 10s
  timeout: 5s
  retries: 5
```

For Redis (redis service):
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 5s
  retries: 5
```

These checks ensure services are truly ready before dependents start.

#### Warning #1: Volume Name Consistency
The README specifies volume names as `sovd-db-data` and `sovd-redis-data` (lines 92, 98). However, your placeholder docker-compose.yml only defines `db_data`. You MUST:
1. Rename the existing volume from `db_data` to `sovd-db-data`
2. Add a new volume `sovd-redis-data` for Redis
3. Update the mount paths accordingly

#### Warning #2: Port Conflicts
The README troubleshooting section (lines 182-185) warns about port conflicts. Your docker-compose.yml SHOULD include clear comments about which ports are exposed and why, to help users identify conflicts quickly.

#### Note #1: Network Configuration
The placeholder docker-compose.yml defines a bridge network `sovd-network`. You SHOULD:
1. Keep this network definition
2. Add all four services to this network (either explicitly or by default)
3. This enables service-to-service communication via DNS names

#### Note #2: Restart Policies
For development, services SHOULD have restart policies to handle transient failures:
- Use `restart: unless-stopped` for db and redis (infrastructure services)
- Use `restart: on-failure` for backend and frontend (application services)

This ensures the development environment is resilient to temporary issues.

#### Note #3: Comments and Documentation
The task description explicitly requires: "Add comments explaining each service configuration." You MUST add:
1. A header comment explaining the purpose of the file
2. Per-service comments explaining each service's role
3. Comments for critical configuration options (environment variables, volumes, health checks)

#### Note #4: YAML Best Practices
Follow these YAML formatting standards:
- Use 2-space indentation (consistent with placeholder)
- Use `version: '3.8'` (already present)
- Keep the file organized: services, networks, volumes (in that order)
- Use quotes for string values with special characters
- Use YAML anchors/aliases if there's repeated configuration (optional but recommended)

---

## 4. Validation Checklist

Before completing the task, verify that your docker-compose.yml meets ALL these criteria:

### Service Configuration
- [ ] Four services defined: db, redis, backend, frontend
- [ ] All services connected to sovd-network
- [ ] PostgreSQL: postgres:15 image, sovd database, sovd_user/sovd_pass
- [ ] Redis: redis:7 image, port 6379, AOF persistence enabled
- [ ] Backend: builds from ./backend, ports 8000:8000, volume mounted
- [ ] Frontend: builds from ./frontend, ports 3000:3000, volume mounted

### Dependencies and Health Checks
- [ ] db service has pg_isready health check
- [ ] redis service has redis-cli ping health check
- [ ] backend depends_on db and redis with service_healthy condition
- [ ] frontend depends_on backend (optional: with service_healthy condition)

### Environment Variables
- [ ] Backend has DATABASE_URL set to postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd
- [ ] Backend has REDIS_URL set to redis://redis:6379/0
- [ ] PostgreSQL has POSTGRES_DB=sovd, POSTGRES_USER=sovd_user, POSTGRES_PASSWORD=sovd_pass

### Volumes and Persistence
- [ ] Volume sovd-db-data defined and mounted to /var/lib/postgresql/data in db service
- [ ] Volume sovd-redis-data defined and mounted to /data in redis service
- [ ] Backend source mounted: ./backend:/app
- [ ] Frontend source mounted: ./frontend:/app

### Documentation
- [ ] Header comment explaining the file's purpose
- [ ] Each service has explanatory comments
- [ ] Critical configuration options are documented
- [ ] Matches specifications in README.md (lines 87-111)

### Integration with Existing Files
- [ ] Works with `make up` (runs docker-compose up -d)
- [ ] Works with `make down` (runs docker-compose down)
- [ ] Compatible with scripts/init_db.sh expectations
- [ ] Backend Dockerfile not modified (already complete)
- [ ] Frontend Dockerfile not modified (already complete)

### Acceptance Criteria Validation
- [ ] `docker-compose up` starts all 4 services without errors
- [ ] PostgreSQL accessible on localhost:5432 with credentials sovd_user/sovd_pass
- [ ] Redis accessible on localhost:6379
- [ ] Backend can connect to database and redis (check logs)
- [ ] Volume mounts enable hot reload (test by editing a file)
- [ ] Health checks pass for db and redis (check with `docker-compose ps`)

---

## 5. Quick Reference: Expected Service Configuration

Use this as a quick reference for the exact specifications required:

### Database Service (db)
```
Image: postgres:15
Container Name: sovd-db (optional)
Environment:
  - POSTGRES_DB=sovd
  - POSTGRES_USER=sovd_user
  - POSTGRES_PASSWORD=sovd_pass
Ports: 5432:5432
Volume: sovd-db-data:/var/lib/postgresql/data
Healthcheck: pg_isready -U sovd_user -d sovd
Restart: unless-stopped
Network: sovd-network
```

### Cache Service (redis)
```
Image: redis:7
Container Name: sovd-redis (optional)
Command: redis-server --appendonly yes
Ports: 6379:6379
Volume: sovd-redis-data:/data
Healthcheck: redis-cli ping
Restart: unless-stopped
Network: sovd-network
```

### Backend Service (backend)
```
Build: ./backend
Context: ./backend
Dockerfile: Dockerfile
Container Name: sovd-backend (optional)
Environment:
  - DATABASE_URL=postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd
  - REDIS_URL=redis://redis:6379/0
Ports: 8000:8000
Volume: ./backend:/app
Depends On: db (healthy), redis (healthy)
Restart: on-failure
Network: sovd-network
```

### Frontend Service (frontend)
```
Build: ./frontend
Context: ./frontend
Dockerfile: Dockerfile
Container Name: sovd-frontend (optional)
Environment:
  - VITE_API_URL=http://localhost:8000 (optional)
Ports: 3000:3000
Volume: ./frontend:/app
Depends On: backend
Restart: on-failure
Network: sovd-network
```

### Networks
```
sovd-network:
  driver: bridge
```

### Volumes
```
sovd-db-data:
  driver: local
sovd-redis-data:
  driver: local
```

---

## End of Task Briefing Package

This comprehensive package provides everything you need to successfully complete task I1.T5. Review all sections carefully, follow the strategic guidance, and validate your implementation against the checklist before submission.
