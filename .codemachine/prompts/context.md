# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T2",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Create PlantUML source files for Component Diagram (C4 Level 3 - Application Server internal components) and Container Diagram (C4 Level 2 - deployable containers). Component diagram must include: API Router, Auth Controller, Vehicle Controller, Command Controller, Auth Service, Vehicle Service, Command Service, Audit Service, SOVD Protocol Handler, Repository Layer (Vehicle/Command/Response/User repositories), Shared Kernel. Container diagram must include: Web App (React SPA), API Gateway (Nginx), Application Server (FastAPI), WebSocket Server (FastAPI embedded), Vehicle Connector, PostgreSQL, Redis. Include all relationships and communication protocols.",
  "agent_type_hint": "DiagrammingAgent",
  "inputs": "Architecture Blueprint Sections 3.4, 3.5; Plan Section 2 (Core Architecture); Technology Stack from Plan Section 2.",
  "target_files": [
    "docs/diagrams/component_diagram.puml",
    "docs/diagrams/container_diagram.puml"
  ],
  "input_files": [],
  "deliverables": "Two PlantUML `.puml` source files that render without syntax errors and accurately represent architecture.",
  "acceptance_criteria": "PlantUML files compile without errors (test with `plantuml -testdot` or online renderer); Component diagram shows all modules listed in description with correct dependencies; Container diagram shows all containers with communication protocols labeled; Diagrams match Architecture Blueprint diagrams in Sections 3.4 and 3.5; Files committed to `docs/diagrams/` directory",
  "dependencies": ["I1.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: container-diagram (from Architecture Blueprint - Section 3)

**C4 Level 2: Container Diagram - Deployable Containers**

The container diagram shows the major deployable containers and their interactions:

**Containers:**

1. **Web App (React SPA)**
   - Technology: React 18, TypeScript, Vite
   - Responsibilities: User interface, authentication UI, vehicle management UI, command submission UI, real-time response display
   - Deployed: Nginx serving static files
   - Port: 3000 (dev), 80/443 (prod)

2. **API Gateway (Nginx)**
   - Technology: Nginx
   - Responsibilities: Reverse proxy, load balancing, TLS termination, rate limiting, static file serving (frontend)
   - Configuration: Routes `/api/*` to Application Server, serves SPA at `/`
   - Port: 80/443

3. **Application Server (FastAPI)**
   - Technology: Python 3.11+, FastAPI, Uvicorn
   - Responsibilities: REST API endpoints, business logic, authentication/authorization, command orchestration, WebSocket server (embedded)
   - Components: See Component Diagram for internal structure
   - Port: 8000

4. **WebSocket Server (FastAPI embedded)**
   - Technology: FastAPI WebSocket support
   - Responsibilities: Real-time bidirectional communication for streaming command responses
   - Integrated: Part of Application Server, not separate container
   - Endpoint: `/ws/responses/{command_id}`

5. **Vehicle Connector**
   - Technology: Python with gRPC client
   - Responsibilities: gRPC communication with vehicles, command execution, response streaming, connection management
   - Communication: gRPC with vehicles (primary), MQTT (fallback - future)
   - Note: Initially part of Application Server, can be separated later for scaling

6. **PostgreSQL Database**
   - Technology: PostgreSQL 15+
   - Responsibilities: Persistent storage for users, vehicles, commands, responses, sessions, audit logs
   - Configuration: Connection pooling, read replicas (production)
   - Port: 5432

7. **Redis Cache**
   - Technology: Redis 7
   - Responsibilities: Session storage, caching (vehicle status), Pub/Sub for internal events (response streaming)
   - Channels: `response:{command_id}` for streaming responses to WebSocket clients
   - Port: 6379

**Communication Flows:**

- **User → Web App (SPA):** HTTPS, user interactions
- **Web App → API Gateway:** HTTPS, REST API calls, WebSocket upgrade
- **API Gateway → Application Server:** HTTP, reverse proxy
- **Application Server → PostgreSQL:** PostgreSQL protocol (asyncpg driver), SQL queries
- **Application Server → Redis:** Redis protocol, caching, Pub/Sub
- **Application Server (Vehicle Connector) → Vehicle:** gRPC (primary protocol), TLS-encrypted
- **Application Server → WebSocket Clients:** WebSocket protocol (ws:// or wss://), real-time streaming
- **Redis Pub/Sub → Application Server:** Internal event bus for response distribution

**Deployment Notes:**
- Development: All containers in Docker Compose
- Production: Kubernetes with Helm, EKS on AWS
- Scaling: Application Server horizontally scalable (3+ replicas), PostgreSQL uses read replicas, Redis cluster (optional)

---

### Context: component-diagram (from Architecture Blueprint - Section 3)

**C4 Level 3: Component Diagram - Application Server Internal Components**

The component diagram details the internal structure of the Application Server (FastAPI application) following a **Modular Monolith** architecture with clear separation of concerns.

**Components:**

**1. API Router Layer (FastAPI Routers)**

- **Auth Controller** (`app/api/v1/auth.py`)
  - Endpoints: POST /login, POST /refresh, POST /logout, GET /me
  - Depends on: Auth Service

- **Vehicle Controller** (`app/api/v1/vehicles.py`)
  - Endpoints: GET /vehicles, GET /vehicles/{id}, GET /vehicles/{id}/status
  - Depends on: Vehicle Service
  - Authorization: Requires authenticated user

- **Command Controller** (`app/api/v1/commands.py`)
  - Endpoints: POST /commands, GET /commands/{id}, GET /commands, GET /commands/{id}/responses
  - Depends on: Command Service
  - Authorization: Requires engineer or admin role

- **WebSocket Handler** (`app/api/v1/websocket.py`)
  - Endpoint: /ws/responses/{command_id}
  - Depends on: WebSocket Manager, Redis Pub/Sub
  - Authorization: JWT in query parameter

**2. Service Layer (Business Logic)**

- **Auth Service** (`app/services/auth_service.py`)
  - Responsibilities: JWT generation/validation, password hashing/verification, user authentication, session management
  - Depends on: User Repository, Session Repository
  - External: Redis (session storage)

- **Vehicle Service** (`app/services/vehicle_service.py`)
  - Responsibilities: Vehicle management, status queries, caching vehicle data
  - Depends on: Vehicle Repository, Redis (caching)

- **Command Service** (`app/services/command_service.py`)
  - Responsibilities: Command submission, validation, orchestration, status tracking, history queries
  - Depends on: Command Repository, Response Repository, SOVD Protocol Handler, Vehicle Connector, Audit Service

- **Audit Service** (`app/services/audit_service.py`)
  - Responsibilities: Audit logging for all critical operations (login, command submission, etc.)
  - Depends on: Audit Log Repository

- **WebSocket Manager** (`app/services/websocket_manager.py`)
  - Responsibilities: WebSocket connection lifecycle, broadcasting responses to subscribers, Redis Pub/Sub listener
  - Depends on: Redis Pub/Sub

**3. Integration/Connector Layer**

- **SOVD Protocol Handler** (`app/services/sovd_protocol_handler.py`)
  - Responsibilities: SOVD 2.0 command validation, encoding/decoding, schema validation
  - Validation: JSON Schema for command parameters
  - No database dependencies (pure logic)

- **Vehicle Connector** (`app/connectors/vehicle_connector.py`)
  - Responsibilities: gRPC client for vehicle communication, command execution, response streaming, connection management, retry logic, timeout handling
  - External: Vehicle gRPC servers
  - Depends on: Response Repository (to store responses)

**4. Repository Layer (Data Access)**

All repositories use async SQLAlchemy 2.0:

- **User Repository** (`app/repositories/user_repository.py`)
  - CRUD operations for users table

- **Vehicle Repository** (`app/repositories/vehicle_repository.py`)
  - CRUD operations for vehicles table, queries with filters

- **Command Repository** (`app/repositories/command_repository.py`)
  - CRUD operations for commands table, status updates, history queries with pagination

- **Response Repository** (`app/repositories/response_repository.py`)
  - CRUD operations for responses table, queries by command_id

- **Session Repository** (`app/repositories/session_repository.py`)
  - CRUD operations for sessions table (refresh tokens)

- **Audit Log Repository** (`app/repositories/audit_log_repository.py`)
  - Insert operations for audit_logs table

**5. Shared Kernel (Cross-Cutting Concerns)**

- **Database Module** (`app/database.py`)
  - Async engine, session factory, dependency injection (get_db)

- **Config Module** (`app/config.py`)
  - Pydantic Settings, environment variable loading

- **Dependencies Module** (`app/dependencies.py`)
  - FastAPI dependencies: get_current_user, require_role (RBAC)

- **Middleware**
  - `app/middleware/logging_middleware.py`: Request logging, correlation IDs
  - `app/middleware/error_handling_middleware.py`: Global exception handling (future)

- **Utils**
  - `app/utils/logging.py`: Structured logging configuration (structlog)
  - `app/utils/error_codes.py`: Error code definitions (future)

**Component Interaction Patterns:**

1. **Request Flow:** API Router → Service → Repository → Database
2. **Command Execution Flow:** Command Controller → Command Service → SOVD Protocol Handler (validation) → Vehicle Connector (gRPC) → Vehicle
3. **Response Streaming Flow:** Vehicle Connector → Redis Pub/Sub → WebSocket Manager → WebSocket clients
4. **Caching Flow:** Vehicle Service → Redis (cache vehicle status)
5. **Audit Flow:** Service layer → Audit Service → Audit Log Repository → Database

**Key Design Principles:**
- **Separation of Concerns:** Clear boundaries between API, business logic, data access
- **Dependency Injection:** FastAPI dependencies for session, authentication, authorization
- **Async/Await:** Fully async for I/O operations (database, Redis, gRPC)
- **Single Responsibility:** Each service/repository has one clear purpose
- **Testability:** Easy to mock dependencies for unit testing

---

### Context: architectural-style (from Architecture Blueprint - Section 2)

**Selected Architectural Style: Modular Monolith with Service-Oriented Modules**

**Overview:**
The SOVD Command WebApp adopts a **Modular Monolith** architecture, which provides clear internal module boundaries while maintaining a single deployable unit. This is a pragmatic choice for the initial implementation, balancing simplicity with maintainability and future evolution potential.

**Rationale:**

**Why Modular Monolith:**

1. **Simplicity for MVP:**
   - Single deployable artifact reduces operational complexity
   - Easier debugging (single process, single log stream)
   - Simplified deployment pipeline (one Docker image)
   - Lower infrastructure cost (no inter-service network overhead)

2. **Development Velocity:**
   - Faster iteration during early stages
   - No need for complex service orchestration or distributed tracing initially
   - Easier refactoring (internal module boundaries can change without breaking external contracts)
   - Shared codebase simplifies dependency management

3. **Performance:**
   - In-process communication (no network serialization for internal calls)
   - Lower latency for inter-module communication
   - Easier to optimize with profiling (single process)

4. **Team Size:**
   - Suitable for small to medium teams (2-5 developers initially)
   - Lower cognitive load (fewer deployment units to understand)

5. **Future Evolution Path:**
   - Modules designed with clear boundaries enable future extraction to microservices if needed
   - Decision deferred until scaling requirements are proven (premature optimization avoided)

**Module Structure (Service-Oriented):**

The monolith is divided into **cohesive modules** with well-defined responsibilities:

1. **Authentication Module:** User authentication, JWT management, session handling
2. **Vehicle Management Module:** Vehicle registry, status tracking, metadata management
3. **Command Execution Module:** Command submission, validation, orchestration, status tracking
4. **Response Streaming Module:** Real-time response delivery via WebSocket, event distribution
5. **Audit Module:** Logging of security-critical events, compliance
6. **SOVD Protocol Module:** Protocol-specific logic (validation, encoding/decoding)
7. **Vehicle Connector Module:** Integration with external vehicle systems (gRPC client)

**Inter-Module Communication:**
- Modules communicate via **well-defined service interfaces** (Python classes/functions)
- No direct database access across module boundaries (each module owns its repositories)
- Shared kernel provides cross-cutting concerns (database session, logging, config)

**Why Not Microservices (for MVP):**

1. **Premature Complexity:**
   - Distributed systems introduce network latency, partial failures, eventual consistency
   - Requires sophisticated DevOps (service mesh, distributed tracing, log aggregation)
   - Inter-service authentication/authorization adds overhead

2. **Unproven Scaling Needs:**
   - Initial requirements (100+ concurrent users) achievable with vertical scaling
   - Horizontal scaling of monolith sufficient for 1000s of concurrent users
   - Microservices justified when different components have vastly different scaling requirements (not yet proven)

3. **Team Maturity:**
   - Microservices require mature DevOps practices and tooling
   - Early-stage projects benefit from simplicity

**Evolution Strategy:**

If the system grows beyond monolith capabilities, modules can be extracted into microservices:

1. **Phase 1 (Current):** Modular Monolith
2. **Phase 2 (Future, if needed):** Extract high-load modules first (e.g., Vehicle Connector if it becomes bottleneck)
3. **Phase 3 (Future):** Full microservices if organizational scale demands it (10+ engineers, complex domain)

**Key Constraint:** Maintain **logical module boundaries** even within the monolith (no circular dependencies, clear interfaces) to preserve evolution optionality.

---

### Context: technology-stack (from Architecture Blueprint - Section 2)

**Technology Stack Summary**

This section presents the complete technology stack with justifications for each choice.

**Technology Selection Matrix:**

| Layer | Technology | Version | Purpose | Key Libraries/Tools |
|-------|-----------|---------|---------|---------------------|
| **Frontend** | React | 18.x | UI Framework | react-router-dom, @tanstack/react-query |
| | TypeScript | 5.x | Type Safety | - |
| | Material-UI (MUI) | 5.x | UI Components | @mui/material, @mui/icons-material |
| | Vite | 5.x | Build Tool | @vitejs/plugin-react |
| | Axios | 1.x | HTTP Client | - |
| **Backend** | Python | 3.11+ | Programming Language | - |
| | FastAPI | 0.104+ | Web Framework | uvicorn[standard], pydantic |
| | SQLAlchemy | 2.0+ | ORM | asyncpg (PostgreSQL driver) |
| | Alembic | 1.12+ | Database Migrations | - |
| **Authentication** | JWT | - | Token-based Auth | python-jose[cryptography] |
| | Passlib | 1.7+ | Password Hashing | passlib[bcrypt] |
| **Database** | PostgreSQL | 15+ | Relational Database | - |
| | Redis | 7.x | Cache & Pub/Sub | redis-py |
| **Communication** | gRPC | - | Vehicle Communication | grpcio, grpcio-tools |
| | WebSocket | - | Real-time Streaming | FastAPI WebSocket support |
| **Testing** | pytest | 7.4+ | Backend Testing | pytest-asyncio, httpx, pytest-cov |
| | Vitest | 1.0+ | Frontend Testing | @testing-library/react, @testing-library/jest-dom |
| | Playwright | 1.40+ | E2E Testing | @playwright/test |
| **Code Quality** | Ruff | 0.1+ | Python Linting | - |
| | Black | 23.11+ | Python Formatting | - |
| | mypy | 1.7+ | Python Type Checking | - |
| | ESLint | 8.54+ | JS/TS Linting | eslint-plugin-react |
| | Prettier | 3.1+ | JS/TS Formatting | - |
| **Logging & Monitoring** | structlog | 23.2+ | Structured Logging | - |
| | Prometheus | 2.x | Metrics Collection | prometheus-client, prometheus-fastapi-instrumentator |
| | Grafana | 10.x | Metrics Visualization | - |
| **DevOps** | Docker | 24.x | Containerization | - |
| | Docker Compose | 2.x | Local Orchestration | - |
| | Kubernetes | 1.28+ | Production Orchestration | - |
| | Helm | 3.x | K8s Package Manager | - |
| | GitHub Actions | - | CI/CD | - |
| **Cloud (Production)** | AWS EKS | - | Kubernetes Service | - |
| | AWS RDS | - | Managed PostgreSQL | Multi-AZ deployment |
| | AWS ElastiCache | - | Managed Redis | - |
| | AWS ALB | - | Load Balancer | - |
| | AWS Secrets Manager | - | Secrets Management | - |

**Key Technology Decisions & Justifications:**

**1. FastAPI vs. Node.js/Express (Backend Framework)**

**Decision:** FastAPI

**Rationale:**
- **Performance:** FastAPI is one of the fastest Python frameworks (comparable to Node.js), built on Starlette and Pydantic
- **Async Support:** Native async/await support critical for handling concurrent WebSocket connections and gRPC calls
- **Type Safety:** Pydantic models provide automatic validation and serialization with type hints
- **Auto-Generated Documentation:** OpenAPI (Swagger) documentation auto-generated from code (requirement)
- **Developer Productivity:** Python's simplicity and extensive ecosystem (especially for data processing, future ML integration)
- **Standards:** Built-in support for modern standards (OpenAPI 3.1, JSON Schema)

**Trade-off:** Slightly slower than Go/Rust for CPU-bound tasks, but I/O-bound nature of this application makes Python acceptable. Team familiarity with Python reduces onboarding time.

**2. PostgreSQL vs. NoSQL (Database)**

**Decision:** PostgreSQL

**Rationale:**
- **ACID Compliance:** Strong consistency required for command execution (no duplicate commands, reliable audit logs)
- **Relational Data Model:** Natural fit for entities with relationships (users, vehicles, commands, responses)
- **JSONB Support:** Flexible schema for command parameters and response payloads (hybrid relational + document model)
- **Mature Ecosystem:** Excellent ORM support (SQLAlchemy), connection pooling, monitoring tools
- **Query Capabilities:** Complex queries for command history filtering, audit log analysis, aggregations
- **Proven Scaling:** Vertical scaling to 100K+ transactions/sec, horizontal scaling with read replicas and sharding if needed

**Trade-off:** NoSQL (MongoDB, DynamoDB) might offer easier horizontal scaling, but PostgreSQL's strong consistency and query power outweigh this for an automotive diagnostics system where data integrity is critical.

**3. gRPC vs. REST (Vehicle Communication)**

**Decision:** gRPC (primary), REST (fallback for vehicles without gRPC support - future)

**Rationale:**
- **Performance:** Binary protocol (Protocol Buffers) reduces payload size, critical for large diagnostic data streams
- **Streaming:** Native bi-directional streaming support for real-time response updates (multiple DTC chunks)
- **Type Safety:** Strongly typed protobuf schemas ensure contract compliance between cloud and vehicle
- **Efficiency:** Lower latency and bandwidth usage than JSON/REST, important for vehicles on cellular networks
- **Automotive Industry Trend:** gRPC increasingly adopted in automotive (COVESA, SDV standards)

**Trade-off:** gRPC requires additional tooling (protobuf compiler) and is less human-readable than REST, but these costs are acceptable for the performance gains.

**4. WebSocket vs. Server-Sent Events (Real-Time Streaming to Frontend)**

**Decision:** WebSocket

**Rationale:**
- **Bi-Directional:** Allows future enhancements (e.g., client sending cancellation requests)
- **Low Latency:** Full-duplex communication with minimal overhead
- **Widespread Browser Support:** All modern browsers support WebSocket
- **FastAPI Support:** Built-in WebSocket support in FastAPI simplifies implementation

**Trade-off:** Server-Sent Events (SSE) would be simpler (HTTP-based, automatic reconnect), but WebSocket's flexibility and lower latency are preferred for real-time diagnostics.

**5. React vs. Angular/Vue (Frontend Framework)**

**Decision:** React

**Rationale:**
- **Ecosystem:** Largest ecosystem of UI libraries and tools (MUI, React Query, React Router)
- **Performance:** Virtual DOM and efficient re-rendering for real-time updates (command responses streaming)
- **Developer Experience:** Declarative syntax, component reusability, extensive community support
- **Hiring Pool:** Larger pool of React developers compared to Angular/Vue
- **Type Safety:** Excellent TypeScript support (better than Vue 2, comparable to Angular)

**Trade-off:** Vue 3 might be simpler for small teams, Angular offers more structure, but React's ecosystem and performance fit this project best.

**6. Material-UI (MUI) vs. Custom CSS/Tailwind**

**Decision:** Material-UI (MUI)

**Rationale:**
- **Component Library:** Pre-built components (tables, forms, modals) accelerate development
- **Consistency:** Google Material Design ensures professional, consistent UI
- **Accessibility:** Built-in ARIA support, keyboard navigation
- **Theming:** Powerful theming system for automotive branding
- **TypeScript Support:** Excellent type definitions

**Trade-off:** MUI adds bundle size (~300KB gzipped), but development speed gains justify this for MVP. Can optimize later with code splitting.

---

### Context: core-architecture (from Plan - Section 2)

**Core Architecture Overview**

This section summarizes the architectural style, technology stack, and key components as defined in the plan.

**Architectural Style:**
- **Modular Monolith** with service-oriented modules
- Clear module boundaries for future microservices extraction if needed
- Single deployable unit for MVP simplicity

**Technology Stack:**

**Frontend:**
- React 18 with TypeScript
- Material-UI (MUI) for components
- Vite for build tooling
- React Query for state management and caching
- Axios for HTTP client
- React Router for navigation

**Backend:**
- Python 3.11+ with FastAPI
- Uvicorn (ASGI server)
- SQLAlchemy 2.0 (ORM, async)
- Alembic (database migrations)
- JWT (python-jose) for authentication
- Passlib (bcrypt) for password hashing
- structlog for structured logging

**Database & Cache:**
- PostgreSQL 15+ (primary data store)
- Redis 7 (session storage, caching, Pub/Sub)

**Communication:**
- REST APIs (HTTP/JSON) for frontend-backend
- WebSocket for real-time response streaming
- gRPC for cloud-to-vehicle communication
- Redis Pub/Sub for internal event distribution

**Infrastructure:**
- Docker for containerization
- Docker Compose for local development
- Kubernetes with Helm for production
- GitHub Actions for CI/CD
- Prometheus + Grafana for monitoring

**Key Components (Application Server):**

The Application Server (FastAPI) contains these major components:

1. **API Router Layer:**
   - Auth Controller (login, refresh, logout, me)
   - Vehicle Controller (list, get, status)
   - Command Controller (submit, get, list, responses)
   - WebSocket Handler (real-time streaming)

2. **Service Layer:**
   - Auth Service (JWT, password hashing, user auth)
   - Vehicle Service (vehicle management, caching)
   - Command Service (command orchestration, validation, status)
   - Audit Service (audit logging)
   - WebSocket Manager (connection lifecycle, broadcasting)

3. **Integration Layer:**
   - SOVD Protocol Handler (validation, encoding/decoding)
   - Vehicle Connector (gRPC client, retry logic, timeouts)

4. **Repository Layer:**
   - User Repository
   - Vehicle Repository
   - Command Repository
   - Response Repository
   - Session Repository
   - Audit Log Repository

5. **Shared Kernel:**
   - Database module (async engine, session factory)
   - Config module (Pydantic Settings)
   - Dependencies module (get_current_user, RBAC)
   - Middleware (logging, error handling)
   - Utils (logging, error codes)

**Data Model:**

**Core Entities:**
- **users:** User accounts (username, email, password_hash, role)
- **vehicles:** Vehicle registry (vin, make, model, connection_status)
- **commands:** Command execution records (vehicle_id, command_name, params, status, user_id)
- **responses:** Command response chunks (command_id, payload JSONB, sequence_number, is_final)
- **sessions:** Refresh token storage (user_id, refresh_token, expires_at)
- **audit_logs:** Security audit trail (user_id, action, entity_type, ip_address, user_agent)

**Relationships:**
- users → commands (1:many) - users submit commands
- users → sessions (1:many) - users have sessions
- vehicles → commands (1:many) - vehicles receive commands
- commands → responses (1:many) - commands have responses

**API Contract Style:**
- RESTful API design with OpenAPI 3.1 specification
- JWT Bearer token authentication
- JSON payloads for request/response
- WebSocket for streaming (separate protocol)

**Communication Patterns:**
- **Synchronous Request/Response:** REST APIs for CRUD operations
- **Asynchronous Streaming:** WebSocket for real-time response updates
- **Event-Driven (Internal):** Redis Pub/Sub for distributing responses to WebSocket clients
- **RPC (External):** gRPC for cloud-to-vehicle command execution

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

**Current Project State:**
- Task I1.T1 has been completed: directory structure exists, Makefile functional, README.md present with project overview
- `.gitignore` properly configured with Python, Node.js, environment, and IDE exclusions
- Basic `pyproject.toml` configured with Black, Ruff, mypy, and pytest settings
- Skeleton project structure in place with all required directories

**Directory Structure Analysis:**

- **`docs/diagrams/`** - Target directory for your PlantUML files. Currently contains only a `rendered/` subdirectory. This is where you will create:
  - `component_diagram.puml`
  - `container_diagram.puml`

- **`backend/app/`** - Backend application structure is in place with proper module organization:
  - `api/v1/` - Will contain REST controllers (currently empty)
  - `services/` - Service layer for business logic (currently empty)
  - `repositories/` - Data access layer (currently empty)
  - `connectors/` - External integrations like Vehicle Connector (currently empty)
  - `models/`, `schemas/`, `middleware/`, `utils/` - All supporting directories ready

- **Configuration Files:**
  - `pyproject.toml` - Already configured with proper tool settings (Black line-length=100, Ruff with E/F/I/N/W/UP rules, mypy strict mode, pytest with coverage)
  - `Makefile` - Functional with targets: up, down, test, lint, logs
  - `docker-compose.yml` - Placeholder exists, will be populated in I1.T5

### Implementation Tips & Notes

**PlantUML Diagram Creation:**

1. **Component Diagram (C4 Level 3) Requirements:**
   - Must show internal structure of the Application Server
   - Include all components listed in the task description:
     - **API Router Layer:** Auth Controller, Vehicle Controller, Command Controller, WebSocket Handler
     - **Service Layer:** Auth Service, Vehicle Service, Command Service, Audit Service, WebSocket Manager
     - **Integration Layer:** SOVD Protocol Handler, Vehicle Connector
     - **Repository Layer:** User Repository, Vehicle Repository, Command Repository, Response Repository, Session Repository, Audit Log Repository
     - **Shared Kernel:** Database module, Config, Dependencies, Middleware, Utils
   - Show dependencies between components (arrows indicating calls/uses relationships)
   - Use C4-PlantUML notation for consistency (you can use standard PlantUML with proper component stereotypes if C4-PlantUML macros are not available)

2. **Container Diagram (C4 Level 2) Requirements:**
   - Must show all deployable containers:
     - Web App (React SPA)
     - API Gateway (Nginx)
     - Application Server (FastAPI)
     - WebSocket Server (note: embedded in Application Server, not separate container)
     - Vehicle Connector (note: initially part of Application Server)
     - PostgreSQL
     - Redis
   - Label all communication protocols:
     - HTTPS between components
     - WebSocket (ws:// or wss://)
     - PostgreSQL protocol
     - Redis protocol
     - gRPC (to vehicles)
   - Show boundaries and system context

3. **PlantUML Best Practices:**
   - Use `@startuml` and `@enduml` to wrap your diagrams
   - Add a title to each diagram using `title`
   - Use proper component syntax: `component`, `database`, `rectangle`, `cloud`
   - Use stereotypes to indicate technology (e.g., `<<React>>`, `<<FastAPI>>`, `<<PostgreSQL>>`)
   - Use different line styles for different protocols:
     - `-->` for synchronous calls
     - `..>` for asynchronous/event-driven
     - Label relationships with protocol names
   - Add notes using `note` for clarifications
   - Keep diagrams readable - don't over-complicate

4. **Testing Your Diagrams:**
   - You can validate PlantUML syntax using the online editor at http://www.plantuml.com/plantuml/
   - The acceptance criteria requires diagrams compile without errors
   - Ensure all component names match the terminology used in the architecture documentation

5. **File Locations:**
   - Create both files in `docs/diagrams/` directory
   - Use `.puml` extension (not `.txt` or `.uml`)
   - Follow naming convention: `component_diagram.puml` and `container_diagram.puml`

**Technology Considerations:**

- **C4 Model Reference:** The C4 model uses a hierarchical approach:
  - Level 1: System Context (not part of this task)
  - Level 2: Container (your task) - shows runtime containers and how they communicate
  - Level 3: Component (your task) - zooms into a container to show internal components
  - Level 4: Code (not typically done in C4)

- **PlantUML vs. C4-PlantUML:** While C4-PlantUML (https://github.com/plantuml-stdlib/C4-PlantUML) provides specific macros, standard PlantUML is acceptable. Use component diagrams with appropriate stereotypes and styling.

**Critical Reminders:**

- ⚠️ **WebSocket Server** is NOT a separate container - it's embedded in the FastAPI Application Server. Show this clearly in your container diagram.
- ⚠️ **Vehicle Connector** is initially part of the Application Server (for MVP). Can be shown as a component within the Application Server or as a separate container if you want to indicate future separation potential.
- ⚠️ The **Component Diagram** should focus ONLY on the internal structure of the Application Server, not the entire system.
- ⚠️ Include ALL repositories listed in the architecture (6 total: User, Vehicle, Command, Response, Session, Audit Log).
- ⚠️ Show dependencies correctly: Controllers depend on Services, Services depend on Repositories, everyone uses Shared Kernel.

**Validation Checklist:**

Before marking the task complete, verify:
- [ ] Both `.puml` files created in `docs/diagrams/`
- [ ] Component diagram shows all 4 layers (API Router, Service, Integration/Connector, Repository, Shared Kernel)
- [ ] Container diagram shows all 7 containers (even if some are embedded/integrated)
- [ ] Communication protocols labeled on all arrows
- [ ] Diagrams compile without PlantUML syntax errors
- [ ] Technology stereotypes added (<<FastAPI>>, <<PostgreSQL>>, etc.)
- [ ] Diagrams are readable and match the architecture descriptions above
- [ ] Files committed to git repository

**Next Steps After This Task:**

After completing this task, I1.T3 will create the Entity Relationship Diagram (ERD) for the database schema, which will complement these architectural diagrams by showing the data model structure.
