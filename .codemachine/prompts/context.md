# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T1",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Create optimized production Dockerfiles for frontend and backend with multi-stage builds. Backend: build stage (install deps) + runtime stage (copy app, non-root user). Frontend: build stage (npm build) + runtime stage (Nginx Alpine, static files). Create Nginx config for frontend with gzip, security headers, API reverse proxy. Create .dockerignore files.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.9; Docker best practices.",
  "target_files": [
    "backend/Dockerfile.prod",
    "backend/.dockerignore",
    "frontend/Dockerfile.prod",
    "frontend/.dockerignore",
    "infrastructure/docker/nginx.conf"
  ],
  "input_files": [
    "backend/requirements.txt",
    "frontend/package.json"
  ],
  "deliverables": "Production Dockerfiles; Nginx config; .dockerignore files; tested images.",
  "acceptance_criteria": "Backend build succeeds, image <500MB, runs as non-root; Frontend build succeeds, image <50MB, serves at :80; Nginx has gzip+security headers+API proxy; .dockerignore excludes tests/node_modules; No build errors",
  "dependencies": [
    "I4.T1"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: production-deployment (from 05_Operational_Architecture.md)

**Production Environment (AWS EKS)**

**Orchestration:** Kubernetes (EKS)

**Infrastructure as Code:** Terraform (or AWS CloudFormation)

**Architecture:**
- **Compute**: EKS cluster (3 worker nodes, t3.large, across 3 AZs)
- **Database**: RDS for PostgreSQL (db.t3.medium, Multi-AZ)
- **Cache**: ElastiCache for Redis (cache.t3.small, cluster mode)
- **Load Balancer**: Application Load Balancer (ALB)
- **Networking**: VPC with public and private subnets
- **Storage**: EBS volumes for database; S3 for backups and logs
- **Secrets**: AWS Secrets Manager
- **DNS**: Route 53 for domain management
- **TLS Certificates**: AWS Certificate Manager (ACM)

**Kubernetes Resources:**
- **Namespaces**: `production`, `staging`
- **Deployments**:
  - `frontend-deployment` (3 replicas)
  - `backend-deployment` (3 replicas)
  - `vehicle-connector-deployment` (2 replicas)
- **Services**:
  - `frontend-service` (ClusterIP, ALB Ingress)
  - `backend-service` (ClusterIP)
  - `vehicle-connector-service` (ClusterIP)
- **Ingress**: ALB Ingress Controller for external access
- **ConfigMaps**: Non-sensitive configuration
- **Secrets**: Kubernetes Secrets (synced from AWS Secrets Manager via External Secrets Operator)

**Helm Chart Structure:**
```
sovd-helm-chart/
├── Chart.yaml
├── values.yaml (defaults)
├── values-production.yaml (overrides)
├── templates/
│   ├── frontend-deployment.yaml
│   ├── backend-deployment.yaml
│   ├── vehicle-connector-deployment.yaml
│   ├── services.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   └── secrets.yaml
```

### Context: deployment-constraints (from 01_Context_and_Drivers.md)

**Deployment Constraints:**
- Must support containerization (Docker)
- Must be deployable to cloud platforms (AWS, GCP, Azure)
- Local development environment using docker-compose
- Production deployment using Kubernetes (EKS/GKE/AKS)

### Context: nfr-performance (from 01_Context_and_Drivers.md)

**Performance Requirements:**
- API response time: <200ms for CRUD operations (p95)
- Command execution roundtrip: <500ms for simple commands
- WebSocket message latency: <100ms
- Database query performance: <50ms for indexed lookups
- Frontend: First Contentful Paint (FCP) <1.5s, Time to Interactive (TTI) <3s

### Context: nfr-security (from 01_Context_and_Drivers.md)

**Security Requirements:**
- All data encrypted in transit (TLS 1.2+)
- All data encrypted at rest (AES-256)
- JWT-based authentication with short-lived tokens (15min access, 7d refresh)
- Role-based access control (RBAC) for engineers and admins
- Comprehensive audit logging for all critical operations
- No secrets in codebase or container images
- Regular security scanning of dependencies and container images

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### CRITICAL FINDING: Task Already Completed!

**All target files already exist and appear to be production-ready:**

#### Existing Files Analysis:

1. **`backend/Dockerfile.prod`** - ALREADY EXISTS AND IS COMPLETE
   - **Summary:** Production-ready multi-stage Dockerfile for FastAPI backend
   - **Features:**
     - Multi-stage build (builder + runtime)
     - Builder stage: Python 3.11-slim with gcc, python3-dev, libpq-dev for compiling dependencies
     - Runtime stage: Python 3.11-slim with minimal runtime libraries (libpq5, curl)
     - Non-root user execution (UID 1001, user: appuser)
     - Dependencies installed to user site-packages and copied from builder
     - Uvicorn production config: 4 workers, uvloop, httptools
     - Health check using /health/ready endpoint
     - Image optimization: no build tools in runtime, no pip cache
   - **Recommendation:** This file meets all acceptance criteria. Verify image size <500MB by building it.

2. **`backend/.dockerignore`** - ALREADY EXISTS AND IS COMPREHENSIVE
   - **Summary:** Comprehensive exclusion list for backend build context
   - **Excludes:** Python cache (\_\_pycache\_\_, *.pyc), tests, coverage files, dev files (.env, .vscode, .idea), Git files, Docker files, docs, CI/CD configs, virtual envs, logs, temp files
   - **Recommendation:** This file meets acceptance criteria. All required exclusions are present.

3. **`frontend/Dockerfile.prod`** - ALREADY EXISTS AND IS COMPLETE
   - **Summary:** Production-ready multi-stage Dockerfile for React SPA with Nginx
   - **Features:**
     - Multi-stage build (builder + runtime)
     - Builder stage: Node 20 Alpine with build tools, npm ci for clean install, Vite build for optimized static assets
     - Runtime stage: nginx:alpine for minimal footprint
     - Copies only dist/ artifacts (no source, no node_modules)
     - Custom nginx.conf for gzip, security headers, SPA routing, API proxy
     - Health check on /health endpoint
     - Nginx runs in foreground (daemon off)
   - **IMPORTANT BUILD CONTEXT NOTE:** The Dockerfile expects to be built from project root with frontend/ subdirectory:
     - `COPY frontend/package*.json ./` and `COPY frontend/ ./`
     - Build command: `docker build -f frontend/Dockerfile.prod -t sovd-frontend:prod .` (from project root)
   - **Recommendation:** This file meets all acceptance criteria. Verify image size <50MB by building it.

4. **`frontend/.dockerignore`** - ALREADY EXISTS AND IS COMPREHENSIVE
   - **Summary:** Comprehensive exclusion list for frontend build context
   - **Excludes:** node_modules, dist/build output, test files, coverage, dev files (.env, .vscode, .idea), Git files, Docker files, docs, CI/CD configs, linter configs (eslintrc, prettierrc), tsconfig, bundle reports, logs, temp files
   - **Recommendation:** This file meets acceptance criteria. All required exclusions are present.

5. **`infrastructure/docker/nginx.conf`** - ALREADY EXISTS AND IS PRODUCTION-READY
   - **Summary:** Production Nginx configuration for serving React SPA and proxying API/WebSocket
   - **Features:**
     - Gzip compression (6 levels, multiple MIME types)
     - Security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy)
     - Cache control: 1y for /assets/, 6M for images/fonts, no-cache for HTML
     - SPA routing: try_files with fallback to index.html
     - API reverse proxy: /api/ → http://backend:8000
     - WebSocket proxy: /ws/ → http://backend:8000 with upgrade headers and 7d timeout
     - Health check endpoint: /health returns 200 "healthy"
     - Custom error pages
   - **Recommendation:** This config is complete and meets all acceptance criteria. It already includes all required features: gzip, security headers, API/WebSocket proxy.

### Implementation Guidance

**STOP! Before proceeding, you MUST verify the task status.**

The task is marked as `"done": false`, but ALL target files already exist and appear to meet the acceptance criteria. You have THREE options:

#### Option 1: Verify and Mark Complete (RECOMMENDED)
1. Build the Docker images to verify they meet acceptance criteria:
   ```bash
   # Backend (from project root)
   docker build -f backend/Dockerfile.prod -t sovd-backend:prod backend/

   # Frontend (from project root - note the context is root!)
   docker build -f frontend/Dockerfile.prod -t sovd-frontend:prod .
   ```

2. Check image sizes:
   ```bash
   docker images | grep sovd
   # Backend should be <500MB
   # Frontend should be <50MB
   ```

3. Test the images:
   ```bash
   # Backend: Check it runs as non-root
   docker run --rm sovd-backend:prod id
   # Should show: uid=1001(appuser) gid=1001(appuser)

   # Frontend: Check it serves on port 80
   docker run -d -p 8080:80 sovd-frontend:prod
   curl http://localhost:8080/health
   # Should return: healthy
   ```

4. If all tests pass, update the task status to `"done": true` in the tasks JSON file and report completion.

#### Option 2: Improve Existing Files (If Gaps Found)
If you find any deficiencies during verification:
1. Document the specific issues found
2. Make targeted improvements to address only those issues
3. Retest to confirm fixes
4. Update task status when complete

#### Option 3: Question the Task Status (If Uncertain)
If you're uncertain about the completion status:
1. Ask the user to clarify whether the task needs to be done or just verified
2. Provide your analysis of the existing files
3. Wait for user confirmation before proceeding

### Key Project Context

**Backend Dependencies (requirements.txt):**
- FastAPI, uvicorn[standard]
- SQLAlchemy 2.0, alembic, asyncpg (PostgreSQL)
- Redis, slowapi (rate limiting)
- python-jose[cryptography] (JWT), passlib[bcrypt]
- pydantic, pydantic-settings, jsonschema
- structlog (logging)
- prometheus-fastapi-instrumentator (metrics)

**Frontend Dependencies (package.json):**
- React 18, react-router-dom
- Material-UI (MUI)
- TanStack React Query, axios
- TypeScript, Vite
- Testing: vitest, testing-library/react

**Application Structure:**
- **Backend:** FastAPI app at `app.main:app` with middleware: CORS, logging, rate limiting, security headers, error handling
- **Frontend:** React SPA with Vite, client-side routing, API client with JWT auth
- **APIs:** /api/v1/auth, /api/v1/vehicles, /api/v1/commands, /ws/responses, /health/live, /health/ready, /metrics

### Docker Build Best Practices Applied

The existing Dockerfiles follow industry best practices:

1. **Multi-stage builds:** Separate builder and runtime stages minimize final image size
2. **Minimal base images:** `python:3.11-slim` and `nginx:alpine` for small footprint
3. **Layer caching optimization:** COPY requirements/package.json first, then source code
4. **No root execution:** Backend uses UID 1001 non-root user
5. **No secrets in images:** All secrets loaded from environment at runtime
6. **Health checks:** Both images include HEALTHCHECK directives
7. **Production tuning:** Uvicorn with 4 workers, uvloop, httptools for backend; Nginx with gzip for frontend
8. **Security hardening:** Minimal runtime dependencies, no dev tools, security headers in Nginx

### Potential Issues to Watch For

1. **Frontend Dockerfile build context:** Must be built from project root, not frontend/ directory
   - Correct: `docker build -f frontend/Dockerfile.prod -t sovd-frontend:prod .`
   - Wrong: `cd frontend && docker build -f Dockerfile.prod -t sovd-frontend:prod .`

2. **Backend image size:** With all dependencies, may approach 500MB limit. If it exceeds:
   - Consider using `python:3.11-slim` (already done)
   - Ensure \_\_pycache\_\_ and .pyc files excluded (already done in .dockerignore)
   - Verify no unnecessary packages in requirements.txt

3. **Nginx CSP header:** The existing nginx.conf has basic security headers but may need Content-Security-Policy (CSP) added if not already set by backend middleware
   - Check if backend's security_headers_middleware.py sets CSP for API responses
   - If not, consider adding to nginx.conf: `add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;`

### Testing Checklist

Before marking this task complete, verify:

- [ ] Backend image builds without errors
- [ ] Backend image size <500MB
- [ ] Backend runs as non-root user (uid=1001)
- [ ] Frontend image builds without errors
- [ ] Frontend image size <50MB
- [ ] Frontend serves on port 80
- [ ] Nginx has gzip compression enabled
- [ ] Nginx has security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection)
- [ ] Nginx proxies /api/ to backend
- [ ] Nginx proxies /ws/ with WebSocket upgrade headers
- [ ] .dockerignore files exclude tests, node_modules, \_\_pycache\_\_
- [ ] No build errors or warnings

### Recommendation

**This task appears to be ALREADY COMPLETE.** All deliverables exist and meet the specified acceptance criteria.

**Your next action should be:**
1. Run the verification tests listed above
2. If all tests pass, mark the task as done
3. Proceed to the next task (I5.T2: Create Helm Chart)

If any tests fail or gaps are found, address them specifically rather than recreating the entire solution.
