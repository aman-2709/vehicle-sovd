# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T6",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Create `backend/requirements.txt` with pinned versions of core dependencies: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`, `sqlalchemy>=2.0.0`, `alembic>=1.12.0`, `asyncpg>=0.29.0` (PostgreSQL async driver), `redis>=5.0.0`, `python-jose[cryptography]>=3.3.0` (JWT), `passlib[bcrypt]>=1.7.4` (password hashing), `pydantic>=2.4.0`, `pydantic-settings>=2.0.0` (config management), `python-multipart>=0.0.6` (file uploads), `structlog>=23.2.0` (logging). Create `backend/requirements-dev.txt` with dev dependencies: `pytest>=7.4.0`, `pytest-asyncio>=0.21.0`, `httpx>=0.25.0` (async test client), `pytest-cov>=4.1.0` (coverage), `ruff>=0.1.0`, `black>=23.11.0`, `mypy>=1.7.0`. Configure `backend/pyproject.toml` with Black (line-length=100), Ruff (select rules: E, F, I), and mypy (strict mode) settings.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Technology Stack from Plan Section 2.",
  "target_files": [
    "backend/requirements.txt",
    "backend/requirements-dev.txt",
    "backend/pyproject.toml"
  ],
  "input_files": [],
  "deliverables": "Complete Python dependency files with pinned versions; pyproject.toml with linter/formatter configurations.",
  "acceptance_criteria": "`pip install -r backend/requirements.txt` succeeds without errors; `pip install -r backend/requirements-dev.txt` succeeds; All dependencies from Technology Stack included; Versions are pinned or use compatible release specifier (`>=` with minor version); `black backend/` runs without errors (even on empty directory); `ruff check backend/` runs without errors; `mypy backend/` runs (may show errors on empty directory, acceptable); `pyproject.toml` includes `[tool.black]`, `[tool.ruff]`, `[tool.mypy]` sections",
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

### Context: Technology Stack - Backend (from README.md)

```markdown
## Technology Stack

### Frontend
- **Framework:** React 18 with TypeScript
- **UI Library:** Material-UI (MUI)
- **State Management:** React Query
- **Build Tool:** Vite
- **Code Quality:** ESLint, Prettier, TypeScript

### Backend
- **Framework:** Python 3.11+ with FastAPI
- **Server:** Uvicorn (ASGI)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose, passlib)
- **Code Quality:** Ruff, Black, mypy

### Infrastructure
- **Database:** PostgreSQL 15+
- **Cache/Messaging:** Redis 7
- **Vehicle Communication:** gRPC (primary), WebSocket (fallback)
- **API Gateway:** Nginx (production)
- **Containerization:** Docker, Docker Compose (local), Kubernetes/Helm (production)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana, structlog
- **Tracing:** OpenTelemetry + Jaeger

### Testing
- **Backend:** pytest, pytest-asyncio, httpx
- **Frontend:** Vitest, React Testing Library
- **E2E:** Playwright
```

### Context: Project Goals and Non-Functional Requirements (from README.md)

```markdown
## Goals

- User authentication and role-based access control (Engineer, Admin roles)
- Vehicle registry with connection status monitoring
- SOVD command submission with parameter validation
- Real-time response streaming via WebSocket
- Command history and audit logging
- <2 second round-trip time for 95% of commands
- Support for 100+ concurrent users
- Secure communication (TLS, JWT, RBAC)
- Docker-based deployment ready for cloud platforms (AWS/GCP/Azure)
- 80%+ test coverage with CI/CD pipeline
- OpenAPI/Swagger documentation for all backend APIs
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/requirements.txt`
    *   **Summary:** This file currently contains minimal dependencies added during I1.T5 (docker-compose setup). It includes basic FastAPI, uvicorn, sqlalchemy, asyncpg, redis, and python-dotenv packages with version constraints.
    *   **Recommendation:** You MUST expand this file to include ALL dependencies specified in the task description with proper version pinning. The current file has a comment indicating it's minimal and will be completed in I1.T6 (this task).
    *   **Warning:** The current file uses relaxed version constraints (`>=`). You should maintain this pattern for consistency, using compatible release specifiers.

*   **File:** `backend/pyproject.toml`
    *   **Summary:** This file contains comprehensive configuration for Black, Ruff, mypy, pytest, and coverage. Black is configured with line-length=100 and target Python 3.11. Ruff has E, F, I, N, W, UP rules selected. mypy has strict settings enabled. pytest is configured with coverage reporting.
    *   **Recommendation:** You SHOULD verify that the existing configurations match the task requirements. The file already includes proper [tool.black], [tool.ruff], [tool.mypy] sections, but you may need to adjust Ruff rules (task specifies E, F, I only).
    *   **Note:** The task requires mypy "strict mode" settings. The current file has `disallow_untyped_defs = true` which is stricter than the baseline. You should verify this meets the "strict mode" requirement or adjust accordingly.

*   **File:** `backend/app/main.py`
    *   **Summary:** This is the FastAPI application entry point. It creates a minimal FastAPI app with health check endpoints, CORS middleware for localhost:3000, and startup/shutdown event handlers (currently just printing messages).
    *   **Recommendation:** This file imports `fastapi` which is already in requirements.txt. When testing the dependencies, verify that the existing application can still start with the new dependency versions.
    *   **Note:** The Dockerfile references this file as the entry point (`app.main:app`), so ensure compatibility is maintained.

*   **File:** `backend/Dockerfile`
    *   **Summary:** This is the development Dockerfile that installs dependencies from requirements.txt and runs uvicorn with hot reload. It uses Python 3.11-slim, installs PostgreSQL client libraries, and has a health check that calls `/health` endpoint.
    *   **Recommendation:** After updating requirements.txt, you SHOULD test that the Docker build succeeds. The Dockerfile has a fallback (`|| true`) if requirements.txt install fails, but proper dependencies should install cleanly.
    *   **Warning:** The Dockerfile installs system packages (gcc, python3-dev, libpq-dev) needed for compiling Python packages with C extensions. Ensure the new dependencies (especially cryptography for python-jose and bcrypt for passlib) can compile with these system packages.

*   **File:** `docker-compose.yml`
    *   **Summary:** This orchestrates all services including backend, frontend, PostgreSQL, and Redis. The backend service has environment variables for DATABASE_URL (postgresql+asyncpg://...) and REDIS_URL (redis://...).
    *   **Recommendation:** Your dependencies must support the connection strings configured here. Specifically, asyncpg is the PostgreSQL driver (already specified in task), and redis client must support the redis:// URL scheme.

*   **File:** `Makefile`
    *   **Summary:** The root Makefile has targets for `up`, `down`, `test`, and `lint`. The `lint` target runs `ruff check`, `black --check`, and `mypy` on the backend.
    *   **Recommendation:** After completing this task, you SHOULD verify that `make lint` runs successfully. The acceptance criteria require that these commands run without errors (even on empty directories).

### Implementation Tips & Notes

*   **Tip:** The task specifies version constraints like `>=0.104.0` which means "at least 0.104.0 but allow newer versions compatible with the same major.minor series". This is the preferred pattern for this project (already used in current requirements.txt).

*   **Tip:** When creating `requirements-dev.txt`, you should NOT duplicate production dependencies from `requirements.txt`. Development dependencies are typically installed alongside production dependencies using `pip install -r requirements.txt -r requirements-dev.txt`.

*   **Note:** The task mentions `pydantic-settings>=2.0.0` for configuration management. This is a separate package from `pydantic` starting in Pydantic v2. The current backend doesn't have configuration yet, but this will be needed for task I1.T10 (database session management with config module).

*   **Note:** The task requires `python-jose[cryptography]` (with the cryptography extra) for JWT handling. The `[cryptography]` extra provides more secure algorithms than the default. Make sure to include the bracket notation.

*   **Note:** Similarly, `passlib[bcrypt]` requires the bcrypt extra for bcrypt password hashing support. The `uvicorn[standard]` also uses bracket notation for additional features.

*   **Warning:** The acceptance criteria state that `mypy backend/` may show errors on empty directory, which is acceptable. Don't be alarmed if mypy complains about missing modules - this is expected since the backend implementation is still minimal.

*   **Tip:** The existing `pyproject.toml` already has a `[tool.pytest.ini_options]` section with coverage configured. This will be useful for future tasks that require 80%+ test coverage, but for this task you only need to ensure the tools can run.

*   **Tip:** The Ruff configuration currently selects rules: E, F, I, N, W, UP. The task description specifies only E, F, I. You SHOULD update the Ruff configuration to match the task specification exactly (remove N, W, UP rules).

*   **Note:** Black requires no additional configuration beyond what's already in pyproject.toml (line-length=100 is specified). Running `black backend/` on an empty or existing directory should succeed without errors.

*   **Critical:** The backend directory structure already exists with subdirectories (app/api, app/models, app/services, etc.) containing `__init__.py` files. When testing linters, they will scan these directories. Ensure the tools run cleanly on this existing structure.

*   **Testing Strategy:** To verify the acceptance criteria, you should:
    1. First, update requirements.txt with all production dependencies
    2. Create requirements-dev.txt with development dependencies
    3. Update pyproject.toml to adjust Ruff rules (remove N, W, UP)
    4. Test installation: `pip install -r backend/requirements.txt -r backend/requirements-dev.txt`
    5. Test linters: `black backend/`, `ruff check backend/`, `mypy backend/`
    6. Verify Docker build: `docker-compose build backend`

*   **Version Pinning Guidance:** Use the `>=` operator with major.minor.patch versions as specified in the task. This ensures minimum versions while allowing patch updates. For example: `fastapi>=0.104.0` means "at least 0.104.0 but 0.104.1, 0.104.2, etc. are acceptable".

### Project Structure Context

The backend directory structure is:
```
backend/
├── alembic/              # Database migration tools (empty, will be configured in I1.T8)
│   └── versions/
├── app/                  # Main application package
│   ├── api/             # API route handlers
│   │   └── v1/          # Version 1 API endpoints
│   ├── connectors/      # External system connectors (vehicles, etc.)
│   ├── middleware/      # Custom middleware
│   ├── models/          # SQLAlchemy ORM models (empty, will be created in I1.T9)
│   ├── repositories/    # Data access layer
│   ├── schemas/         # Pydantic request/response models
│   ├── services/        # Business logic layer
│   ├── utils/           # Utility functions
│   └── main.py          # FastAPI application entry point
├── tests/               # Test suite
│   ├── integration/     # Integration tests
│   └── unit/            # Unit tests
├── Dockerfile           # Development container image
├── requirements.txt     # Production dependencies (TO BE UPDATED)
├── requirements-dev.txt # Development dependencies (TO BE CREATED)
└── pyproject.toml       # Tool configurations (TO BE UPDATED)
```

All subdirectories have `__init__.py` files, making them proper Python packages. The linters will scan all these directories when run from the backend/ directory.

---

## End of Task Briefing Package

The Coder Agent should now have all the context needed to complete task I1.T6 successfully. This includes:
- The complete task specification with acceptance criteria
- Relevant architectural context from project documentation
- Detailed analysis of the existing codebase
- Strategic recommendations based on the current implementation
- Specific tips and warnings to avoid common pitfalls
