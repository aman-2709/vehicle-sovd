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

### Context: container-diagram (from 03_System_Structure_and_Data.md)

```markdown
### 3.4. Container Diagram (C4 Level 2)

#### Description

This diagram zooms into the SOVD Command WebApp system boundary and shows the major deployable containers (applications and data stores). Key containers include:

- **Web Application (SPA)**: React-based frontend served as static files
- **API Gateway**: Nginx reverse proxy for routing, TLS termination, and load balancing
- **Application Server**: FastAPI-based backend with modular services
- **WebSocket Server**: Handles real-time streaming responses (embedded in FastAPI)
- **Vehicle Connector Service**: Abstraction layer for vehicle communication protocols
- **PostgreSQL Database**: Primary data store for vehicles, commands, responses, and audit logs
- **Redis Cache**: Session storage and response caching for performance

#### Diagram (PlantUML)

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
```

### Context: component-diagram (from 03_System_Structure_and_Data.md)

```markdown
### 3.5. Component Diagram(s) (C4 Level 3)

#### Description

This diagram details the internal components of the **Application Server** container. It shows the modular architecture with clear separation of concerns:

- **API Controllers**: FastAPI routers handling HTTP endpoints
- **Auth Service**: Authentication, JWT generation/validation, RBAC
- **Vehicle Service**: Vehicle registry and status management
- **Command Service**: SOVD command validation and execution orchestration
- **Audit Service**: Comprehensive logging of all operations
- **Repository Layer**: Data access abstraction using repository pattern
- **SOVD Protocol Handler**: SOVD 2.0 specification compliance layer
- **Shared Kernel**: Cross-cutting utilities (logging, config, error handling)

#### Diagram (PlantUML - Application Server Components)

```plantuml
@startuml
!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml

LAYOUT_WITH_LEGEND()

title Component Diagram - Application Server

Container_Boundary(app_server, "Application Server (FastAPI)") {

  Component(api_router, "API Router", "FastAPI APIRouter", "Top-level request routing and middleware chain")

  Component(auth_controller, "Auth Controller", "FastAPI Router", "Handles /auth/* endpoints: login, logout, refresh token")
  Component(vehicle_controller, "Vehicle Controller", "FastAPI Router", "Handles /vehicles/* endpoints: list, get, status")
  Component(command_controller, "Command Controller", "FastAPI Router", "Handles /commands/* endpoints: execute, history, get response")

  Component(auth_service, "Auth Service", "Python Module", "JWT generation/validation, password hashing, RBAC enforcement")
  Component(vehicle_service, "Vehicle Service", "Python Module", "Vehicle registry, connection status, health checks")
  Component(command_service, "Command Service", "Python Module", "Command validation, execution orchestration, response aggregation")
  Component(audit_service, "Audit Service", "Python Module", "Structured logging, audit trail persistence")

  Component(sovd_handler, "SOVD Protocol Handler", "Python Module", "SOVD 2.0 specification validation, command encoding, response decoding")

  Component(vehicle_repo, "Vehicle Repository", "SQLAlchemy", "Data access for vehicles table")
  Component(command_repo, "Command Repository", "SQLAlchemy", "Data access for commands table")
  Component(response_repo, "Response Repository", "SQLAlchemy", "Data access for responses table")
  Component(user_repo, "User Repository", "SQLAlchemy", "Data access for users table")

  Component(shared_kernel, "Shared Kernel", "Python Modules", "Logging, configuration, error handling, dependency injection")
}

ContainerDb(postgres, "PostgreSQL", "Database")
ContainerDb(redis, "Redis", "Cache")
Container(vehicle_connector, "Vehicle Connector", "gRPC/WebSocket Client")
System_Ext(idp, "Identity Provider", "OAuth2")

Rel(api_router, auth_controller, "Routes /auth/* to")
Rel(api_router, vehicle_controller, "Routes /vehicles/* to")
Rel(api_router, command_controller, "Routes /commands/* to")

Rel(auth_controller, auth_service, "Uses")
Rel(vehicle_controller, vehicle_service, "Uses")
Rel(command_controller, command_service, "Uses")

Rel(auth_service, user_repo, "Uses")
Rel(auth_service, idp, "Validates tokens with", "HTTPS")
Rel(auth_service, audit_service, "Logs auth events to")

Rel(vehicle_service, vehicle_repo, "Uses")
Rel(vehicle_service, redis, "Caches vehicle status in", "Redis Protocol")
Rel(vehicle_service, audit_service, "Logs vehicle events to")

Rel(command_service, command_repo, "Uses")
Rel(command_service, response_repo, "Uses")
Rel(command_service, sovd_handler, "Validates commands with")
Rel(command_service, vehicle_connector, "Executes commands via")
Rel(command_service, audit_service, "Logs command events to")

Rel(vehicle_repo, postgres, "Reads/Writes", "SQL")
Rel(command_repo, postgres, "Reads/Writes", "SQL")
Rel(response_repo, postgres, "Reads/Writes", "SQL")
Rel(user_repo, postgres, "Reads/Writes", "SQL")

Rel(audit_service, postgres, "Writes audit logs to", "SQL")

Rel(auth_service, shared_kernel, "Uses utilities from")
Rel(vehicle_service, shared_kernel, "Uses utilities from")
Rel(command_service, shared_kernel, "Uses utilities from")

@enduml
```
```

### Context: technology-stack (from 01_Plan_Overview_and_Setup.md)

```markdown
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

### Context: architectural-style (from 02_Architecture_Overview.md)

```markdown
### 3.1. Architectural Style

**Selected Style:** **Modular Monolith with Service-Oriented Modules**

#### Rationale

The architecture adopts a **modular monolith** approach with clear service boundaries, positioning the system for future evolution toward microservices if needed, while maintaining simplicity for initial deployment.

**Why Modular Monolith:**

1. **Right-Sized Complexity**: The system has ~3-5 core functional areas (auth, vehicle management, command execution, response handling, audit). This doesn't justify the operational overhead of full microservices.

2. **Simplified Deployment**: Single deployment unit reduces operational complexity while maintaining Docker/Kubernetes compatibility for scaling.

3. **Performance**: In-process communication between modules eliminates network latency for non-critical paths, helping meet the <2s response time requirement.

4. **Development Velocity**: Simplified testing, debugging, and deployment accelerates initial development while the team is small.

5. **Clear Module Boundaries**: Modules are designed as if they were microservices (separate code domains, dependency injection, interface contracts), making future extraction straightforward.

**Service-Oriented Module Design:**

- **API Gateway Module**: Request routing, authentication, rate limiting
- **Auth Service Module**: User authentication, JWT management, RBAC
- **Vehicle Service Module**: Vehicle registry, connection status, health monitoring
- **Command Service Module**: SOVD command validation, execution orchestration, response handling
- **Vehicle Connector Module**: Abstraction layer for vehicle communication (WebSocket/gRPC)
- **Audit Service Module**: Comprehensive logging of all operations
- **Database Access Layer**: Centralized data access with repository pattern

**Modularity Enforcement:**
- Each module has a clear public interface (domain facade)
- Inter-module communication through dependency injection
- No direct database access across module boundaries
- Shared kernel for cross-cutting concerns (logging, config, utilities)
```

### Context: key-components (from 01_Plan_Overview_and_Setup.md)

```markdown
*   **Key Components/Services:**
    *   **Web Application (SPA)**: React-based frontend for authentication, vehicle selection, command execution, response viewing
    *   **API Gateway (Nginx)**: Routes requests, terminates TLS, serves static files, load balances
    *   **Application Server (FastAPI)**: Core business logic with modular services
        *   **Auth Service Module**: JWT generation/validation, password hashing, RBAC enforcement
        *   **Vehicle Service Module**: Vehicle registry, connection status, health monitoring
        *   **Command Service Module**: SOVD command validation, execution orchestration, response aggregation
        *   **Audit Service Module**: Structured logging, audit trail persistence
        *   **SOVD Protocol Handler**: SOVD 2.0 specification compliance, command encoding, response decoding
    *   **WebSocket Server (FastAPI)**: Real-time streaming of command responses (embedded in Application Server)
    *   **Vehicle Connector Service**: Abstraction layer for gRPC/WebSocket communication with vehicles
    *   **PostgreSQL Database**: Persistent storage for users, vehicles, commands, responses, sessions, audit logs
    *   **Redis Cache**: Session storage, vehicle status caching, Pub/Sub for response events
```

### Context: communication-patterns (from 01_Plan_Overview_and_Setup.md)

```markdown
*   **Communication Patterns:**
    *   **Synchronous Request/Response (REST)**: Auth endpoints (login/logout/refresh), vehicle listing, command submission, history retrieval
    *   **Asynchronous Streaming (WebSocket)**: Real-time command response delivery, live vehicle status updates, command execution status
    *   **Event-Driven Internal (Redis Pub/Sub)**: Decouples Vehicle Connector from WebSocket Server; response events published to channels, subscribed by WebSocket clients
    *   **gRPC (Vehicle Communication)**: Efficient binary protocol for backend ↔ vehicle communication; supports server-streaming for multi-part responses
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `docs/diagrams/component_diagram.puml`
    *   **Summary:** This file contains an existing component diagram but it does NOT use the C4 PlantUML library as specified in the Architecture Blueprint. It uses standard PlantUML syntax with custom styling.
    *   **Recommendation:** You MUST REPLACE this file completely with a new diagram that uses the official C4 PlantUML library (`!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Component.puml`). The Architecture Blueprint Section 3.5 provides the exact structure you should follow.
    *   **Critical:** The existing diagram has good content coverage showing all required components, but the syntax must be converted to use C4 macros like `Component()`, `Container_Boundary()`, `Rel()`, etc.

*   **File:** `docs/diagrams/container_diagram.puml`
    *   **Summary:** This file contains an existing container diagram but similarly does NOT use the C4 PlantUML library as required. It uses standard PlantUML component syntax.
    *   **Recommendation:** You MUST REPLACE this file completely with a new diagram using the official C4 PlantUML library (`!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml`). The Architecture Blueprint Section 3.4 provides the exact reference implementation.
    *   **Critical:** The existing diagram covers most required containers (Web App, API Gateway, Application Server, PostgreSQL, Redis, Connected Vehicle) but needs to be rewritten using C4 macros like `Container()`, `ContainerDb()`, `Person()`, `System_Ext()`, `Rel()`, etc.

*   **File:** `README.md` (root)
    *   **Summary:** The project README is complete and well-structured, providing project overview, goals, technology stack, and quick start instructions.
    *   **Note:** This file was created in task I1.T1 and meets all acceptance criteria. No changes needed for this task.

*   **File:** `Makefile` (root)
    *   **Summary:** The Makefile provides convenient targets for `up`, `down`, `test`, `lint`, and `logs` commands.
    *   **Note:** This file was created in task I1.T1. The project follows a "make-based" workflow for development commands.

### Implementation Tips & Notes

*   **Tip - C4 PlantUML Syntax:** The Architecture Blueprint provides EXACT PlantUML code examples in Sections 3.4 and 3.5 that use the official C4 library. You should use these as your PRIMARY reference and adapt them to ensure all components mentioned in the task description are included.

*   **Tip - Component Diagram Requirements:** The task description specifies these components MUST be included in the Component Diagram:
    - API Router
    - Auth Controller, Vehicle Controller, Command Controller
    - Auth Service, Vehicle Service, Command Service, Audit Service
    - SOVD Protocol Handler
    - Repository Layer (Vehicle/Command/Response/User repositories)
    - Shared Kernel

    The existing diagram has all of these PLUS additional components (WebSocket Handler, Session Repository, Audit Log Repository, WebSocket Manager). You should INCLUDE all components from both the task description and the Architecture Blueprint to be comprehensive.

*   **Tip - Container Diagram Requirements:** The task description specifies these containers MUST be included:
    - Web App (React SPA)
    - API Gateway (Nginx)
    - Application Server (FastAPI)
    - WebSocket Server (FastAPI embedded)
    - Vehicle Connector
    - PostgreSQL
    - Redis

    The Architecture Blueprint adds Identity Provider as an external system. Include ALL of these for completeness.

*   **Tip - Communication Protocols:** The task explicitly requires "communication protocols labeled" in the Container Diagram. Use the `Rel()` macro's third parameter to specify protocols like "HTTPS", "WSS", "gRPC over TLS", "Redis Pub/Sub", "SQL (asyncpg)", etc. The Architecture Blueprint examples show exactly how to do this.

*   **Warning - PlantUML Testing:** The acceptance criteria require testing diagrams "with `plantuml -testdot` or online renderer". PlantUML is NOT installed in the local environment. You MUST instruct the Coder Agent to use an online PlantUML renderer (like https://www.plantuml.com/plantuml/ or http://www.plantuml.com/plantuml/uml/) to validate the diagrams compile without errors. Alternatively, suggest installing PlantUML locally if needed.

*   **Warning - File Overwrites:** Both target files already exist with content. Your task is to REPLACE them, not append. Make sure to use the Write tool (not Edit) to completely overwrite the existing files with the new C4-compliant diagrams.

*   **Note - C4 Layout Directives:** The Architecture Blueprint examples use `LAYOUT_TOP_DOWN()` for Container Diagram and `LAYOUT_WITH_LEGEND()` for Component Diagram. These are C4 library helpers that improve diagram readability. You SHOULD use these same directives.

*   **Note - Directory Structure Convention:** The project follows the directory structure from Plan Section 3, which places PlantUML source files in `docs/diagrams/` with rendered outputs in `docs/diagrams/rendered/` subdirectory. You do NOT need to generate rendered images - only the `.puml` source files.

*   **Note - Git Workflow:** The acceptance criteria state "Files committed to `docs/diagrams/` directory". The Coder Agent should be instructed that files will be committed as part of the normal git workflow (this task doesn't require running git commands).

### Quality Checklist for Coder Agent

Before completing this task, ensure:

1. ✅ Both `.puml` files use the official C4 PlantUML library includes
2. ✅ Container Diagram uses `C4_Container.puml` and appropriate macros
3. ✅ Component Diagram uses `C4_Component.puml` and appropriate macros
4. ✅ All components/containers from task description are present
5. ✅ All components/containers from Architecture Blueprint are present
6. ✅ Communication protocols are labeled in relationships
7. ✅ Diagrams compile without errors (validated via online renderer)
8. ✅ File structure matches: API Router → Controllers → Services → Repositories → Database
9. ✅ External systems (Vehicle, Identity Provider) are properly marked as `System_Ext()`
10. ✅ Databases use `ContainerDb()` macro
11. ✅ Diagram titles match Architecture Blueprint style
12. ✅ Notes/legends provide additional context where helpful

---

**End of Briefing Package**
