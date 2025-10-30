# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T7",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Create operational runbooks: deployment.md (procedures for local/staging/prod), troubleshooting.md (common issues), disaster_recovery.md (backup/restore), monitoring.md (metrics/alerts guide). Create engineer_guide.md user documentation. Update README with links.",
  "agent_type_hint": "DocumentationAgent",
  "inputs": "Architecture Blueprint Section 3.9; implemented features.",
  "target_files": [
    "docs/runbooks/deployment.md",
    "docs/runbooks/troubleshooting.md",
    "docs/runbooks/disaster_recovery.md",
    "docs/runbooks/monitoring.md",
    "docs/user-guides/engineer_guide.md",
    "README.md"
  ],
  "input_files": [],
  "deliverables": "Complete operational runbooks; user guide; updated README.",
  "acceptance_criteria": "deployment.md includes step-by-step for all environments; troubleshooting.md covers ≥5 issues; disaster_recovery.md includes backup script; monitoring.md explains metrics; engineer_guide.md shows UI workflow; README links all docs",
  "dependencies": [
    "I4.T1",
    "I4.T2",
    "I4.T3",
    "I4.T4",
    "I4.T5",
    "I4.T6"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Deployment Strategy (from 05_Operational_Architecture.md)

```markdown
**Development Environment:**
- **Tool**: Docker Compose
- **Services**: Frontend (React dev server, Vite HMR), Backend (FastAPI with hot reload), PostgreSQL, Redis
- **Deployment Command**:
  ```bash
  docker-compose up -d
  ```
- **Benefits**: Fast iteration, matches production architecture, easy onboarding

**Production Environment:**
- **Platform**: AWS EKS (Elastic Kubernetes Service)
- **Container Orchestration**: Kubernetes with Helm charts
- **Services**: Frontend (Nginx serving static build), Backend (Uvicorn), PostgreSQL (AWS RDS), Redis (AWS ElastiCache)

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

**Deployment Command:**
```bash
helm upgrade --install sovd-webapp ./sovd-helm-chart \
  -f values-production.yaml \
  -n production
```
```

### Context: CI/CD Pipeline (from 05_Operational_Architecture.md)

```markdown
**Workflow Stages:**

1. **Lint & Format Check**
   - Frontend: ESLint, Prettier
   - Backend: Ruff, Black, mypy

2. **Unit Tests**
   - Frontend: Vitest (coverage threshold 80%)
   - Backend: pytest (coverage threshold 80%)

3. **Build Docker Images**
   - Build frontend and backend images
   - Tag with commit SHA and `latest`

4. **Integration Tests**
   - Spin up services with docker-compose
   - Run API integration tests (pytest + httpx)
   - Run E2E tests (Playwright)

5. **Security Scans**
   - `npm audit` (frontend dependencies)
   - `pip-audit` (backend dependencies)
   - Trivy (Docker image vulnerabilities)

6. **Push Images**
   - Push to AWS ECR (Elastic Container Registry)

7. **Deploy to Staging**
   - Update Kubernetes deployment with new image
   - Run smoke tests

8. **Manual Approval Gate**
   - Require approval for production deploy

9. **Deploy to Production**
   - Blue-green deployment strategy
   - Gradual rollout (10%, 50%, 100%)
   - Automatic rollback if error rate spikes
```

### Context: Fault Tolerance Mechanisms (from 05_Operational_Architecture.md)

```markdown
**Health Checks:**
- **Liveness Probe**: `/health/live` (returns 200 if service is running)
- **Readiness Probe**: `/health/ready` (checks database, Redis connectivity)
- Kubernetes restarts unhealthy pods automatically

**Circuit Breaker Pattern:**
- Vehicle communication wrapped in circuit breaker (e.g., `tenacity` library)
- After 5 consecutive failures, circuit opens (fail fast)
- Periodic retry attempts to close circuit

**Retry Logic:**
- Vehicle communication retries (3 attempts with exponential backoff)
- Database operations retry on transient errors (connection loss)

**Graceful Degradation:**
- If Redis unavailable, fall back to database for sessions (slower but functional)
- If vehicle unreachable, return clear error (don't crash service)
- If database read replica fails, route to primary (higher load but available)

**Data Persistence:**
- Database backups: Daily automated snapshots (AWS RDS); 30-day retention
- Point-in-time recovery: Restore to any second within last 7 days
- Audit logs: Backed up to S3 (long-term retention)
```

### Context: High Availability (from 05_Operational_Architecture.md)

```markdown
**Deployment Strategy:**
- **Multi-AZ**: All services deployed across 3 Availability Zones
- **Load Balancing**: ALB distributes traffic; Kubernetes service load balances backend pods
- **Auto-Scaling**: Horizontal Pod Autoscaler scales pods based on CPU/memory
- **Database**: RDS Multi-AZ with automatic failover (<60 seconds)
- **Redis**: ElastiCache cluster mode for high availability

**Target Availability:**
- **SLA**: 99.9% uptime (8.76 hours downtime per year)
- **Recovery Time Objective (RTO)**: <15 minutes
- **Recovery Point Objective (RPO)**: <5 minutes (point-in-time recovery)

**Disaster Recovery:**
- **Automated Backups**: Daily database snapshots to S3
- **Cross-Region Replication**: Backup replication to secondary region (optional)
- **Documented Recovery Procedures**: Runbook for restoring from backup
```

### Context: Monitoring Strategy (from 05_Operational_Architecture.md)

```markdown
**Metrics Collection:**
- **Prometheus**: Time-series database for metrics
- **Exporters**: FastAPI metrics exporter (HTTP metrics, custom business metrics)
- **Grafana**: Visualization dashboards

**Logging Strategy:**
- **Structured Logging**: JSON logs with contextual fields (correlation_id, user_id, etc.)
- **Log Aggregation**: CloudWatch Logs (AWS) or ELK stack
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Retention**: 30 days for application logs; 90 days for audit logs

**Alerting:**
- **Critical Alerts**: Database down, service unhealthy, error rate >5%
- **Warning Alerts**: High latency (p95 >3s), low disk space, high CPU
- **Notification Channels**: Email, Slack, PagerDuty (production)
```

### Context: Horizontal Scaling Strategy (from 05_Operational_Architecture.md)

```markdown
**Stateless Services:**
- All backend services are stateless (session stored in Redis/database)
- Enables horizontal scaling without session affinity

**Container Orchestration (Kubernetes):**
- **Horizontal Pod Autoscaler (HPA)**: Scales pods based on CPU/memory or custom metrics (e.g., request rate)
  - Application Server: Scale from 3 to 10 pods
  - Vehicle Connector: Scale from 2 to 8 pods
  - WebSocket Server: Scale from 2 to 6 pods
- **Cluster Autoscaler**: Adds/removes nodes based on pod resource requests

**Load Balancing:**
- **External**: AWS ALB distributes traffic across API Gateway pods
- **Internal**: Kubernetes Service load balances between backend pods
- **WebSocket Affinity**: Sticky sessions not required (Redis Pub/Sub decouples connections)

**Database Scaling:**
- **Vertical Scaling**: Initial approach (RDS instance size increase)
- **Read Replicas**: For read-heavy queries (command history, vehicle list)
- **Connection Pooling**: SQLAlchemy pool (size=20, overflow=10) prevents connection exhaustion
- **Future**: Sharding by vehicle_id or partitioning audit_logs by time

**Redis Scaling:**
- **Redis Cluster**: Horizontal scaling for high availability and throughput
- Used for: session storage, vehicle status cache, Pub/Sub
```

### Context: Security Practices (from 05_Operational_Architecture.md)

```markdown
**Secrets Management:**
- Sensitive configuration (database passwords, JWT secrets, API keys) stored in environment variables
- Production: AWS Secrets Manager with automatic rotation
- Development: `.env` file (never committed to Git)

**Input Validation:**
- Pydantic models for all request/response validation
- SOVD command schema validation (JSON Schema)
- SQL injection prevention: SQLAlchemy parameterized queries

**Dependency Management:**
- Pin all dependencies (requirements.txt, package.json)
- Regular updates (monthly review cycle)
- Security scanning: `pip-audit`, `npm audit`

**Secure Development Lifecycle:**
- Code review required (CODEOWNERS)
- Static analysis: Bandit (Python security linter), ESLint security plugin
- Secrets scanning: git-secrets, TruffleHog
- Penetration testing: Annual third-party audit (production)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `README.md`
    *   **Summary:** This is the main project README with comprehensive quick-start instructions, technology stack details, development workflow, troubleshooting, monitoring setup (Prometheus/Grafana), and E2E testing documentation.
    *   **Recommendation:** You MUST update this file to add a new "Documentation" section that links to all the new runbooks and user guides you'll create. The file already has a partial documentation section at lines 678-684 that you should expand.

*   **File:** `docker-compose.yml`
    *   **Summary:** Complete Docker Compose configuration for local development with 6 services (db, redis, backend, frontend, prometheus, grafana). Includes detailed comments explaining each service's purpose, environment variables, health checks, and volume mounts.
    *   **Recommendation:** Reference this file extensively in your `deployment.md` runbook when documenting local development deployment. The file is very well-commented and serves as the source of truth for local environment setup.

*   **File:** `backend/app/config.py`
    *   **Summary:** Application configuration using pydantic-settings for environment variable management. Defines DATABASE_URL, REDIS_URL, JWT settings, and LOG_LEVEL.
    *   **Recommendation:** Use this file as a reference when documenting required environment variables in the deployment and troubleshooting runbooks. All sensitive configuration must come from environment variables.

*   **File:** `backend/app/services/health_service.py`
    *   **Summary:** Implements health check functions for database and Redis using `/health/live` (liveness) and `/health/ready` (readiness) patterns following Kubernetes best practices.
    *   **Recommendation:** Reference these health check endpoints in your troubleshooting runbook for diagnosing backend health issues. The functions `check_database_health()` and `check_redis_health()` return boolean and status tuples.

*   **File:** `backend/app/utils/metrics.py`
    *   **Summary:** Defines custom Prometheus metrics including `commands_executed_total`, `command_execution_duration_seconds`, `websocket_connections_active`, and `vehicle_connections_active`. Includes helper functions for incrementing/observing metrics.
    *   **Recommendation:** Document all these custom metrics in your `monitoring.md` runbook. Explain what each metric measures, how to query it in Prometheus, and what values indicate healthy vs unhealthy states.

*   **File:** `backend/app/middleware/error_handling_middleware.py`
    *   **Summary:** Global error handling middleware that formats all exceptions into standardized error responses with error codes, correlation IDs, and structured logging. Includes handlers for HTTP exceptions, validation errors, and unexpected exceptions.
    *   **Recommendation:** Reference the error response format (with `error.code`, `error.correlation_id`, etc.) in your troubleshooting guide. Explain how engineers can use the correlation_id from error responses to search logs for debugging.

*   **File:** `backend/app/middleware/rate_limiting_middleware.py`
    *   **Summary:** Rate limiting implementation using slowapi with Redis backend. Different limits for auth (5/min), commands (10/min), general API (100/min), and admin users (10000/min).
    *   **Recommendation:** Document rate limiting behavior in the troubleshooting runbook. If users see 429 errors, explain that rate limits exist and provide the current limits. Admins are effectively unlimited.

*   **File:** `Makefile`
    *   **Summary:** Contains all common development commands including `make up`, `make down`, `make test`, `make e2e`, `make lint`, and `make logs`. Well-documented with help text.
    *   **Recommendation:** Reference all these Makefile targets in your deployment.md and troubleshooting.md runbooks. Engineers should use these commands rather than raw docker-compose commands.

*   **File:** `scripts/init_db.sh`
    *   **Summary:** Database initialization script that creates tables, indexes, and inserts seed data (2 users: admin/admin123 and engineer/engineer123; 2 vehicles).
    *   **Recommendation:** Document this script in deployment.md as a required step after first startup. Include the seed credentials prominently so engineers know how to log in initially.

### Implementation Tips & Notes

*   **Tip:** The README already has excellent sections on Quick Start, Monitoring (Prometheus/Grafana with detailed queries), E2E Testing, and Troubleshooting. Your runbooks should COMPLEMENT not DUPLICATE this content. Reference the README where appropriate and add operational depth that goes beyond developer quick-start.

*   **Note:** The project already has comprehensive monitoring set up with 3 Grafana dashboards (Operations, Commands, Vehicles) that are auto-provisioned. Your `monitoring.md` runbook should explain how to interpret these dashboards, what metrics to watch, and when to escalate issues.

*   **Tip:** The architecture documents in `.codemachine/artifacts/architecture/` contain extensive details about deployment strategy, CI/CD pipeline, scaling, and disaster recovery. Mine these documents for authoritative information when writing your runbooks.

*   **Note:** The acceptance criteria requires "≥5 issues" in troubleshooting.md. Good candidates based on the codebase:
    1. Backend won't start (database not initialized)
    2. Frontend 401 errors (JWT token expired/invalid)
    3. WebSocket connections failing (Redis pub/sub issues)
    4. Rate limiting 429 errors
    5. Health check failures (database/Redis connectivity)
    6. Port conflicts preventing startup
    7. Volume permission issues

*   **Tip:** The disaster_recovery.md runbook should include a backup script. Based on the architecture, this should cover PostgreSQL backup (pg_dump), Redis backup (SAVE/BGSAVE), and audit log archival to S3. Provide concrete shell commands.

*   **Note:** The engineer_guide.md should be a step-by-step UI walkthrough showing: 1) Login with credentials, 2) Navigate to Vehicles page, 3) Select a vehicle, 4) Go to Commands page, 5) Submit a command (e.g., ReadDTC), 6) View real-time responses via WebSocket, 7) Check command history. Use the seed credentials (admin/admin123 or engineer/engineer123) in examples.

*   **Warning:** When updating README.md, preserve all existing content. Only add a new section or expand the existing "Documentation" section at line 678. Do NOT remove or modify the extensive monitoring, E2E testing, or troubleshooting content that already exists.

*   **Tip:** For deployment.md, structure it with clear sections for each environment:
    - **Local Development**: Reference docker-compose.yml, Makefile commands, init_db.sh
    - **Staging**: Kubernetes/Helm deployment (reference architecture docs)
    - **Production**: AWS EKS deployment, secrets management, multi-AZ setup
    Include prerequisites, step-by-step commands, verification steps, and rollback procedures for each.

*   **Note:** The monitoring.md guide should explain the Prometheus query language (PromQL) examples that are already in the README (lines 287-324) but add operational context: what values are normal, what indicates problems, how to correlate metrics with logs using correlation_id.

*   **Tip:** Reference the health check endpoints (`/health/live` and `/health/ready`) in troubleshooting as the first diagnostic step. The readiness endpoint specifically checks database and Redis connectivity, so if it returns 503, that's a dependency issue.

### Critical Success Factors

1. **Step-by-step clarity**: Each runbook must have numbered steps that an engineer can follow without guessing
2. **Concrete examples**: Use actual URLs (http://localhost:8000/docs), actual credentials (admin/admin123), actual commands (make up, docker-compose logs backend)
3. **Verification steps**: After each major step, tell the engineer how to verify it worked
4. **Error handling**: For each procedure, document what to do if it fails
5. **Cross-references**: Link between documents (deployment.md references troubleshooting.md, monitoring.md references health checks, etc.)
6. **README integration**: Add prominent links to all new documentation in the README's Documentation section
