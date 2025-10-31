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
  "dependencies": ["I4.T1"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Production Deployment Environment (from 05_Operational_Architecture.md)

```markdown
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

### Context: Development vs Production Deployment Strategy (from deployment.md runbook)

```markdown
**Development Environment (Local)**

**Orchestration:** Docker Compose

**Components:**
- Frontend: Vite dev server with HMR
- Backend: FastAPI with uvicorn --reload
- Database: PostgreSQL container
- Redis: Redis container
- Monitoring: Prometheus + Grafana

**Key Features:**
- Volume mounts for hot-reload development
- No authentication/TLS (localhost only)
- Seed data auto-loaded
- Port mappings: 3000 (frontend), 8000 (backend), 5432 (db), 6379 (redis)

**Production Environment Notes:**
- Production uses optimized, multi-stage Docker builds
- Runs as non-root user for security
- No development dependencies included
- Minimal attack surface
- Read-only root filesystem where possible
```

### Context: Docker Best Practices & Security (from deployment.md runbook)

```markdown
**Production Docker Image Requirements:**

1. **Multi-stage builds**: Separate build and runtime stages to minimize final image size
2. **Non-root user**: All containers MUST run as non-root user (UID > 1000)
3. **Minimal base images**: Use Alpine or slim variants where possible
4. **No secrets in images**: Environment variables only, never hardcoded secrets
5. **Security scanning**: Images scanned with Trivy in CI/CD pipeline
6. **Size targets**:
   - Backend: <500MB (Python + dependencies)
   - Frontend: <50MB (Nginx + static files)
7. **Health checks**: Dockerfiles MUST include HEALTHCHECK instructions
8. **.dockerignore**: Exclude tests, node_modules, .git, __pycache__, coverage reports
```

### Context: Nginx Configuration Requirements (from deployment.md runbook)

```markdown
**Nginx Requirements for Production Frontend:**

1. **Gzip Compression**: Enable gzip for text/css/js/json files
2. **Security Headers**:
   - X-Frame-Options: SAMEORIGIN
   - X-Content-Type-Options: nosniff
   - X-XSS-Protection: 1; mode=block
   - Referrer-Policy: strict-origin-when-cross-origin
   - Content-Security-Policy: (strict CSP)
3. **API Reverse Proxy**: Proxy /api/ requests to backend service
   - Preserve headers: X-Real-IP, X-Forwarded-For, X-Forwarded-Proto
   - WebSocket upgrade support for /ws/ endpoints
4. **SPA Routing**: Serve index.html for all routes (try_files $uri /index.html)
5. **Cache Control**:
   - Static assets (hashed): Cache-Control: public, immutable, expires 1y
   - HTML files: no-cache, no-store, must-revalidate
6. **Health Check Endpoint**: /health returns 200 OK
```

### Context: Technology Stack (from 02_Architecture_Overview.md)

```markdown
**Backend:**
- Python 3.11
- FastAPI 0.104+
- uvicorn (ASGI server)
- SQLAlchemy 2.0 (async ORM)
- asyncpg (PostgreSQL driver)
- Redis 5.0+
- structlog (logging)
- Prometheus client

**Frontend:**
- Node 20 LTS
- React 18.2
- TypeScript 5.3
- Vite 5.0 (build tool)
- Material-UI 5.14
- Axios 1.6
- React Query 5.8

**Production Web Server:**
- Nginx Alpine (lightweight, production-grade)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### File: `backend/Dockerfile` (Development Version)
- **Summary**: This is the current DEVELOPMENT Dockerfile using Python 3.11-slim. It includes hot-reload with uvicorn --reload and volume mounts. It installs ALL dependencies (including dev tools like gcc) and runs as root user.
- **Recommendation**: You MUST create a NEW file `backend/Dockerfile.prod` that is COMPLETELY DIFFERENT. Do NOT copy the development Dockerfile structure. Production must use multi-stage build, no dev dependencies, non-root user, no volume mounts, and optimized for size.
- **Key Differences Required**:
  - Stage 1 (builder): Install dependencies, compile packages
  - Stage 2 (runtime): Copy only production requirements, create non-root user, copy compiled packages
  - Remove: gcc, python3-dev, libpq-dev from runtime stage
  - Remove: --reload flag from uvicorn command
  - Add: USER directive to run as non-root
  - Health check should use /health/ready endpoint

#### File: `frontend/Dockerfile` (Development Version)
- **Summary**: This is the current DEVELOPMENT Dockerfile using Node 20 Alpine. It runs the Vite dev server with HMR on port 3000. It includes build tools (python3, make, g++) needed for some npm packages.
- **Recommendation**: You MUST create a NEW file `frontend/Dockerfile.prod` with COMPLETELY DIFFERENT structure. Production must:
  - Stage 1: Build the static files using `npm run build` (outputs to ./dist)
  - Stage 2: Use nginx:alpine base image, copy ONLY ./dist files to /usr/share/nginx/html
  - No Node.js in final image (only Nginx)
  - Copy your new nginx.conf to /etc/nginx/conf.d/default.conf
  - Expose port 80 (not 3000)
  - Run as non-root user (nginx user)

#### File: `backend/requirements.txt`
- **Summary**: This file contains the production Python dependencies with pinned versions. It includes FastAPI, SQLAlchemy, asyncpg, redis, structlog, prometheus-fastapi-instrumentator, and security libraries (python-jose, passlib).
- **Recommendation**: In your multi-stage Dockerfile, the builder stage MUST install these requirements. The runtime stage should copy the installed packages from the builder. Note that asyncpg and passlib have C extensions that require compilation during build.
- **Important**: There is also a `backend/requirements-dev.txt` file (pytest, ruff, black, mypy) that MUST NOT be installed in production images.

#### File: `frontend/package.json`
- **Summary**: This file defines the build script as `vite build`. Running `npm run build` will generate optimized static files in the `./dist` directory.
- **Recommendation**: Your production Dockerfile must run `npm run build` in the builder stage. The build output is configured in vite.config.ts to output to ./dist with code splitting (vendor-react, vendor-mui, vendor-query, vendor-axios chunks).
- **Note**: The build process includes terser minification (drops console.log), gzip compression plugin, and bundle analysis. The dist folder will contain index.html and /assets/*.js/*.css files.

#### File: `frontend/vite.config.ts`
- **Summary**: Vite is configured to build with aggressive optimizations: code splitting into 4 vendor chunks, terser minification with console.log removal, gzip compression, and sourcemap disabled.
- **Recommendation**: The production build will output to `./dist` directory. In your Dockerfile's runtime stage (nginx), copy ./dist/* to /usr/share/nginx/html. The nginx.conf should serve index.html and handle SPA routing.
- **Build Output Structure**:
  - dist/index.html (main entry point)
  - dist/assets/[name]-[hash].js (chunked JS files)
  - dist/assets/[name]-[hash].css (styles)
  - dist/assets/*.gz (pre-compressed files from vite-plugin-compression)

#### File: `infrastructure/docker/nginx.conf`
- **Summary**: This is an EXISTING production-ready nginx configuration created in task I4.T9. It already includes gzip compression, security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy), SPA routing, cache control for static assets, and a /health endpoint.
- **Recommendation**: You can REUSE this existing nginx.conf file in your frontend production Dockerfile. However, you MUST UNCOMMENT and CONFIGURE the API reverse proxy section (lines 78-88) to proxy /api/ requests to the backend service and add WebSocket support for /ws/ endpoints.
- **Required Changes to nginx.conf**:
  - Uncomment the `location /api/` block
  - Update `proxy_pass` to `http://backend:8000` (assuming backend service named "backend" in Kubernetes)
  - Add WebSocket upgrade headers for streaming responses
  - Add a `location /ws/` block for WebSocket connections with upgrade headers

### Existing Infrastructure Components

#### Directory: `infrastructure/docker/`
- **Summary**: This directory already exists and contains nginx.conf. You should place any additional Docker-related configuration here.
- **Recommendation**: The nginx.conf file is already in the correct location. Reference it in your frontend Dockerfile.prod with: `COPY infrastructure/docker/nginx.conf /etc/nginx/conf.d/default.conf`

### Implementation Tips & Notes

#### Tip 1: Multi-stage Build Best Practices
- **Backend Multi-stage Pattern**:
  - Stage 1 (AS builder): Use python:3.11-slim, install build dependencies (gcc, python3-dev, libpq-dev), pip install requirements
  - Stage 2 (runtime): Use python:3.11-slim, create non-root user, copy /usr/local/lib/python3.11/site-packages from builder, copy application code, switch to non-root user
  - This pattern reduces final image size by 40-60% compared to single-stage builds

#### Tip 2: Non-root User Security
- **Backend**: Create a user named `appuser` with UID 1001, create /app directory owned by appuser, switch to appuser before CMD
- **Frontend**: Nginx Alpine image already has `nginx` user (UID 101). Use `USER nginx` directive and ensure /usr/share/nginx/html is readable by nginx user.

#### Tip 3: .dockerignore Files
- **Backend .dockerignore MUST exclude**:
  - `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`
  - `tests/`, `htmlcov/`, `coverage.json`, `.coverage`
  - `.git/`, `.gitignore`, `.env`, `.env.example`
  - `alembic/versions/*.pyc` (keep .py files for migrations)
  - `README.md`, `Makefile`, `docker-compose.yml`
  - `Dockerfile`, `Dockerfile.prod` (don't copy Dockerfiles into image)

- **Frontend .dockerignore MUST exclude**:
  - `node_modules/` (reinstall in image)
  - `dist/` (rebuilt in image)
  - `coverage/`, `stats.html`
  - `.git/`, `.gitignore`, `.env`, `.env.example`
  - `tests/`, `*.test.ts`, `*.test.tsx`
  - `README.md`, `Makefile`, `docker-compose.yml`
  - `Dockerfile`, `Dockerfile.prod`

#### Tip 4: Health Check Endpoints
- **Backend**: Use `/health/ready` (implemented in task I4.T4). This endpoint checks database and Redis connectivity. HEALTHCHECK should use: `curl -f http://localhost:8000/health/ready || exit 1`
- **Frontend**: Use the built-in `/health` endpoint in nginx.conf (already configured). HEALTHCHECK: `wget --no-verbose --tries=1 --spider http://localhost:80/health || exit 1`

#### Tip 5: Build Context and Image Naming
- **Backend build context**: `./backend/` (cd into backend dir before building)
- **Frontend build context**: `./frontend/` (cd into frontend dir before building)
- **Image tags for testing**: `sovd-backend:prod-test` and `sovd-frontend:prod-test`
- **Build commands**:
  ```bash
  cd backend && docker build -f Dockerfile.prod -t sovd-backend:prod-test .
  cd frontend && docker build -f Dockerfile.prod -t sovd-frontend:prod-test .
  ```

#### Tip 6: Uvicorn Production Configuration
- **Production uvicorn command**:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --loop uvloop --http httptools`
  - Remove `--reload` flag (only for development)
  - Add `--workers 4` for parallel processing
  - Use `--loop uvloop` for better async performance
  - Use `--http httptools` for faster HTTP parsing
  - Workers should be: (2 * CPU cores) + 1, defaulting to 4 for production

#### Tip 7: Environment Variable Handling
- **Backend**: Database URL, Redis URL, JWT secrets should come from environment variables (not hardcoded). The config.py module already handles this via pydantic-settings.
- **Frontend**: API base URL is baked into the build at build time (not runtime). Vite uses `import.meta.env.VITE_API_BASE_URL`. For production, this should be `/api` (relative path, proxied by nginx).

#### Warning 1: Nginx Proxy Configuration
- The current nginx.conf has the API proxy section COMMENTED OUT. You MUST uncomment and properly configure it. The backend service in Kubernetes will be accessible at `http://backend:8000` (service name + port).
- WebSocket connections for real-time responses (/ws/ endpoints) REQUIRE special headers:
  ```nginx
  location /ws/ {
      proxy_pass http://backend:8000;
      proxy_http_version 1.1;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
  }
  ```

#### Warning 2: CSP Header Not Yet Configured
- The nginx.conf includes basic security headers but does NOT include Content-Security-Policy (CSP). This is acceptable for I5.T1 scope, but note that CSP should be added in a future security hardening task.
- Current security headers are sufficient: X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy.

#### Note 1: Image Size Validation
- After building, verify image sizes with: `docker images | grep sovd`
- Backend should be <500MB (expect ~350-450MB with Python + packages)
- Frontend should be <50MB (expect ~25-35MB with Nginx Alpine + static files)
- If backend exceeds 500MB, review what's being copied from builder stage (may be copying unnecessary files)

#### Note 2: Testing Production Images Locally
- You can test production images locally before pushing to ECR:
  ```bash
  # Backend
  docker run -p 8000:8000 -e DATABASE_URL=... -e REDIS_URL=... -e JWT_SECRET=... sovd-backend:prod-test

  # Frontend (standalone, no API proxy needed for basic test)
  docker run -p 80:80 sovd-frontend:prod-test

  # Frontend with backend (use docker-compose with prod images)
  ```
- For local testing, create a temporary docker-compose.prod.yml that uses the production images with environment variables.

#### Note 3: Build Caching and CI/CD Integration
- Multi-stage builds enable Docker layer caching. In CI/CD (GitHub Actions), use `--cache-from` and `--cache-to` flags to speed up builds.
- The CI/CD pipeline (I5.T3) will build these images, tag with commit SHA, and push to AWS ECR.
- Ensure Dockerfiles are optimized for layer caching: copy requirements files BEFORE copying application code (so dependencies layer is cached).

---

## 4. Step-by-Step Implementation Guide

Based on the analysis above, here is the recommended implementation sequence:

### Step 1: Create `backend/Dockerfile.prod`
1. **Stage 1 (builder)**:
   - Base: `FROM python:3.11-slim AS builder`
   - Install build dependencies: gcc, python3-dev, libpq-dev
   - Set WORKDIR /app
   - Copy requirements.txt
   - RUN pip install --user --no-cache-dir -r requirements.txt
   - This installs packages to /root/.local

2. **Stage 2 (runtime)**:
   - Base: `FROM python:3.11-slim`
   - Install runtime dependencies: libpq5, curl (for healthcheck)
   - Create non-root user: `RUN useradd -m -u 1001 appuser`
   - Set WORKDIR /app
   - Copy installed packages from builder: `COPY --from=builder /root/.local /home/appuser/.local`
   - Update PATH to include user packages
   - Copy application code: `COPY --chown=appuser:appuser . /app`
   - Switch user: `USER appuser`
   - EXPOSE 8000
   - HEALTHCHECK using curl on /health/ready
   - CMD: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`

### Step 2: Create `backend/.dockerignore`
- List all exclusions from Tip 3 above
- Verify no sensitive files are accidentally included

### Step 3: Create `frontend/Dockerfile.prod`
1. **Stage 1 (builder)**:
   - Base: `FROM node:20-alpine AS builder`
   - Install build tools: python3, make, g++ (needed for some npm packages)
   - Set WORKDIR /app
   - Copy package*.json
   - RUN npm ci --legacy-peer-deps (clean install)
   - Copy source code: `COPY . .`
   - RUN npm run build (outputs to ./dist)

2. **Stage 2 (runtime)**:
   - Base: `FROM nginx:alpine`
   - Copy dist files: `COPY --from=builder /app/dist /usr/share/nginx/html`
   - Copy nginx config: `COPY ../infrastructure/docker/nginx.conf /etc/nginx/conf.d/default.conf`
   - USER nginx
   - EXPOSE 80
   - HEALTHCHECK using wget on /health
   - CMD: `["nginx", "-g", "daemon off;"]`

### Step 4: Create `frontend/.dockerignore`
- List all exclusions from Tip 3 above
- Critical: exclude node_modules and dist directories

### Step 5: Update `infrastructure/docker/nginx.conf`
- Uncomment the API proxy location block (lines 78-88)
- Update proxy_pass to http://backend:8000
- Add WebSocket location block for /ws/ paths with upgrade headers
- Ensure all security headers are present
- Verify gzip settings are enabled
- Keep existing SPA routing and cache control settings

### Step 6: Build and Test Images Locally
1. Build backend: `cd backend && docker build -f Dockerfile.prod -t sovd-backend:prod-test .`
2. Verify backend image size: `docker images sovd-backend:prod-test` (should be <500MB)
3. Build frontend: `cd frontend && docker build -f Dockerfile.prod -t sovd-frontend:prod-test .`
4. Verify frontend image size: `docker images sovd-frontend:prod-test` (should be <50MB)
5. Test backend runs: `docker run --rm -p 8000:8000 -e DATABASE_URL=... sovd-backend:prod-test` (should start without errors)
6. Test frontend serves: `docker run --rm -p 80:80 sovd-frontend:prod-test` (nginx should start, health check passes)
7. Verify health checks work
8. Inspect running containers to confirm non-root user: `docker exec <container-id> whoami` (should return appuser for backend, nginx for frontend)

### Step 7: Verify Acceptance Criteria
- ✅ Backend build succeeds without errors
- ✅ Backend image <500MB
- ✅ Backend runs as non-root user (appuser, UID 1001)
- ✅ Frontend build succeeds without errors
- ✅ Frontend image <50MB
- ✅ Frontend serves on port 80
- ✅ Nginx has gzip compression enabled
- ✅ Nginx has security headers (X-Frame-Options, X-Content-Type-Options, X-XSS-Protection, Referrer-Policy)
- ✅ Nginx has API reverse proxy configured (/api/ → backend:8000)
- ✅ Nginx has WebSocket support (/ws/ with upgrade headers)
- ✅ .dockerignore excludes tests, node_modules, __pycache__, coverage files
- ✅ No build errors or warnings

---

**End of Task Briefing Package**

This briefing provides everything needed to implement production-optimized Docker images for the SOVD Command WebApp. Follow the step-by-step guide and refer to the codebase analysis for specific implementation details. Good luck!
