# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

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
