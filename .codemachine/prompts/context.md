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

### Context: Container Diagram - SOVD Command WebApp (from docs/diagrams/container_diagram.puml)

This PlantUML diagram shows the complete container architecture for the SOVD system. It defines all the major deployable containers you need to configure in docker-compose:

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml

LAYOUT_TOP_DOWN()

title Container Diagram - SOVD Command WebApp

Person(engineer, "Automotive Engineer", "Performs vehicle diagnostics")
System_Ext(vehicle, "Connected Vehicle", "SOVD 2.0 endpoint")
System_Ext(idp, "Identity Provider", "OAuth2/OIDC provider")

System_Boundary(sovd_system, "SOVD Command WebApp") {
  Container(web_app, "Web Application", "React 18, TypeScript, MUI", "Provides UI for authentication, vehicle selection, command execution, and response viewing")

  Container(api_gateway, "API Gateway", "Nginx", "Routes requests, terminates TLS, serves static files, load balances")

  Container(app_server, "Application Server", "FastAPI, Python 3.11", "Handles business logic: authentication, command validation, execution orchestration, response handling")

  Container(ws_server, "WebSocket Server", "FastAPI WebSocket", "Manages real-time streaming connections for command responses")

  Container(vehicle_connector, "Vehicle Connector", "Python, gRPC/WebSocket Client", "Abstracts vehicle communication protocols, handles retries, connection pooling")

  ContainerDb(postgres, "Database", "PostgreSQL 15", "Stores vehicles, commands, responses, users, sessions, audit logs")

  ContainerDb(redis, "Cache", "Redis 7", "Caches sessions, vehicle status, recent responses for performance")
}

Rel(engineer, web_app, "Uses", "HTTPS")
Rel(web_app, api_gateway, "Makes API calls", "HTTPS, JSON")
Rel(web_app, ws_server, "Opens WebSocket for streaming", "WSS")

Rel(api_gateway, app_server, "Routes requests to", "HTTP")
Rel(api_gateway, ws_server, "Routes WebSocket upgrade", "WebSocket Protocol")

Rel(app_server, postgres, "Reads/Writes", "SQL (asyncpg)")
Rel(app_server, redis, "Caches data", "Redis Protocol")
Rel(app_server, vehicle_connector, "Requests command execution", "Internal API")
Rel(app_server, idp, "Validates tokens", "OAuth2/OIDC")

Rel(ws_server, postgres, "Reads response data", "SQL (asyncpg)")
Rel(ws_server, redis, "Publishes/Subscribes to response events", "Redis Pub/Sub")

Rel(vehicle_connector, vehicle, "Sends SOVD commands, receives responses", "gRPC/WebSocket over TLS")
Rel(vehicle_connector, redis, "Publishes response events", "Redis Pub/Sub")
Rel(vehicle_connector, postgres, "Writes responses", "SQL (asyncpg)")

@enduml
```

**Key Insights from Diagram:**
- For local development, you can combine the Application Server, WebSocket Server, and Vehicle Connector into a single FastAPI backend service
- The API Gateway (Nginx) is not needed for local development - frontend and backend can communicate directly
- PostgreSQL 15 and Redis 7 are the data persistence layers required
- Backend needs connection strings to both PostgreSQL and Redis
- The system uses async PostgreSQL driver (asyncpg) and Redis Pub/Sub for real-time events

### Context: Database Schema (from docs/api/initial_schema.sql)

The database initialization script has already been created in task I1.T4. This defines the database structure and seed data:

**Database Configuration Requirements:**
- Database Name: `sovd`
- User: `sovd_user` (per task spec)
- Password: `sovd_pass` (per task spec)
- Port: 5432 (standard PostgreSQL)
- Total Tables: 6 (users, vehicles, commands, responses, sessions, audit_logs)
- Seed Data: 2 users (admin/admin123, engineer/engineer123) and 2 test vehicles

**Critical Database Details:**
- Uses PostgreSQL 15+ with `pgcrypto` extension for UUID generation
- All primary keys use UUID type with `gen_random_uuid()`
- 21+ indexes created for performance optimization
- Foreign keys with CASCADE/SET NULL delete behavior
- JSONB fields for flexible metadata storage
- Bcrypt-hashed passwords for authentication

**Database Connection URL Format:**
```
postgresql://sovd_user:sovd_pass@db:5432/sovd
```

### Context: Technology Stack (from README.md)

**Backend Stack Requirements:**
- Python 3.11+
- FastAPI framework
- Uvicorn ASGI server
- SQLAlchemy 2.0 (ORM)
- Alembic (migrations)
- asyncpg (async PostgreSQL driver)
- Redis Python client
- JWT authentication libraries
- Pydantic for validation

**Frontend Stack Requirements:**
- React 18 with TypeScript
- Vite (build tool and dev server)
- Material-UI components
- React Query for state management
- Port 3000 for development

**Infrastructure:**
- PostgreSQL 15+ database
- Redis 7 for caching and pub/sub
- Docker Compose for orchestration

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `scripts/init_db.sh`
- **Summary:** This is a comprehensive database initialization script with connection retry logic, schema execution, and verification functions. It expects to connect to PostgreSQL and execute the `docs/api/initial_schema.sql` file.
- **Recommendation:** You SHOULD reference this script's environment variable patterns when configuring the docker-compose database service. The script expects these environment variables:
  - `POSTGRES_HOST` (default: localhost)
  - `POSTGRES_PORT` (default: 5432)
  - `POSTGRES_DB` (default: sovd)
  - `POSTGRES_USER` (default: postgres)
  - `POSTGRES_PASSWORD` (required)
  - Alternatively: `DATABASE_URL` as a full connection string
- **Critical Detail:** The script has a 30-retry loop (60 seconds total) waiting for PostgreSQL to be ready. Your docker-compose health checks should be configured to handle this startup sequence.

#### File: `docs/api/initial_schema.sql`
- **Summary:** Complete SQL DDL script creating all 6 tables (users, vehicles, commands, responses, sessions, audit_logs) with 21+ indexes and seed data.
- **Recommendation:** This file will be executed by `init_db.sh` during database initialization. Your postgres container MUST have this file accessible via volume mount or initialization script.
- **Important:** The seed data includes hardcoded UUIDs for testing:
  - Admin user: `00000000-0000-0000-0000-000000000001`
  - Engineer user: `00000000-0000-0000-0000-000000000002`
  - Tesla vehicle: `00000000-0000-0000-0000-000000000101`
  - BMW vehicle: `00000000-0000-0000-0000-000000000102`

#### File: `Makefile`
- **Summary:** Provides convenience targets for common operations. Currently has placeholder implementations for `make up` and `make down`.
- **Recommendation:** The acceptance criteria states that `make up` should execute `docker-compose up -d` and `make down` should execute `docker-compose down`. The current Makefile already has these targets but includes placeholder detection logic that you should remove.
- **Action Required:** Once you create the real docker-compose.yml, the Makefile's `up` target should work correctly as-is, but you should remove the placeholder detection logic on lines 14-16.

#### File: `docker-compose.yml` (current)
- **Summary:** Contains only a placeholder `hello-world` service and empty network/volume definitions.
- **Recommendation:** You MUST completely replace this file's content while preserving the version, networks, and volumes structure. The existing `sovd-network` bridge network and `db_data` volume should be maintained.

#### File: `backend/requirements.txt`
- **Summary:** Currently contains only comments listing the planned dependencies. NOT YET POPULATED.
- **Recommendation:** While not strictly required for this task, you SHOULD be aware that the backend Dockerfile will need to handle the case where requirements.txt might be incomplete. Use a minimal placeholder or skip pip install if the file is empty.
- **Future Note:** Task I1.T6 will populate this file with actual dependencies.

#### File: `frontend/package.json`
- **Summary:** Minimal package.json with only basic metadata and script definitions. No dependencies listed yet.
- **Recommendation:** Similar to backend requirements, the frontend Dockerfile should handle the case where package.json has no dependencies. You can use `npm install` which will succeed even with an empty dependencies object.
- **Future Note:** Task I1.T7 will add all React dependencies.

#### File: `.gitignore`
- **Summary:** Comprehensive gitignore covering Python, Node.js, databases, IDEs, and build artifacts.
- **Recommendation:** The `.gitignore` already excludes `db_data/` (line 22), which matches the volume name in your docker-compose. No changes needed, but be aware that the database persistence directory won't be committed to git.

### Directory Structure Context

```
sovd-command-webapp/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── ...
│   ├── tests/
│   ├── requirements.txt (empty placeholder)
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── api/
│   │   └── ...
│   ├── public/
│   └── package.json (minimal)
├── docs/
│   ├── api/
│   │   └── initial_schema.sql ✓
│   └── diagrams/ ✓
├── scripts/
│   └── init_db.sh ✓
├── docker-compose.yml (placeholder)
├── Makefile ✓
└── README.md ✓
```

### Implementation Tips & Notes

#### **Tip #1: Database Service Health Check**
The PostgreSQL official Docker image includes `pg_isready` which is the recommended way to check database health. Your health check should look like:
```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U sovd_user -d sovd"]
  interval: 5s
  timeout: 5s
  retries: 5
```

#### **Tip #2: Redis Health Check**
Redis health checks should use `redis-cli ping` which returns "PONG" when ready:
```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 5s
  timeout: 3s
  retries: 5
```

#### **Tip #3: Backend Database Connection**
The backend needs the DATABASE_URL environment variable in this exact format:
```
postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd
```
Note the `+asyncpg` driver specification, which is required for SQLAlchemy async operations. The hostname should be `db` (the service name in docker-compose), not `localhost`.

#### **Tip #4: Hot Reload Volume Mounts**
For development hot reload to work:
- Backend: Mount `./backend:/app` and set working directory to `/app`
- Frontend: Mount `./frontend:/app` with working directory `/app`
- Both services should have `stdin_open: true` and `tty: true` for interactive development

#### **Tip #5: Service Dependencies**
Use `depends_on` with health conditions to ensure proper startup order:
```yaml
backend:
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
```

#### **Tip #6: Dockerfile for Backend (Development)**
The backend Dockerfile should be minimal for development mode:
- Base: `python:3.11-slim` or `python:3.11-alpine`
- Install system dependencies if needed (e.g., `postgresql-dev`, `gcc` for psycopg2)
- Set working directory to `/app`
- Copy requirements.txt and run `pip install` (handle empty file gracefully)
- Expose port 8000
- CMD should use uvicorn with `--reload` flag for hot reload
- Example: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

#### **Tip #7: Dockerfile for Frontend (Development)**
The frontend Dockerfile should use Node.js:
- Base: `node:18-alpine` or `node:20-alpine`
- Set working directory to `/app`
- Copy package.json and package-lock.json (if exists)
- Run `npm install`
- Expose port 3000
- CMD: `npm run dev -- --host 0.0.0.0` (Vite needs --host for Docker networking)

#### **Tip #8: Network Configuration**
Keep the existing `sovd-network` bridge network. All services should be connected to this network to enable inter-service communication by service name (e.g., backend can reach `db:5432`).

#### **Warning #1: Database Initialization Timing**
The backend service will likely fail on first startup because the database tables don't exist yet. The `init_db.sh` script needs to be run manually after the database is up, or you should add an initialization service to docker-compose that runs the script. Consider adding a comment in docker-compose explaining this limitation.

#### **Warning #2: Empty Dependencies**
Since requirements.txt and package.json are currently empty/minimal, the Docker builds will succeed but the applications won't actually run yet. This is expected - tasks I1.T6 and I1.T7 will populate these files. Your Dockerfiles should handle this gracefully without failing the build.

#### **Warning #3: Port Conflicts**
Ensure ports 3000 (frontend), 8000 (backend), 5432 (postgres), and 6379 (redis) are not already in use on the host system. The acceptance criteria requires these services to be accessible on localhost at these ports.

#### **Note #1: Volume Persistence**
The `db_data` volume ensures database persistence across container restarts. This is critical for development workflow - developers shouldn't lose their data when restarting services.

#### **Note #2: Environment Variable Documentation**
Add comments in docker-compose.yml documenting all environment variables, especially:
- Database connection parameters
- Redis URL
- Any future API keys or secrets
This will help developers understand the configuration without reading external docs.

#### **Note #3: Container Naming**
Consider using the `container_name` property for each service to make `docker ps` output more readable:
- `sovd-db`
- `sovd-redis`
- `sovd-backend`
- `sovd-frontend`

#### **Critical Acceptance Criteria Checklist**
To pass all acceptance criteria, ensure:
1. ✅ All 4 services defined (db, redis, backend, frontend)
2. ✅ PostgreSQL accessible on `localhost:5432` with credentials `sovd_user/sovd_pass`
3. ✅ Redis accessible on `localhost:6379`
4. ✅ Health checks configured for db and redis
5. ✅ Volume mounts enable hot reload (verify by changing a file after startup)
6. ✅ `make up` starts services in detached mode
7. ✅ `make down` stops and removes containers
8. ✅ Backend can connect to database and redis (check logs for connection messages)
9. ✅ Services start without errors (verify with `docker-compose ps` showing all "Up" states)

---

## 4. Additional Context & Resources

### Related Task Dependencies

This task depends on:
- **I1.T1** ✅ (Complete): Project structure and basic configuration files created
- **I1.T4** ✅ (Complete): Database schema SQL file created at `docs/api/initial_schema.sql`

This task blocks:
- **I1.T6**: Backend Python environment setup (needs working container to install dependencies)
- **I1.T7**: Frontend Node environment setup (needs working container to install dependencies)
- **I1.T8**: Alembic initialization (needs working database container)

### Documentation to Update

After completing this task, you should add to the README.md a section explaining:
- How to initialize the database using `init_db.sh` script
- Expected startup sequence and timing
- How to verify all services are running correctly
- Troubleshooting common issues (port conflicts, volume permissions, etc.)

### Testing Your Implementation

To verify your docker-compose.yml works correctly:

1. **Start Services:**
   ```bash
   make up
   # or
   docker-compose up -d
   ```

2. **Check Service Status:**
   ```bash
   docker-compose ps
   # All services should show "Up" or "Up (healthy)"
   ```

3. **Verify PostgreSQL:**
   ```bash
   docker-compose exec db psql -U sovd_user -d sovd -c "SELECT version();"
   # Should return PostgreSQL version info
   ```

4. **Verify Redis:**
   ```bash
   docker-compose exec redis redis-cli ping
   # Should return "PONG"
   ```

5. **Check Backend Logs:**
   ```bash
   docker-compose logs backend
   # Should show uvicorn starting (may show connection errors if app not yet implemented)
   ```

6. **Check Frontend Logs:**
   ```bash
   docker-compose logs frontend
   # Should show Vite dev server starting
   ```

7. **Initialize Database:**
   ```bash
   POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh
   ```

8. **Test Hot Reload:**
   - Modify a file in `backend/app/` or `frontend/src/`
   - Check logs to see if the service automatically reloaded

### Success Criteria Summary

Your implementation is complete when:
- ✅ `docker-compose up` starts 4 services without errors
- ✅ All services reach "healthy" or "running" state
- ✅ Database is accessible and accepts connections
- ✅ Redis is accessible and responds to ping
- ✅ Volume mounts enable hot reload
- ✅ Services can be stopped with `make down`
- ✅ Database data persists across restarts (test by inserting data, stopping, starting)

Good luck with the implementation! Remember to add comprehensive comments in the docker-compose.yml explaining the purpose of each service and configuration option.
