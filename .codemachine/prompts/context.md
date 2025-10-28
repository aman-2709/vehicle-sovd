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
  "description": "Create `backend/requirements.txt` with pinned versions of core dependencies: `fastapi>=0.104.0`, `uvicorn[standard]>=0.24.0`, `sqlalchemy>=2.0.0`, `alembic>=1.12.0`, `asyncpg>=0.29.0` (PostgreSQL async driver), `redis>=5.0.0`, `python-jose[cryptography]>=3.3.0` (JWT), `passlib[bcrypt]>=1.7.4` (password hashing), `pydantic>=2.4.0`, `pydantic-settings>=2.0.0` (config management), `python-multipart>=0.0.6` (file uploads), `structlog>=23.2.0` (logging). Create `backend/requirements-dev.txt` with dev dependencies: `pytest>=7.4.0`, `pytest-asyncio>=0.21.0`, `httpx>=0.25.0` (async test client), `pytest-cov>=4.1.0` (coverage), `ruff>=0.1.0`, `black>=23.11.0`, `mypy>=1.7.0`. Configure `backend/pyproject.toml` with Black (line-length=100), Ruff (select rules: E, F, I, N, W, UP), and mypy (strict mode) settings.",
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

### Context: plan-technology-stack (from 01_Plan_Overview_and_Setup.md)

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

### Context: key-technology-decisions (from 02_Architecture_Overview.md)

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

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/requirements.txt`
    *   **Summary:** Currently contains minimal dependencies with comments indicating this file is a placeholder for I1.T6. Contains basic FastAPI, uvicorn, asyncpg, sqlalchemy, redis, and python-dotenv with minimal version constraints.
    *   **Recommendation:** You MUST completely replace this file with the full pinned dependency list as specified in the task description. The current minimal dependencies were only for docker-compose startup in I1.T5.

*   **File:** `backend/pyproject.toml`
    *   **Summary:** Already has a basic structure with tool configurations for black, ruff, mypy, pytest, and coverage. Line length is set to 100, target Python version is 3.11, and basic linting rules are configured.
    *   **Recommendation:** You SHOULD review and ensure the existing configuration matches the task requirements. You MAY need to enhance the `[tool.ruff.lint]` section to include the specific rule codes (E, F, I, N, W, UP) and ensure mypy is configured with strict mode settings.

*   **File:** `backend/Dockerfile`
    *   **Summary:** This is the development Dockerfile that installs dependencies from requirements.txt. It has a fallback `|| true` in case requirements.txt is empty or minimal.
    *   **Recommendation:** After updating requirements.txt, this Dockerfile will properly install all dependencies during the next `docker-compose up --build`. No changes to the Dockerfile are needed for this task.

*   **File:** `backend/app/main.py`
    *   **Summary:** Contains a minimal FastAPI application with a health check endpoint and CORS middleware configured for the frontend.
    *   **Recommendation:** This file will remain unchanged for this task. Future tasks will add more functionality to this application entry point.

*   **File:** `docker-compose.yml`
    *   **Summary:** Orchestrates the complete development environment including db (PostgreSQL), redis, backend, and frontend services. The backend service mounts the source code for hot reload.
    *   **Recommendation:** No changes needed to docker-compose.yml for this task. The backend service will automatically pick up the new dependencies when rebuilt.

*   **File:** `Makefile`
    *   **Summary:** Contains targets for up, down, test, lint, and logs. The lint target already runs ruff, black, and mypy on the backend code.
    *   **Recommendation:** You can use `make lint` after completing this task to verify that the linting tools work correctly with the empty codebase.

### Implementation Tips & Notes

*   **Tip:** The pyproject.toml file already exists with reasonable defaults. You should **enhance** it rather than replace it completely. Specifically, verify that:
    - `[tool.black]` section has `line-length = 100` (already present)
    - `[tool.ruff.lint]` section has `select = ["E", "F", "I", "N", "W", "UP"]` (currently present, verify exact match)
    - `[tool.mypy]` section has strict mode settings like `disallow_untyped_defs = true` (already present)

*   **Tip:** For requirements.txt, the task specifies "pinned versions" which means using `>=` with specific versions. The current file uses this format already, so you should follow the same pattern but with the complete list of dependencies.

*   **Tip:** The task requires `pydantic-settings>=2.0.0` which is the new package name in Pydantic v2. Don't use the old `pydantic[dotenv]` syntax.

*   **Note:** The acceptance criteria states that running `black backend/` and `ruff check backend/` should succeed even on an empty directory. The current backend/app/ directory has minimal code (just main.py and __init__.py files), so these tools should run successfully once installed.

*   **Note:** The task specifies `python-jose[cryptography]>=3.3.0` with the cryptography extra, and `passlib[bcrypt]>=1.7.4` with the bcrypt extra. Make sure to include the extras in square brackets.

*   **Note:** The task mentions `python-multipart>=0.0.6` for file uploads. This is a FastAPI dependency for handling multipart form data, which will be needed for future features.

*   **Warning:** After updating requirements.txt, you will need to rebuild the backend Docker container with `docker-compose up -d --build backend` to install the new dependencies. The acceptance criteria require that the pip install commands succeed, which can be tested by running them inside the container or locally.

*   **Best Practice:** Create requirements-dev.txt as a separate file that includes ALL development dependencies. These should NOT be installed in production Docker builds. The current Dockerfile only installs from requirements.txt, which is correct.

*   **Best Practice:** The pyproject.toml file should be comprehensive enough to configure all the development tools mentioned (black, ruff, mypy, pytest). The existing configuration is a good foundation, but verify each tool section against the task requirements.

*   **Documentation Note:** The README.md mentions running tests and linters with `make test` and `make lint`. After this task, these commands should work correctly with the newly installed tools.

### File Creation Order

1. **First:** Update `backend/requirements.txt` with the complete list of pinned production dependencies
2. **Second:** Create `backend/requirements-dev.txt` with development and testing dependencies
3. **Third:** Enhance `backend/pyproject.toml` to ensure all tool configurations meet the task specifications
4. **Finally:** Test that the files are correct by attempting to install dependencies (either locally or by rebuilding the Docker container)

### Acceptance Criteria Verification

After completing this task, you should verify:

1. ✅ `pip install -r backend/requirements.txt` succeeds without errors
2. ✅ `pip install -r backend/requirements-dev.txt` succeeds without errors
3. ✅ All dependencies from the Technology Stack are included
4. ✅ Versions use `>=` with specific minor versions
5. ✅ `black backend/` runs without errors
6. ✅ `ruff check backend/` runs without errors
7. ✅ `mypy backend/` runs (errors on empty directory are acceptable)
8. ✅ `pyproject.toml` includes all required tool sections

The easiest way to verify these is to rebuild the backend container and run the make targets:
```bash
docker-compose up -d --build backend
docker-compose exec backend black app/
docker-compose exec backend ruff check app/
docker-compose exec backend mypy app/
```
