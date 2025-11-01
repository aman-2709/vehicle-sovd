# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T10",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Perform end-to-end production deployment test in staging. Workflow: provision infra (if Terraform), create AWS secrets, install External Secrets Operator, deploy Helm chart (helm install with values-production.yaml), verify pods running+healthy, run smoke tests (Ingress or port-forward), submit command+verify E2E (WebSocket), check Prometheus+Grafana, test HPA (load, scale up), test rollback, verify migration, test secrets rotation. Document in deployment_test_report.md with screenshots. Address issues.",
  "agent_type_hint": "BackendAgent",
  "inputs": "All I5 tasks (complete deployment infra+CI/CD).",
  "target_files": ["docs/runbooks/deployment_test_report.md"],
  "input_files": [],
  "deliverables": "Successful production-like deployment; smoke test results; deployment test report; verified E2E functionality.",
  "acceptance_criteria": "Helm deploys successfully; All pods Running+ready; /health/ready returns 200; Frontend accessible, login works; Full flow: login → vehicle → command → real-time responses; WebSocket connected, responses stream; Prometheus targets healthy; Grafana shows data; HPA scales 3→5 on CPU>70%; Migration Job completed before pods; Secrets synced from AWS; Rollback succeeds (helm rollback 0); Smoke tests pass; deployment_test_report.md: steps, results, screenshots, issues, resolutions; No critical blockers",
  "dependencies": [
    "I5.T1",
    "I5.T2",
    "I5.T3",
    "I5.T4",
    "I5.T5",
    "I5.T6",
    "I5.T7",
    "I5.T8",
    "I5.T9"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: deployment-view (from 05_Operational_Architecture.md)

**Key Insight**: This task requires executing the production deployment strategy defined in the architecture.

The deployment architecture includes:
- **Target Environment**: AWS EKS for production/staging
- **Development Environment**: Docker Compose for local testing
- **Production Deployment**: Kubernetes with Helm charts, multi-AZ setup, External Secrets Operator for secrets management

### Context: production-deployment (from 05_Operational_Architecture.md)

**Production Environment Details**:
- **Container Orchestration**: AWS EKS (Kubernetes) with Helm chart deployments
- **Infrastructure Components**:
  - VPC with 3 Availability Zones (us-east-1a, us-east-1b, us-east-1c)
  - Public subnets for ALB
  - Private subnets for EKS worker nodes
  - RDS PostgreSQL Multi-AZ for database
  - ElastiCache Redis for session storage and pub/sub
  - Application Load Balancer (ALB) with TLS termination
- **Deployment Strategy**: Rolling update with zero downtime (maxSurge: 1, maxUnavailable: 0)
- **Health Checks**: Liveness (`/health/live`) and Readiness (`/health/ready`) probes
- **Horizontal Pod Autoscaling**: 3-20 replicas based on CPU (70% target)
- **Secrets Management**: AWS Secrets Manager with External Secrets Operator

### Context: cicd-pipeline (from 05_Operational_Architecture.md)

**CI/CD Pipeline Flow** (GitHub Actions):
1. **Lint Stage**: ESLint (frontend), Ruff/Black/mypy (backend)
2. **Unit Tests**: Jest/Vitest (frontend), pytest (backend) - 80% coverage requirement
3. **Integration Tests**: Full docker-compose stack testing
4. **E2E Tests**: Playwright tests covering critical user flows
5. **Security Scans**: npm audit, pip-audit, Bandit, Trivy container scanning
6. **Build Images**: Multi-stage Dockerfiles for production
7. **Push to ECR**: Tag with commit SHA and latest
8. **Deploy Staging**: Auto-deploy on `develop` branch
9. **Deploy Production**: Manual approval on `main` branch, smoke tests, rollback capability

### Context: deployment-scaling (from 05_Operational_Architecture.md)

**Scaling Strategy**:
- **Small Scale** (10-50 users): 3 backend pods, 2 frontend pods, single-AZ RDS
- **Medium Scale** (50-200 users): 5-10 backend pods, 3 frontend pods, Multi-AZ RDS, Redis cluster
- **Large Scale** (200+ users): 10-20 backend pods, 5-8 frontend pods, read replicas for RDS, Redis cluster with replication

### Context: health-checks (from 05_Operational_Architecture.md)

**Health Check Endpoints**:
- `GET /health/live`: Simple liveness check (returns 200 if server running)
- `GET /health/ready`: Readiness check verifying database and Redis connectivity
  - Expected response: `{"status": "healthy", "database": "connected", "redis": "connected"}`
  - Returns 503 if dependencies unhealthy

### Context: task-i5-t2 (from tasks_I5.json)

**Helm Chart Structure** created in I5.T2:
- Chart: `infrastructure/helm/sovd-webapp/`
- Templates: backend-deployment, frontend-deployment, vehicle-connector-deployment, services, ingress, configmap, secrets, hpa, migration-job
- Values: `values.yaml` (defaults), `values-production.yaml` (production overrides)
- Configuration: 3 replicas (production: 5), resource requests/limits, health checks, HPA (CPU 70%, 3-10 replicas)

### Context: task-i5-t3 (from tasks_I5.json)

**CI/CD Pipeline** created in I5.T3:
- Pipeline: `.github/workflows/ci-cd.yml`
- Smoke Tests: `scripts/smoke_tests.sh`
- Stages: Lint → Unit Tests → Integration Tests → E2E → Security Scans → Build → Push → Deploy
- Deployment: Staging auto-deploys on `develop`, Production requires manual approval on `main`

### Context: task-i5-t8 (from tasks_I5.json)

**Database Migration Strategy** created in I5.T8:
- Migration Job: `infrastructure/helm/sovd-webapp/templates/migration-job.yaml`
- Helm Hook: `pre-upgrade` hook ensures migrations run before deployment
- Command: `alembic upgrade head`
- Failure Handling: `backoffLimit: 3`, `restartPolicy: OnFailure`

### Context: task-i5-t9 (from tasks_I5.json)

**Secrets Management** created in I5.T9:
- AWS Secrets Manager secrets: `sovd/production/database`, `sovd/production/jwt`, `sovd/production/redis`
- External Secrets Operator: Syncs AWS secrets to Kubernetes secrets (refresh interval: 1 hour)
- IRSA: IAM role for service account with `secretsmanager:GetSecretValue` permission
- Script: `scripts/create_aws_secrets.sh` automates secret creation

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

#### **File**: `infrastructure/helm/sovd-webapp/values-production.yaml`
- **Summary**: Production-specific Helm values with 5 backend replicas, 3 frontend replicas, AWS ECR image repositories, ALB ingress configuration, HPA settings (70% CPU, 5-20 replicas), and External Secrets Operator integration.
- **Recommendation**: You MUST use this file when deploying to production/staging environment. Note that image tags are set to `v1.0.0` - you may need to update these to match actual built images or use local Docker images.
- **Key Configuration**:
  - Backend replicas: 5 (production), resources: 512Mi/500m requests, 1Gi/1000m limits
  - Frontend replicas: 3, resources: 128Mi/200m requests, 256Mi/400m limits
  - HPA: Scales 5-20 backend pods, 3-8 frontend pods at 70% CPU
  - Ingress: ALB with TLS certificate, HTTPS redirect, health checks
  - External Secrets: Enabled, pointing to AWS Secrets Manager
- **IMPORTANT**: Contains **placeholder values** that may need adjustment for local testing:
  - ECR repository: `123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-backend` (placeholder account ID)
  - RDS endpoint: `sovd-production.c9akciq32.us-east-1.rds.amazonaws.com` (placeholder)
  - Redis endpoint: `sovd-production.abc123.ng.0001.use1.cache.amazonaws.com` (placeholder)
  - ACM certificate ARN (for HTTPS)

#### **File**: `scripts/smoke_tests.sh`
- **Summary**: Comprehensive smoke test script that validates critical endpoints: health checks, API documentation, Prometheus metrics, frontend assets, CORS headers.
- **Recommendation**: You MUST run this script as part of post-deployment verification. It accepts `API_BASE_URL` and `FRONTEND_BASE_URL` environment variables.
- **Test Coverage**:
  1. Backend health (liveness): `/health/live` → 200
  2. Backend readiness: `/health/ready` → 200 with `{"status": "healthy", ...}`
  3. API documentation: `/docs` → 200
  4. OpenAPI spec: `/openapi.json` → 200
  5. Prometheus metrics: `/metrics` → 200
  6. Frontend application: `/` → 200
  7. Frontend assets: Check for Vite/React markers
  8. CORS headers: OPTIONS preflight → 200/204
- **Exit Code**: Returns 0 if all tests pass, 1 if any fail
- **Usage**:
  ```bash
  export API_BASE_URL=http://localhost:8000
  export FRONTEND_BASE_URL=http://localhost:3000
  ./scripts/smoke_tests.sh
  ```

#### **File**: `infrastructure/helm/sovd-webapp/Chart.yaml`
- **Summary**: Helm chart metadata for sovd-webapp version 1.0.0.
- **Recommendation**: Ensure this version matches your deployment expectations. The chart is application-type (not library).

#### **File**: `docs/runbooks/deployment.md`
- **Summary**: Comprehensive deployment runbook covering local development, staging, and production deployment procedures with step-by-step instructions, verification steps, and rollback procedures.
- **Recommendation**: You SHOULD follow this runbook closely for the deployment test. Key sections:
  - **Staging Deployment** (lines 167-283): Your primary reference
  - **Production Deployment** (lines 286-382): Additional production-specific considerations
  - **Rollback Procedures** (lines 385-451): How to rollback using Helm or kubectl
  - **Post-Deployment Verification** (lines 453-522): Checklist for verifying deployment success
- **Critical Steps from Runbook**:
  1. Authenticate to AWS ECR (or use local registry)
  2. Build and push Docker images with commit SHA tag
  3. Configure secrets in AWS Secrets Manager (or use local K8s secrets)
  4. Deploy with Helm using `values-production.yaml`
  5. Verify pods running (all `Running` with `1/1` ready)
  6. Test health endpoints
  7. Run smoke tests
  8. Monitor for 30 minutes (production only)

#### **File**: `infrastructure/helm/sovd-webapp/templates/migration-job.yaml`
- **Summary**: Kubernetes Job that runs Alembic migrations with Helm pre-upgrade hook. Configured with backoffLimit: 3, activeDeadlineSeconds: 600 (10 minutes), restartPolicy: OnFailure.
- **Recommendation**: This Job will run automatically before deployment. Verify it completes successfully by checking `kubectl get jobs -n <namespace>` and `kubectl logs -n <namespace> <migration-job-pod>`.
- **Expected Output**: "✓ Database migration completed successfully" and current migration revision displayed.
- **Key Details**:
  - Helm hook: `pre-upgrade, pre-install` with weight `-5` (runs first)
  - Uses backend image to run `alembic upgrade head`
  - Sources DATABASE_URL from Kubernetes Secret
  - Fails entire deployment if migration fails

#### **File**: `docs/runbooks/secrets_management.md`
- **Summary**: Detailed guide for AWS Secrets Manager integration with External Secrets Operator, including setup, secret creation, verification, rotation, and troubleshooting.
- **Recommendation**: You MUST ensure External Secrets Operator is installed and secrets are synced before deployment (if testing with AWS). Key verification commands:
  - `kubectl get secretstore -n <namespace>` → Should show `aws-secrets-manager` as Ready
  - `kubectl get externalsecret -n <namespace>` → Should show synced status
  - `kubectl get secret <app>-secrets -n <namespace>` → Should exist with correct keys
- **Troubleshooting**: If secrets not syncing, check:
  1. IAM role permissions (secretsmanager:GetSecretValue)
  2. IRSA annotation on ServiceAccount
  3. Secrets exist in AWS with correct names
  4. External Secrets Operator pods running
- **Alternative for Local Testing**: Set `externalSecrets.enabled: false` in values and manually create Kubernetes secrets with hardcoded values.

#### **File**: `.github/workflows/ci-cd.yml`
- **Summary**: CI/CD pipeline with frontend/backend linting, testing, coverage checks, and Lighthouse performance testing. The full pipeline includes security scans, image building, and deployment stages (visible in later lines not shown).
- **Recommendation**: While this task is a manual deployment test (not CI/CD triggered), you SHOULD reference the pipeline's smoke test and verification steps to ensure your manual testing is comprehensive.

### Implementation Tips & Notes

#### **Tip #1: Choose Your Test Environment**
Since this is a production deployment **test** in staging, you have two options:

**Option A: Local Kubernetes** (minikube, kind, Docker Desktop K8s)
- **Pros**: No AWS costs, faster iteration, easier to set up
- **Cons**: Cannot test AWS-specific features (ALB, RDS Multi-AZ, ElastiCache, AWS Secrets Manager, IRSA)
- **Best for**: Validating Helm chart rendering, pod startup, basic functionality
- **Requires**: Local PostgreSQL and Redis (can use docker-compose or K8s deployments)

**Option B: AWS EKS Staging Cluster** (if available from I5.T7)
- **Pros**: Full production-like test, validates all AWS integrations
- **Cons**: Requires AWS infrastructure, costs money, more complex setup
- **Best for**: Complete production readiness validation
- **Requires**: Terraform-provisioned infrastructure, AWS credentials, ECR registry

**Recommendation**:
- If AWS staging exists: Use it for comprehensive testing
- If no AWS staging: Use local K8s and document limitations in report
- **CRITICAL**: Clearly document which environment you used in the deployment report

#### **Tip #2: Adapting values-production.yaml for Local Testing**

If testing locally without AWS, create a `values-local.yaml` override:

```yaml
# values-local.yaml - for local K8s testing
global:
  namespace: staging
  domain: localhost

backend:
  replicaCount: 3  # Reduced for local
  image:
    repository: sovd-backend
    tag: "local"
    pullPolicy: Never  # Use local Docker images

frontend:
  replicaCount: 2  # Reduced for local
  image:
    repository: sovd-frontend
    tag: "local"
    pullPolicy: Never

# Disable External Secrets for local testing
externalSecrets:
  enabled: false

# Use local database/redis
config:
  database:
    host: "postgresql.default.svc.cluster.local"  # Or external IP if docker-compose
    port: "5432"
    name: "sovd"
    user: "sovd_user"
  redis:
    host: "redis.default.svc.cluster.local"
    port: "6379"

# Ingress for local testing (no ALB)
ingress:
  enabled: false  # Use port-forward or NodePort instead
```

Then deploy with:
```bash
helm upgrade --install sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f values.yaml \
  -f values-local.yaml \
  -n staging \
  --create-namespace
```

#### **Tip #3: Building Images for Local Testing**

If using local Kubernetes:

```bash
# Build backend image
cd backend
docker build -f Dockerfile.prod -t sovd-backend:local .

# Build frontend image
cd ../frontend
docker build -f Dockerfile.prod -t sovd-frontend:local .

# For minikube: Load images into minikube
minikube image load sovd-backend:local
minikube image load sovd-frontend:local

# For kind: Load images into kind cluster
kind load docker-image sovd-backend:local --name your-cluster-name
kind load docker-image sovd-frontend:local --name your-cluster-name

# For Docker Desktop K8s: Images already available
```

#### **Tip #4: Setting Up Local Database & Redis**

Option A: Use existing docker-compose (easiest):
```bash
# Start only db and redis from docker-compose
docker-compose up -d db redis

# Get their IP addresses
DB_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' sovd-db-1)
REDIS_IP=$(docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' sovd-redis-1)

# Use these IPs in values-local.yaml config.database.host and config.redis.host
```

Option B: Deploy database/redis in Kubernetes:
```bash
# Deploy PostgreSQL
helm repo add bitnami https://charts.bitnami.com/bitnami
helm install postgresql bitnami/postgresql \
  --set auth.postgresPassword=sovd_pass \
  --set auth.database=sovd \
  --set primary.persistence.enabled=false  # For testing

# Deploy Redis
helm install redis bitnami/redis \
  --set auth.enabled=false \
  --set master.persistence.enabled=false
```

#### **Tip #5: HPA Load Testing**
To test HPA scaling from 3 to 5 pods (or 5 to 7 in production):

```bash
# Generate CPU load on backend using Apache Bench (ab) or similar
# Install ab if needed: sudo apt-get install apache2-utils

# Get backend service IP
BACKEND_IP=$(kubectl get svc sovd-webapp-backend -n staging -o jsonpath='{.spec.clusterIP}')

# Generate sustained load (100 concurrent requests for 5 minutes)
ab -n 30000 -c 100 -t 300 http://${BACKEND_IP}:8000/api/v1/vehicles

# Watch HPA in another terminal
kubectl get hpa -n staging --watch

# Expected: After ~2-3 minutes, backend pods scale up when CPU > 70%
```

Alternative: Simple load generator pod:
```bash
kubectl run -it --rm load-generator --image=busybox --restart=Never -n staging -- \
  /bin/sh -c "while true; do wget -q -O- http://sovd-webapp-backend:8000/api/v1/vehicles; done"

# Watch scaling
kubectl get hpa -n staging --watch
```

#### **Tip #6: WebSocket Testing**
For E2E WebSocket testing:

1. **Using Frontend UI** (recommended):
   - Login → Submit command → Watch real-time responses in Response Viewer
   - This tests the full integration end-to-end

2. **Using wscat** (for debugging):
   ```bash
   # Install wscat
   npm install -g wscat

   # First, get a JWT token by logging in
   TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin123"}' \
     | jq -r .access_token)

   # Connect to WebSocket
   wscat -c "ws://localhost:8000/ws/responses/COMMAND_ID?token=$TOKEN"
   ```

3. **Expected WebSocket Messages**:
   ```json
   {"event":"response","command_id":"...","response":{...},"sequence_number":1}
   {"event":"response","command_id":"...","response":{...},"sequence_number":2}
   {"event":"status","status":"completed"}
   ```

#### **Tip #7: Testing Rollback**

After successful deployment, test rollback capability:

```bash
# List Helm releases
helm history sovd-webapp -n staging

# Should show 2 releases after first deployment
# REVISION  STATUS      CHART           APP VERSION   DESCRIPTION
# 1         deployed    sovd-webapp-1.0 1.0.0         Install complete

# Make a change and upgrade (e.g., change replica count)
helm upgrade sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f values-production.yaml \
  --set backend.replicaCount=7 \
  -n staging

# Verify new revision
helm history sovd-webapp -n staging

# Rollback to previous release
helm rollback sovd-webapp -n staging

# Or rollback to specific revision
helm rollback sovd-webapp 1 -n staging

# Verify rollback
kubectl get pods -n staging
# Should see pods scaling back to original count

# Verify app still works
curl http://localhost:8000/health/ready
```

#### **Tip #8: Screenshots for Report**

The acceptance criteria requires **screenshots** in the deployment report. Capture screenshots of:

1. ✅ **Helm install output** showing successful deployment
2. ✅ **kubectl get pods** showing all pods Running and Ready (1/1)
3. ✅ **kubectl get jobs** showing migration job completed
4. ✅ **/health/ready** response showing healthy status
5. ✅ **Smoke test output** showing all 8 tests passing
6. ✅ **Frontend login screen** and successful login
7. ✅ **Vehicles page** showing vehicle list
8. ✅ **Command submission** and response form
9. ✅ **WebSocket responses** streaming in real-time
10. ✅ **Prometheus targets** page showing all targets UP
11. ✅ **Grafana operations dashboard** showing metrics
12. ✅ **HPA scaling event** (`kubectl get hpa --watch`)
13. ✅ **ExternalSecret status** (if testing with AWS) showing Synced
14. ✅ **Rollback output** showing successful rollback

**How to capture screenshots**:
- Use `screenshot` command or Snipping Tool (Windows) / Shift+Cmd+4 (Mac) / gnome-screenshot (Linux)
- Save in `docs/runbooks/screenshots/` directory
- Name clearly: `01-helm-install.png`, `02-pods-running.png`, etc.
- Embed in markdown: `![Description](screenshots/filename.png)`

#### **Tip #9: Document Issues and Resolutions**

The acceptance criteria requires documenting **issues and resolutions**. Even if everything works perfectly, document:

**Examples of what to document**:
- Configuration adjustments needed for local vs AWS
- Commands that failed initially and how you fixed them (e.g., wrong image tag)
- Performance observations (migration took 45 seconds, pod startup took 2 minutes)
- Unexpected behaviors (frontend took 3 attempts to connect to backend)
- Workarounds applied (disabled External Secrets for local testing)
- Dependencies discovered (needed to install PostgreSQL client for testing)

**Issue Report Template**:
```markdown
### Issue N: [Brief Title]

**Severity**: Critical | High | Medium | Low
**Description**: [What went wrong - be specific]
**Impact**: [What functionality was affected]
**Root Cause**: [Why it happened - after investigation]
**Resolution**: [How you fixed it - exact steps]
**Time to Resolve**: [How long it took]
**Prevention**: [How to avoid in future]
```

#### **Warning #1: Placeholder Values in values-production.yaml**

The `values-production.yaml` file contains **placeholder values** that will cause deployment failures if not addressed:

```yaml
# Lines that need updating for real AWS deployment:
- ECR repository: 123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-backend  # Fake account ID
- ACM certificate: arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id  # Fake cert
- RDS endpoint: sovd-production.c9akciq32.us-east-1.rds.amazonaws.com  # Fake endpoint
- Redis endpoint: sovd-production.abc123.ng.0001.use1.cache.amazonaws.com  # Fake endpoint
- IAM role: arn:aws:iam::123456789012:role/sovd-production-service-account-role  # Fake role
```

**Options**:
1. **If testing locally**: Create `values-local.yaml` with local equivalents (see Tip #2)
2. **If using AWS**: Replace with actual values from Terraform outputs or AWS console
3. **Document in report**: Clearly state which values are placeholders vs. actual

#### **Warning #2: External Secrets Operator Requirement**

**If `externalSecrets.enabled: true` in values:**
- External Secrets Operator MUST be installed in the cluster
- AWS Secrets MUST exist in Secrets Manager
- IAM role MUST have correct permissions
- ServiceAccount MUST have IRSA annotation

**Installation Check**:
```bash
# Check if External Secrets Operator is installed
kubectl get deployment -n external-secrets-system

# If not installed, either:
# Option 1: Install it (requires cluster-admin access)
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets-system --create-namespace --set installCRDs=true

# Option 2: Disable External Secrets in values
# In values-local.yaml:
externalSecrets:
  enabled: false

# Then manually create secrets:
kubectl create secret generic sovd-webapp-secrets -n staging \
  --from-literal=database-url=postgresql://... \
  --from-literal=jwt-secret=your-secret-key \
  --from-literal=redis-url=redis://...
```

#### **Warning #3: Migration Job Pre-Upgrade Hook**

The migration Job uses Helm hook `pre-upgrade,pre-install` with weight `-5`. This means:

- **Runs BEFORE any other resources** are created/updated
- **Blocks deployment** if it fails (backoffLimit: 3 attempts)
- **Timeout**: 10 minutes (activeDeadlineSeconds: 600)

**Implications**:
- If database is unreachable, entire deployment fails
- If migration has syntax error, entire deployment fails
- Migration logs are critical for troubleshooting

**How to check**:
```bash
# Check if migration job exists and succeeded
kubectl get jobs -n staging | grep migration

# Expected output:
# sovd-webapp-migration-xxxxx   1/1           15s        2m

# View logs
kubectl logs -n staging $(kubectl get pods -n staging -l app.kubernetes.io/component=migration -o name | head -1)

# Expected log output:
# Starting database migration...
# Database host: sovd-production.c9akciq32.us-east-1.rds.amazonaws.com
# Database name: sovd_production
# Running: alembic upgrade head
# INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
# INFO  [alembic.runtime.migration] Will assume transactional DDL.
# ✓ Database migration completed successfully
# Current migration revision:
# 001_initial_schema (head)
```

**If migration fails**:
```bash
# Check pod events
kubectl describe pod sovd-webapp-migration-xxxxx -n staging

# Check database connectivity from migration pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -n staging -- \
  psql postgresql://sovd_user:sovd_pass@<DB_HOST>:5432/sovd -c "SELECT 1;"
```

#### **Note #1: gRPC Vehicle Connector Status**

From `values-production.yaml` line 59:
```yaml
vehicleConnector:
  enabled: false
```

This means:
- **Vehicle connector deployment is DISABLED** in production
- Command execution will use the **mock** vehicle connector (backend-embedded)
- Real gRPC communication to external vehicles is **not tested** in this deployment

**For this task, this is acceptable** because:
- The mock connector (from I5.T6) simulates streaming responses
- It's sufficient for E2E testing of WebSocket communication
- Real gRPC vehicles are out of scope for deployment testing

**In deployment report, note**: "Vehicle connector disabled per production configuration. Commands use embedded mock connector."

#### **Note #2: Database Seed Data**

The database should already have seed data from I1.T4:
- **Admin user**: `admin` / `admin123` (role: admin)
- **Engineer user**: `engineer` / `engineer123` (role: engineer)
- **Vehicles**:
  - VIN: `WDD1234567890ABCD` (IP: 192.168.1.10)
  - VIN: `WDD0987654321ZYXW` (IP: 192.168.1.11)

**However**, if you're using a fresh database, you'll need to seed it.

**Option 1**: Run the init script manually:
```bash
# From project root
docker-compose exec backend bash -c "cd /app && bash /app/scripts/init_db.sh"
```

**Option 2**: Insert seed data via SQL:
```bash
# Connect to database
kubectl port-forward -n staging svc/postgresql 5432:5432
psql postgresql://sovd_user:sovd_pass@localhost:5432/sovd

# Insert users (passwords are bcrypt hashed)
INSERT INTO users (id, username, email, hashed_password, full_name, role, created_at, updated_at)
VALUES
  (gen_random_uuid(), 'admin', 'admin@sovd.com', '$2b$12$...', 'Admin User', 'admin', NOW(), NOW()),
  (gen_random_uuid(), 'engineer', 'engineer@sovd.com', '$2b$12$...', 'Engineer User', 'engineer', NOW(), NOW());

# Insert vehicles
INSERT INTO vehicles (id, vin, make, model, year, ip_address, created_at, updated_at)
VALUES
  (gen_random_uuid(), 'WDD1234567890ABCD', 'Mercedes', 'E-Class', 2024, '192.168.1.10', NOW(), NOW()),
  (gen_random_uuid(), 'WDD0987654321ZYXW', 'Mercedes', 'S-Class', 2024, '192.168.1.11', NOW(), NOW());
```

**Verify seed data**:
```bash
# Via API
curl http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Should return access_token if seed data exists
```

#### **Note #3: Smoke Test Script Exit Codes**

The `scripts/smoke_tests.sh` script is designed for CI/CD and will:
- Exit with code **0** if all tests pass
- Exit with code **1** if any test fails

**This is intentional** - do not modify the script to always return 0.

If a smoke test fails:
1. Identify which test failed (script shows ✗ FAIL message)
2. Investigate the root cause (check logs, curl the endpoint manually)
3. Fix the deployment issue
4. Re-run smoke tests
5. Document the issue and resolution in your report

**Example failed test**:
```
✗ FAIL: Backend Health (Readiness) - Expected HTTP 200, got 503
```

**Troubleshooting steps**:
```bash
# Check the endpoint directly
curl http://localhost:8000/health/ready

# Might return:
# {"status":"unhealthy","database":"disconnected","redis":"connected"}

# This indicates database connection issue - check database pod
kubectl get pods -n staging | grep postgres
```

---

## 4. Task Execution Strategy

Based on the analysis above, here is the recommended execution strategy for completing I5.T10:

### Phase 1: Pre-Deployment Preparation (15-30 minutes)

1. **✅ Determine Test Environment**
   - Decision: Local Kubernetes (minikube/kind) OR AWS EKS staging
   - Document your choice and rationale
   - Create issue tracker: `docs/runbooks/deployment_test_report.md` (start with template)

2. **✅ Prepare Infrastructure**
   - **If Local K8s**:
     - Start minikube/kind cluster: `minikube start --cpus=4 --memory=8192`
     - Verify: `kubectl cluster-info`
     - Start database/redis: `docker-compose up -d db redis` OR deploy via Helm
   - **If AWS EKS**:
     - Configure kubectl: `aws eks update-kubeconfig --region us-east-1 --name sovd-staging`
     - Verify: `kubectl get nodes`
     - Verify Terraform outputs: `cd infrastructure/terraform && terraform output`

3. **✅ Build Docker Images**
   - **Backend**:
     ```bash
     cd backend
     docker build -f Dockerfile.prod -t sovd-backend:local .
     # For minikube: minikube image load sovd-backend:local
     ```
   - **Frontend**:
     ```bash
     cd frontend
     docker build -f Dockerfile.prod -t sovd-frontend:local .
     # For minikube: minikube image load sovd-frontend:local
     ```
   - Capture build output (screenshot 01)

4. **✅ Create/Modify Helm Values**
   - **If Local**: Create `values-local.yaml` (see Tip #2)
   - **If AWS**: Verify/update `values-production.yaml` placeholders
   - Key settings:
     - Image repository and tag
     - Database/Redis endpoints
     - Secrets strategy (external vs manual)

5. **✅ Handle Secrets**
   - **If AWS EKS + External Secrets**:
     - Install External Secrets Operator (if not already)
     - Run: `scripts/create_aws_secrets.sh staging us-east-1`
     - Verify secrets created: `aws secretsmanager list-secrets`
   - **If Local K8s**:
     - Set `externalSecrets.enabled: false` in values
     - Create manual secrets:
       ```bash
       kubectl create namespace staging
       kubectl create secret generic sovd-webapp-secrets -n staging \
         --from-literal=database-url=postgresql://sovd_user:sovd_pass@192.168.1.10:5432/sovd \
         --from-literal=jwt-secret=$(openssl rand -base64 64 | tr -d '\n') \
         --from-literal=redis-url=redis://192.168.1.11:6379/0
       ```

### Phase 2: Helm Deployment (10-20 minutes)

1. **✅ Validate Helm Chart**
   ```bash
   cd infrastructure/helm
   helm lint sovd-webapp
   helm template sovd-webapp ./sovd-webapp -f values-production.yaml --debug | less
   # Check for syntax errors, verify resource rendering
   ```
   - Capture template output (screenshot 02 - optional)

2. **✅ Deploy with Helm**
   ```bash
   # If using values-local.yaml:
   helm upgrade --install sovd-webapp ./sovd-webapp \
     -f sovd-webapp/values.yaml \
     -f sovd-webapp/values-local.yaml \
     -n staging \
     --create-namespace \
     --wait \
     --timeout 10m

   # If using values-production.yaml:
   helm upgrade --install sovd-webapp ./sovd-webapp \
     -f sovd-webapp/values-production.yaml \
     -n staging \
     --create-namespace \
     --wait \
     --timeout 10m
   ```
   - Capture Helm output (screenshot 03) - **CRITICAL for report**
   - Note deployment duration

3. **✅ Monitor Deployment Progress**
   ```bash
   # Watch pods starting up
   kubectl get pods -n staging --watch

   # Check migration job
   kubectl get jobs -n staging

   # View migration logs
   kubectl logs -n staging $(kubectl get pods -n staging -l app.kubernetes.io/component=migration -o name)
   ```
   - Capture migration job status (screenshot 04)
   - Capture migration logs (screenshot 05)
   - Capture final pod status (screenshot 06) - **CRITICAL: all Running 1/1**

### Phase 3: Health & Smoke Tests (15-20 minutes)

1. **✅ Verify Pods Running**
   ```bash
   kubectl get pods -n staging
   kubectl get deployment -n staging
   kubectl get svc -n staging
   ```
   - All pods should be Running with 1/1 Ready
   - Expected: 8 pods (5 backend + 3 frontend)
   - Capture screenshot (already done in Phase 2 step 3)

2. **✅ Test Health Endpoints**
   ```bash
   # Port-forward backend
   kubectl port-forward -n staging svc/sovd-webapp-backend 8000:8000 &

   # Test liveness
   curl http://localhost:8000/health/live
   # Expected: 200 OK

   # Test readiness
   curl http://localhost:8000/health/ready
   # Expected: {"status":"healthy","database":"connected","redis":"connected"}
   ```
   - Capture health check response (screenshot 07)

3. **✅ Run Smoke Tests**
   ```bash
   # Port-forward frontend (in new terminal)
   kubectl port-forward -n staging svc/sovd-webapp-frontend 3000:80 &

   # Run smoke tests
   export API_BASE_URL=http://localhost:8000
   export FRONTEND_BASE_URL=http://localhost:3000
   ./scripts/smoke_tests.sh

   # Expected output:
   # ========================================
   #   Smoke Tests Summary
   # ========================================
   # Total Tests:  8
   # Passed:       8
   # Failed:       0
   # ========================================
   # ✅ All smoke tests PASSED
   ```
   - Capture smoke test output (screenshot 08) - **CRITICAL for report**

### Phase 4: E2E Functional Testing (20-30 minutes)

1. **✅ Frontend Login Flow**
   - Open browser: `http://localhost:3000`
   - Capture login page (screenshot 09)
   - Login with `admin` / `admin123`
   - Verify redirect to dashboard
   - Capture dashboard (screenshot 10)

2. **✅ Vehicles Page**
   - Navigate to Vehicles
   - Verify vehicle list displays (should show 2 vehicles from seed data)
   - Capture vehicles page (screenshot 11)

3. **✅ Command Submission & WebSocket**
   - Navigate to Commands page
   - Select a vehicle from dropdown
   - Select command: "ReadDTC"
   - Fill parameters: `{"ecuAddress": "0x10"}`
   - Submit command
   - Capture command form (screenshot 12)
   - **IMPORTANT**: Watch Response Viewer for real-time WebSocket updates
   - Verify responses stream in (should see 2-3 DTC responses)
   - Capture WebSocket responses (screenshot 13) - **CRITICAL for WebSocket verification**
   - Note: Command execution time (target: <5 seconds)

4. **✅ Verify WebSocket Connection**
   ```bash
   # In browser DevTools Network tab, check WebSocket connection
   # Should see: ws://localhost:8000/ws/responses/{command_id}?token=...
   # Status: 101 Switching Protocols
   # Messages: Multiple response events
   ```

### Phase 5: Monitoring Verification (10-15 minutes)

1. **✅ Prometheus Targets**
   ```bash
   # Port-forward Prometheus (if deployed)
   kubectl port-forward -n staging svc/prometheus 9090:9090 &

   # Open browser: http://localhost:9090/targets
   # Verify all targets are UP
   ```
   - Capture Prometheus targets page (screenshot 14)
   - Note: If Prometheus not deployed, skip and document in report

2. **✅ Grafana Dashboards**
   ```bash
   # Port-forward Grafana (if deployed)
   kubectl port-forward -n staging svc/grafana 3001:3000 &

   # Open browser: http://localhost:3001
   # Login: admin / admin (default Grafana credentials)
   # Navigate to dashboards: Operations, Commands, Vehicles
   ```
   - Capture Operations Dashboard (screenshot 15)
   - Capture Commands Dashboard (screenshot 16)
   - Capture Vehicles Dashboard (screenshot 17)
   - Note: If Grafana not deployed, skip and document

### Phase 6: HPA Load Testing (15-20 minutes)

1. **✅ Check Initial HPA Status**
   ```bash
   kubectl get hpa -n staging
   # Expected: MINPODS=3, MAXPODS=10, REPLICAS=3, CPU%=<10%
   ```
   - Capture HPA before load (screenshot 18)

2. **✅ Generate Load**
   ```bash
   # Option 1: Apache Bench (if installed)
   ab -n 30000 -c 100 -t 300 http://localhost:8000/api/v1/vehicles

   # Option 2: Simple load generator pod
   kubectl run load-generator --image=busybox --restart=Never -n staging -- \
     /bin/sh -c "while true; do wget -q -O- http://sovd-webapp-backend:8000/api/v1/vehicles; done"
   ```

3. **✅ Watch HPA Scaling**
   ```bash
   # In another terminal
   kubectl get hpa -n staging --watch

   # Expected progression (over 2-5 minutes):
   # REPLICAS: 3 → 4 → 5 (or higher if CPU > 70%)
   ```
   - Capture HPA during scaling (screenshot 19)
   - Note: Time to scale, max replicas reached, CPU % at peak

4. **✅ Verify Scaling**
   ```bash
   kubectl get pods -n staging
   # Should see 5+ backend pods (increased from 3)
   ```
   - Capture HPA after scaling (screenshot 20)

5. **✅ Stop Load and Scale Down**
   ```bash
   # Stop load generator
   kubectl delete pod load-generator -n staging

   # Watch scale down (takes 5+ minutes due to stabilization window)
   kubectl get hpa -n staging --watch

   # Expected: Gradual scale down back to 3 replicas
   ```

### Phase 7: External Secrets Verification (10-15 minutes, if applicable)

**Only if using AWS + External Secrets Operator:**

1. **✅ Check SecretStore**
   ```bash
   kubectl get secretstore -n staging
   kubectl describe secretstore aws-secrets-manager -n staging

   # Expected status: Ready
   ```
   - Capture SecretStore status (screenshot 21)

2. **✅ Check ExternalSecret**
   ```bash
   kubectl get externalsecret -n staging
   kubectl describe externalsecret sovd-webapp-external-secrets -n staging

   # Expected:
   # Status: Ready
   # Conditions: SecretSynced=True
   ```
   - Capture ExternalSecret status (screenshot 22)

3. **✅ Verify K8s Secret Created**
   ```bash
   kubectl get secret sovd-webapp-secrets -n staging
   # Should exist with 3 keys: database-url, jwt-secret, redis-url

   # Verify keys (without exposing values)
   kubectl get secret sovd-webapp-secrets -n staging -o jsonpath='{.data}' | jq 'keys'
   ```

4. **✅ Test Secret Rotation (optional, time-permitting)**
   ```bash
   # Update secret in AWS
   aws secretsmanager put-secret-value \
     --secret-id sovd/staging/jwt \
     --secret-string '{"JWT_SECRET":"new-rotated-secret-value"}' \
     --region us-east-1

   # Force immediate sync (delete K8s secret, operator recreates it)
   kubectl delete secret sovd-webapp-secrets -n staging

   # Wait 1-2 minutes and verify recreated
   kubectl get secret sovd-webapp-secrets -n staging

   # Restart backend pods to pick up new secret
   kubectl rollout restart deployment sovd-webapp-backend -n staging

   # Verify app still works
   curl http://localhost:8000/health/ready
   ```

**If NOT using External Secrets:**
- Document in report: "External Secrets Operator not tested - disabled for local environment"
- Show manual K8s secret creation command used

### Phase 8: Rollback Testing (10-15 minutes)

1. **✅ Check Helm History**
   ```bash
   helm history sovd-webapp -n staging

   # Expected output (after first deployment):
   # REVISION  STATUS      CHART           APP VERSION  DESCRIPTION
   # 1         deployed    sovd-webapp-1.0 1.0.0        Install complete
   ```

2. **✅ Make a Change and Upgrade**
   ```bash
   # Modify something (e.g., change replica count)
   helm upgrade sovd-webapp ./sovd-webapp \
     -f values-production.yaml \
     --set backend.replicaCount=7 \
     -n staging \
     --wait

   # Verify change
   kubectl get deployment sovd-webapp-backend -n staging -o jsonpath='{.spec.replicas}'
   # Should show: 7

   # Check history again
   helm history sovd-webapp -n staging
   # Should show revision 2
   ```

3. **✅ Rollback to Previous Version**
   ```bash
   helm rollback sovd-webapp -n staging

   # Or specific revision:
   # helm rollback sovd-webapp 1 -n staging

   # Wait for rollback to complete
   kubectl rollout status deployment sovd-webapp-backend -n staging
   ```
   - Capture rollback output (screenshot 23)

4. **✅ Verify Rollback Success**
   ```bash
   # Check replicas back to original
   kubectl get deployment sovd-webapp-backend -n staging -o jsonpath='{.spec.replicas}'
   # Should show: 3 (or 5 if using production values)

   # Verify app still functional
   curl http://localhost:8000/health/ready
   # Expected: {"status":"healthy",...}

   # Check pods
   kubectl get pods -n staging
   ```
   - Capture pods after rollback (screenshot 24)

5. **✅ Verify Helm History**
   ```bash
   helm history sovd-webapp -n staging

   # Expected:
   # REVISION  STATUS        CHART           DESCRIPTION
   # 1         superseded    sovd-webapp-1.0 Install complete
   # 2         superseded    sovd-webapp-1.0 Upgrade complete
   # 3         deployed      sovd-webapp-1.0 Rollback to 1
   ```

### Phase 9: Documentation (30-60 minutes)

1. **✅ Create Deployment Report**
   - Use the template provided in Section 5
   - File: `docs/runbooks/deployment_test_report.md`
   - Embed all screenshots (minimum 15, ideally 24)
   - Document all test results (pass/fail)

2. **✅ Complete All Sections**
   - Executive Summary: Overall status, key findings
   - Test Environment: Specify local vs AWS, versions, configurations
   - Test Results Summary: Table of all tests with pass/fail
   - Detailed Test Execution: Step-by-step with commands and screenshots
   - Issues & Resolutions: Document every problem encountered
   - Performance Metrics: Record timings and resource usage
   - Recommendations: Based on findings
   - Conclusion: Readiness assessment

3. **✅ Quality Checklist**
   - [ ] All acceptance criteria addressed
   - [ ] Minimum 15 screenshots embedded
   - [ ] All commands documented with outputs
   - [ ] Issues and resolutions section complete
   - [ ] Performance metrics table filled
   - [ ] Executive summary and conclusion written
   - [ ] File saved to `docs/runbooks/deployment_test_report.md`

### Phase 10: Final Verification (5-10 minutes)

1. **✅ Re-run Critical Tests**
   ```bash
   # Health check
   curl http://localhost:8000/health/ready

   # Smoke tests
   ./scripts/smoke_tests.sh

   # Frontend login
   # Open browser and verify login works
   ```

2. **✅ Review Acceptance Criteria**
   - Go through checklist in Section 6
   - Mark each item as complete
   - Identify any gaps

3. **✅ Cleanup (optional)**
   ```bash
   # If desired, clean up test environment
   helm uninstall sovd-webapp -n staging
   kubectl delete namespace staging

   # Or leave running for review
   ```

---

## 5. Deployment Report Template

Create `docs/runbooks/deployment_test_report.md` with the following structure:

```markdown
# Production Deployment Test Report - SOVD WebApp

**Test Date**: 2025-10-31
**Tester**: [Your Name]
**Environment**: [Local Kubernetes (minikube v1.32.0) | AWS EKS Staging us-east-1]
**Helm Chart Version**: 1.0.0
**Backend Image**: sovd-backend:local [or ECR tag]
**Frontend Image**: sovd-frontend:local [or ECR tag]
**Overall Status**: ✅ PASSED | ⚠️ PARTIAL | ❌ FAILED

---

## Executive Summary

**Deployment Result**: [Successful | Partially Successful | Failed]

**Key Findings**:
- [Finding 1: e.g., "Deployment succeeded on first attempt with zero downtime"]
- [Finding 2: e.g., "HPA scaling took 3m 15s to scale from 3 to 5 pods"]
- [Finding 3: e.g., "WebSocket connections stable with no disconnections"]

**Critical Issues** (if any):
- [Issue 1: e.g., "Database migration initially failed due to network timeout - resolved by increasing timeout"]
- [Issue 2: None]

**Recommendations**:
1. [Recommendation 1: e.g., "Consider pre-warming database connections before deployment"]
2. [Recommendation 2: e.g., "Document External Secrets Operator installation in CI/CD pipeline"]

**Production Readiness**: [Ready | Ready with caveats | Not ready]

---

## Test Environment

**Kubernetes Cluster**:
- Type: [minikube | kind | Docker Desktop K8s | AWS EKS]
- Version: [e.g., v1.28.0]
- Nodes: [e.g., 1 node (local) | 3 nodes across 3 AZs (AWS)]
- Node Resources: [e.g., 4 CPUs, 8GB RAM per node]

**Database**:
- Type: [PostgreSQL container in docker-compose | AWS RDS PostgreSQL Multi-AZ]
- Version: [e.g., PostgreSQL 15.3]
- Endpoint: [e.g., localhost:5432 | sovd-staging.xxx.us-east-1.rds.amazonaws.com]
- Persistence: [Ephemeral | Persistent Volume | RDS]

**Redis**:
- Type: [Redis container | AWS ElastiCache]
- Version: [e.g., Redis 7.0]
- Endpoint: [e.g., localhost:6379 | sovd-staging.xxx.ng.0001.use1.cache.amazonaws.com]

**Secrets Management**:
- Strategy: [Kubernetes Secrets (manual) | AWS Secrets Manager + External Secrets Operator]
- External Secrets Operator Version: [e.g., v0.9.11 | N/A]

**Image Registry**:
- Type: [Local Docker images | AWS ECR]
- Repository: [e.g., local/sovd-backend | 123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-backend]

**Monitoring**:
- Prometheus: [Deployed | Not deployed]
- Grafana: [Deployed | Not deployed]

---

## Test Results Summary

| # | Test Category | Status | Duration | Notes |
|---|--------------|--------|----------|-------|
| 1 | Helm Deployment | ✅ PASS | 4m 12s | Deployed successfully on first attempt |
| 2 | Migration Job | ✅ PASS | 23s | Alembic upgrade completed without errors |
| 3 | Pods Running & Ready | ✅ PASS | 2m 45s | 8 pods total, all Running 1/1 Ready |
| 4 | Health Endpoints | ✅ PASS | 150ms | /health/ready returned 200 with healthy status |
| 5 | Smoke Tests | ✅ PASS | 18s | 8/8 tests passed |
| 6 | Frontend E2E Flow | ✅ PASS | 12s | Login → Vehicles → Command → WebSocket responses |
| 7 | Prometheus Targets | ✅ PASS | - | All 8 targets UP |
| 8 | Grafana Dashboards | ✅ PASS | - | 3 dashboards loaded with metrics |
| 9 | HPA Scaling | ✅ PASS | 3m 15s | Scaled from 3 to 5 backend pods at 75% CPU |
| 10 | Migration Pre-Hook | ✅ PASS | 23s | Job completed before deployment |
| 11 | External Secrets | ⚠️ SKIP | - | Disabled for local testing (documented) |
| 12 | Rollback | ✅ PASS | 1m 32s | Rollback succeeded, app functional |

**Overall Pass Rate**: 11/12 (91.7%) - 1 skipped with justification

---

## Detailed Test Execution

### 1. Pre-Deployment: Build Docker Images

**Commands Executed**:
```bash
# Backend
cd backend
docker build -f Dockerfile.prod -t sovd-backend:local .
minikube image load sovd-backend:local

# Frontend
cd frontend
docker build -f Dockerfile.prod -t sovd-frontend:local .
minikube image load sovd-frontend:local
```

**Results**:
- Backend image size: 485 MB
- Frontend image size: 42 MB
- Build time: 3m 45s (backend), 1m 12s (frontend)

**Screenshots**:
![Docker Build Backend](screenshots/01-docker-build-backend.png)
![Docker Build Frontend](screenshots/02-docker-build-frontend.png)

**Status**: ✅ PASS
**Issues**: None

---

### 2. Helm Deployment

**Commands Executed**:
```bash
# Created values-local.yaml with local K8s overrides
# Disabled External Secrets, set local image tags, adjusted endpoints

helm upgrade --install sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f sovd-webapp/values.yaml \
  -f sovd-webapp/values-local.yaml \
  -n staging \
  --create-namespace \
  --wait \
  --timeout 10m
```

**Results**:
- Deployment duration: 4m 12s
- Resources created: 15 (Deployments, Services, ConfigMaps, Secrets, HPA, Job, Ingress)
- All resources created successfully

**Screenshots**:
![Helm Install Output](screenshots/03-helm-install.png)

**Status**: ✅ PASS
**Issues**: None

---

### 3. Migration Job Verification

**Commands Executed**:
```bash
kubectl get jobs -n staging
kubectl logs -n staging sovd-webapp-migration-xxxxx
```

**Results**:
- Migration Job status: Completed (1/1)
- Execution time: 23 seconds
- Migrations applied: Already at head (001_initial_schema)

**Screenshots**:
![Migration Job Status](screenshots/04-migration-job.png)
![Migration Logs](screenshots/05-migration-logs.png)

**Logs Output**:
```
Starting database migration...
Database host: 192.168.49.2
Database name: sovd
Running: alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
✓ Database migration completed successfully
Current migration revision:
001_initial_schema (head)
```

**Status**: ✅ PASS
**Issues**: None

---

### 4. Pods Running & Ready

**Commands Executed**:
```bash
kubectl get pods -n staging
kubectl get deployments -n staging
```

**Results**:
- Backend pods: 5/5 Running, 5/5 Ready
- Frontend pods: 3/3 Running, 3/3 Ready
- Total pods: 8/8 healthy
- Average pod startup time: 42 seconds

**Screenshots**:
![All Pods Running](screenshots/06-pods-running.png)

**Pod Details**:
```
NAME                                READY   STATUS    RESTARTS   AGE
sovd-webapp-backend-7d9c8b-xxxx     1/1     Running   0          2m
sovd-webapp-backend-7d9c8b-yyyy     1/1     Running   0          2m
sovd-webapp-backend-7d9c8b-zzzz     1/1     Running   0          2m
sovd-webapp-backend-7d9c8b-aaaa     1/1     Running   0          2m
sovd-webapp-backend-7d9c8b-bbbb     1/1     Running   0          2m
sovd-webapp-frontend-5f8d7c-xxxx    1/1     Running   0          2m
sovd-webapp-frontend-5f8d7c-yyyy    1/1     Running   0          2m
sovd-webapp-frontend-5f8d7c-zzzz    1/1     Running   0          2m
```

**Status**: ✅ PASS
**Issues**: None

---

### 5. Health Endpoints

**Commands Executed**:
```bash
kubectl port-forward -n staging svc/sovd-webapp-backend 8000:8000 &
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

**Results**:
- `/health/live`: 200 OK
- `/health/ready`: 200 OK with healthy status
- Response time: 150ms average

**Screenshots**:
![Health Check Response](screenshots/07-health-check.png)

**Response Body**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2025-10-31T15:30:00Z"
}
```

**Status**: ✅ PASS
**Issues**: None

---

### 6. Smoke Tests

**Commands Executed**:
```bash
kubectl port-forward -n staging svc/sovd-webapp-frontend 3000:80 &
export API_BASE_URL=http://localhost:8000
export FRONTEND_BASE_URL=http://localhost:3000
./scripts/smoke_tests.sh
```

**Results**:
- Tests run: 8
- Tests passed: 8
- Tests failed: 0
- Execution time: 18 seconds

**Screenshots**:
![Smoke Test Output](screenshots/08-smoke-tests.png)

**Test Breakdown**:
```
✓ PASS: Backend Health (Liveness)
✓ PASS: Backend Health (Readiness)
✓ PASS: API Documentation (Swagger)
✓ PASS: OpenAPI Specification
✓ PASS: Prometheus Metrics
✓ PASS: Frontend Application
✓ PASS: Frontend Static Assets
✓ PASS: CORS Headers
========================================
✅ All smoke tests PASSED
```

**Status**: ✅ PASS
**Issues**: None

---

### 7. Frontend E2E Flow

**Test Steps**:
1. Navigate to http://localhost:3000
2. Login with admin/admin123
3. Navigate to Vehicles page
4. Navigate to Commands page
5. Select vehicle VIN `WDD1234567890ABCD`
6. Submit ReadDTC command with parameters `{"ecuAddress": "0x10"}`
7. Watch WebSocket responses stream in real-time

**Results**:
- Login successful: ✅
- Dashboard loaded: ✅
- Vehicles displayed (2 vehicles): ✅
- Command submission successful: ✅
- WebSocket connection established: ✅
- Responses received (3 chunks): ✅
- Command status updated to "completed": ✅

**Screenshots**:
![Login Page](screenshots/09-login.png)
![Dashboard](screenshots/10-dashboard.png)
![Vehicles List](screenshots/11-vehicles.png)
![Command Submission](screenshots/12-command-submit.png)
![WebSocket Responses](screenshots/13-websocket-responses.png)

**Timings**:
- Login time: <500ms
- Page load times: <1s average
- Command execution (E2E): 3.2s (including WebSocket streaming)
- WebSocket connection time: 450ms

**Status**: ✅ PASS
**Issues**: None

---

### 8. Prometheus Targets

**Commands Executed**:
```bash
kubectl port-forward -n staging svc/prometheus 9090:9090 &
# Open browser: http://localhost:9090/targets
```

**Results**:
- All targets: UP
- Backend instances: 5/5 UP
- Frontend instances: 3/3 UP

**Screenshots**:
![Prometheus Targets](screenshots/14-prometheus-targets.png)

**Target Details**:
```
sovd-webapp-backend (5/5 up)
- backend-0: UP (last scrape: 15s ago)
- backend-1: UP (last scrape: 12s ago)
- backend-2: UP (last scrape: 18s ago)
- backend-3: UP (last scrape: 10s ago)
- backend-4: UP (last scrape: 14s ago)

sovd-webapp-frontend (3/3 up)
- frontend-0: UP (last scrape: 16s ago)
- frontend-1: UP (last scrape: 13s ago)
- frontend-2: UP (last scrape: 11s ago)
```

**Status**: ✅ PASS
**Issues**: None

---

### 9. Grafana Dashboards

**Commands Executed**:
```bash
kubectl port-forward -n staging svc/grafana 3001:3000 &
# Open browser: http://localhost:3001
# Login: admin/admin
# Navigate to dashboards
```

**Results**:
- Operations Dashboard: ✅ Loaded, showing HTTP request rates, error rates, latency
- Commands Dashboard: ✅ Loaded, showing command execution metrics
- Vehicles Dashboard: ✅ Loaded, showing vehicle connection status

**Screenshots**:
![Grafana Operations Dashboard](screenshots/15-grafana-operations.png)
![Grafana Commands Dashboard](screenshots/16-grafana-commands.png)
![Grafana Vehicles Dashboard](screenshots/17-grafana-vehicles.png)

**Metrics Observed**:
- HTTP request rate: ~15 req/s (during testing)
- P95 latency: 245ms
- Error rate: 0%
- Commands executed: 5 total
- Active WebSocket connections: 1

**Status**: ✅ PASS
**Issues**: None

---

### 10. HPA Load Testing

**Commands Executed**:
```bash
# Check initial state
kubectl get hpa -n staging

# Generate load
kubectl run load-generator --image=busybox --restart=Never -n staging -- \
  /bin/sh -c "while true; do wget -q -O- http://sovd-webapp-backend:8000/api/v1/vehicles; done"

# Watch HPA scaling
kubectl get hpa -n staging --watch
```

**Results**:
- Initial replicas: 3
- Peak replicas: 5
- Time to scale 3→5: 3m 15s
- Peak CPU utilization: 78%
- Final replicas (after load stopped): 3 (scaled down after 5m)

**Screenshots**:
![HPA Before Load](screenshots/18-hpa-before.png)
![HPA Scaling Up](screenshots/19-hpa-scaling.png)
![HPA After Scaling](screenshots/20-hpa-after.png)

**HPA Event Timeline**:
```
00:00  - REPLICAS=3, CPU=8%
01:30  - Load generator started
02:00  - CPU=65% (below threshold)
02:45  - CPU=78% (above 70% threshold)
03:15  - REPLICAS=4 (first scale-up)
04:00  - CPU=72% (still above threshold)
04:45  - REPLICAS=5 (second scale-up)
05:30  - CPU=68% (stabilized below threshold)
06:00  - Load generator stopped
11:00  - CPU=15%
13:00  - REPLICAS=4 (scale-down begins)
18:00  - REPLICAS=3 (back to minimum)
```

**Status**: ✅ PASS
**Issues**: None
**Note**: HPA behavior matched expectations - scaling up at 70% CPU, gradual scale-down with 5-minute stabilization window.

---

### 11. External Secrets Sync

**Status**: ⚠️ SKIPPED (Not Applicable for Local Testing)

**Reason**:
External Secrets Operator requires AWS infrastructure (EKS, IAM roles, Secrets Manager). For local Kubernetes testing (minikube), External Secrets was disabled and replaced with manual Kubernetes Secrets.

**Alternative Approach**:
- Set `externalSecrets.enabled: false` in values-local.yaml
- Created Kubernetes Secret manually:
  ```bash
  kubectl create secret generic sovd-webapp-secrets -n staging \
    --from-literal=database-url=postgresql://sovd_user:sovd_pass@192.168.49.2:5432/sovd \
    --from-literal=jwt-secret=$(openssl rand -base64 64 | tr -d '\n') \
    --from-literal=redis-url=redis://192.168.49.2:6379/0
  ```
- Verified backend pods loaded secrets correctly from environment variables

**Screenshots**: N/A

**Recommendations for Production**:
- Install External Secrets Operator on AWS EKS cluster
- Create secrets in AWS Secrets Manager using `scripts/create_aws_secrets.sh`
- Test secret rotation with `refreshInterval: 5m` configuration
- Verify IRSA authentication works correctly

---

### 12. Rollback Testing

**Commands Executed**:
```bash
# Check initial history
helm history sovd-webapp -n staging

# Make a change (increase backend replicas)
helm upgrade sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f values-local.yaml \
  --set backend.replicaCount=7 \
  -n staging

# Verify change
kubectl get deployment sovd-webapp-backend -n staging -o jsonpath='{.spec.replicas}'
# Output: 7

# Rollback
helm rollback sovd-webapp -n staging

# Verify rollback
kubectl get deployment sovd-webapp-backend -n staging -o jsonpath='{.spec.replicas}'
# Output: 3 (back to original)
```

**Results**:
- Rollback duration: 1m 32s
- Pods scaled back from 7 to 3: ✅
- Zero downtime during rollback: ✅
- Application remained functional: ✅

**Screenshots**:
![Rollback Output](screenshots/23-rollback.png)
![Pods After Rollback](screenshots/24-pods-after-rollback.png)

**Helm History After Rollback**:
```
REVISION  STATUS      CHART             APP VERSION  DESCRIPTION
1         superseded  sovd-webapp-1.0.0 1.0.0        Install complete
2         superseded  sovd-webapp-1.0.0 1.0.0        Upgrade complete
3         deployed    sovd-webapp-1.0.0 1.0.0        Rollback to 1
```

**Post-Rollback Verification**:
```bash
curl http://localhost:8000/health/ready
# Response: {"status":"healthy","database":"connected","redis":"connected"}

# Frontend still accessible
# Login still works
# Command submission still works
```

**Status**: ✅ PASS
**Issues**: None

---

## Issues Encountered & Resolutions

### Issue 1: Database Connection Timeout During Migration

**Severity**: High
**Description**:
Initial migration job failed with error:
```
ERROR [alembic.util.messaging] Can't connect to database: connection timeout
```

**Impact**:
Deployment blocked - Helm pre-upgrade hook prevented all resources from being created.

**Root Cause**:
Database pod was still initializing when migration job started. Health check passed (container running) but PostgreSQL was not ready to accept connections yet.

**Resolution**:
1. Increased migration job's `initialDelaySeconds` to 30 seconds (was 10)
2. Added retry logic to migration script (already in template with `backoffLimit: 3`)
3. Migration succeeded on second attempt after waiting for database readiness

**Time to Resolve**: 5 minutes

**Prevention**:
- Document database warmup time in deployment runbook
- Consider adding explicit database readiness check to migration script (e.g., `pg_isready`)

---

### Issue 2: Port-Forward Connections Dropped During Load Test

**Severity**: Low
**Description**:
During HPA load testing, `kubectl port-forward` connections occasionally dropped, interrupting the load generator.

**Impact**:
Minor - had to restart port-forward 2 times during load test. Did not affect HPA scaling test results.

**Root Cause**:
`kubectl port-forward` is not designed for sustained high-load scenarios. It's a development/debugging tool with stability limitations.

**Resolution**:
1. Used direct pod IP instead of port-forward for load generator
2. Load generator pod ran inside cluster, eliminating need for port-forward

**Time to Resolve**: 3 minutes

**Prevention**:
- For production load testing, use Ingress or LoadBalancer service instead of port-forward
- Document this limitation in load testing procedures

---

### Issue 3: Smoke Test False Positive on Frontend Static Assets

**Severity**: Low
**Description**:
Smoke test for "Frontend Static Assets" initially failed with:
```
✗ FAIL: Frontend Static Assets - No Vite/React markers found
```

**Impact**:
Deployment appeared to fail smoke tests, but frontend was actually working.

**Root Cause**:
Frontend was built in production mode, which minifies JavaScript and removes dev markers like `__vite__`. Smoke test was looking for these markers.

**Resolution**:
1. Updated smoke test to check for `root` div instead (which exists in prod and dev)
2. Test now passes in both development and production builds

**Time to Resolve**: 8 minutes

**Prevention**:
- Smoke tests should use production-agnostic checks
- Document differences between dev and prod builds

---

## Performance Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Helm Deployment Time | 4m 12s | <5m | ✅ PASS |
| Migration Execution Time | 23s | <1m | ✅ PASS |
| Average Pod Startup Time | 42s | <1m | ✅ PASS |
| /health/ready Response Time | 150ms | <200ms | ✅ PASS |
| Frontend Page Load Time (FCP) | 0.8s | <1.5s | ✅ PASS |
| Frontend Page Load Time (TTI) | 2.1s | <3s | ✅ PASS |
| Command Execution Time (E2E) | 3.2s | <5s | ✅ PASS |
| WebSocket Connection Time | 450ms | <1s | ✅ PASS |
| Smoke Tests Execution Time | 18s | <30s | ✅ PASS |
| HPA Scaling Time (3→5 pods) | 3m 15s | <5m | ✅ PASS |
| Rollback Time | 1m 32s | <3m | ✅ PASS |

**Resource Utilization (at steady state)**:
- Backend CPU: 5-12% per pod (stable)
- Backend Memory: 180-220 MB per pod
- Frontend CPU: 1-3% per pod
- Frontend Memory: 45-60 MB per pod
- Database CPU: 8%
- Database Memory: 512 MB
- Redis CPU: 2%
- Redis Memory: 64 MB

**Overall Performance**: All metrics within acceptable ranges for staging environment.

---

## Recommendations

### 1. Document External Secrets Setup for Production

**Priority**: High
**Rationale**: External Secrets Operator was not tested in this local deployment. Production will require it.

**Action Items**:
- Add External Secrets Operator installation to CI/CD pipeline or infrastructure provisioning
- Create runbook section for troubleshooting External Secrets sync issues
- Test secret rotation in staging environment before production

---

### 2. Improve Migration Job Database Readiness Check

**Priority**: Medium
**Rationale**: Migration job initially failed due to database not ready. Adding explicit readiness check would improve reliability.

**Action Items**:
- Update migration-job.yaml to include database readiness check (e.g., `pg_isready` loop)
- Test with database that has longer startup time
- Document recommended `initialDelaySeconds` values

---

### 3. Add Load Balancer or Ingress for Production Load Testing

**Priority**: Medium
**Rationale**: Port-forwarding is not suitable for sustained load testing. Production should use proper load balancer.

**Action Items**:
- Configure ALB Ingress Controller on AWS EKS
- Test HPA scaling with real production traffic patterns
- Document load testing procedures with Ingress endpoint

---

### 4. Enhance Smoke Tests for Production Builds

**Priority**: Low
**Rationale**: Some smoke tests had to be adjusted for production builds. This should be documented.

**Action Items**:
- Review all smoke tests for dev vs prod compatibility
- Add flag to smoke_tests.sh for `--production` mode
- Document expected differences between dev and prod builds

---

### 5. Pre-warm Database Connections Before Deployment

**Priority**: Low
**Rationale**: Database was slow to accept connections during migration. Pre-warming could reduce deployment time.

**Action Items**:
- Add database connection pool warming to backend startup
- Consider init container for database readiness check
- Measure impact on deployment time

---

## Conclusion

**Overall Assessment**: ✅ **DEPLOYMENT TEST PASSED**

**Summary**:
The end-to-end production deployment test in a staging-like environment (local Kubernetes with minikube) was **successful**. All critical acceptance criteria were met:

✅ Helm deployment succeeded on first attempt
✅ All 8 pods (5 backend, 3 frontend) reached Running/Ready state
✅ Health endpoints returned healthy status
✅ Frontend was accessible and login worked
✅ Full E2E flow (login → vehicles → command → real-time WebSocket responses) functioned correctly
✅ WebSocket connections established and streamed responses
✅ Prometheus targets were healthy (all UP)
✅ Grafana dashboards loaded and displayed metrics
✅ HPA scaled from 3 to 5 backend pods when CPU exceeded 70%
✅ Migration Job completed successfully before deployment
✅ Rollback succeeded and application remained functional
✅ Smoke tests all passed (8/8)

**Caveats**:
- External Secrets Operator not tested (disabled for local environment)
- AWS-specific features not validated (ALB, RDS Multi-AZ, ElastiCache)
- Load testing performed with simple load generator (not production-scale traffic)

**Production Readiness**: ✅ **READY WITH CAVEATS**

The application is ready for production deployment on AWS EKS with the following prerequisites:
1. External Secrets Operator installed and tested
2. AWS infrastructure provisioned (EKS, RDS, ElastiCache, ALB)
3. Secrets created in AWS Secrets Manager
4. Load testing performed with ALB Ingress
5. Recommendations from this report implemented

**Confidence Level**: **High (85%)**

The deployment procedures, Helm charts, and application code are production-ready. The remaining 15% uncertainty is due to untested AWS-specific integrations, which should be validated in an actual AWS EKS staging environment.

**Next Steps**:
1. Provision AWS EKS staging cluster (if not already done)
2. Install External Secrets Operator on staging cluster
3. Repeat this deployment test on AWS EKS staging
4. Address recommendations listed in section above
5. Perform production deployment after staging validation

---

## Appendix A: Helm Values Used

### values-local.yaml (created for local testing)

```yaml
global:
  namespace: staging
  domain: localhost

backend:
  replicaCount: 3
  image:
    repository: sovd-backend
    tag: "local"
    pullPolicy: Never

frontend:
  replicaCount: 2
  image:
    repository: sovd-frontend
    tag: "local"
    pullPolicy: Never

externalSecrets:
  enabled: false

config:
  database:
    host: "192.168.49.2"  # minikube host IP
    port: "5432"
    name: "sovd"
    user: "sovd_user"
  redis:
    host: "192.168.49.2"
    port: "6379"

ingress:
  enabled: false
```

---

## Appendix B: Environment Variables

**Backend Pods**:
- `DATABASE_URL`: `postgresql://sovd_user:***@192.168.49.2:5432/sovd` (from K8s Secret)
- `REDIS_URL`: `redis://192.168.49.2:6379/0` (from K8s Secret)
- `JWT_SECRET`: `[64-character random string]` (from K8s Secret)
- `JWT_ALGORITHM`: `HS256` (from ConfigMap)
- `LOG_LEVEL`: `INFO` (from ConfigMap)
- `ENVIRONMENT`: `staging` (from ConfigMap)

**Frontend Pods**:
- `VITE_API_BASE_URL`: `http://sovd-webapp-backend:8000` (from ConfigMap)

**Migration Job**:
- `DATABASE_URL`: `postgresql://sovd_user:***@192.168.49.2:5432/sovd` (from K8s Secret)
- `LOG_LEVEL`: `INFO`
- `PYTHONUNBUFFERED`: `1`

---

## Appendix C: Resource Utilization

**Backend Deployment**:
- Replicas: 3 (initial) → 5 (peak) → 3 (final)
- CPU Request: 250m per pod
- CPU Limit: 500m per pod
- Memory Request: 256Mi per pod
- Memory Limit: 512Mi per pod
- Observed CPU: 5-12% of limit
- Observed Memory: 180-220 MB (70-85% of request)

**Frontend Deployment**:
- Replicas: 2
- CPU Request: 100m per pod
- CPU Limit: 200m per pod
- Memory Request: 64Mi per pod
- Memory Limit: 128Mi per pod
- Observed CPU: 1-3% of limit
- Observed Memory: 45-60 MB (70-94% of request)

**Database (PostgreSQL)**:
- Container: postgres:15
- CPU: No limit set
- Memory: No limit set
- Observed CPU: 8% (of node total)
- Observed Memory: 512 MB

**Redis**:
- Container: redis:7
- CPU: No limit set
- Memory: No limit set
- Observed CPU: 2% (of node total)
- Observed Memory: 64 MB

---

## Appendix D: Test Execution Timestamps

| Event | Timestamp | Duration from Start |
|-------|-----------|-------------------|
| Test Start | 2025-10-31 14:00:00 | 0m |
| Docker Builds Complete | 2025-10-31 14:05:30 | 5m 30s |
| Helm Install Initiated | 2025-10-31 14:06:00 | 6m |
| Migration Job Started | 2025-10-31 14:06:15 | 6m 15s |
| Migration Job Completed | 2025-10-31 14:06:38 | 6m 38s |
| All Pods Running | 2025-10-31 14:08:45 | 8m 45s |
| Health Checks Passed | 2025-10-31 14:09:00 | 9m |
| Smoke Tests Complete | 2025-10-31 14:09:18 | 9m 18s |
| E2E Flow Complete | 2025-10-31 14:09:40 | 9m 40s |
| HPA Load Test Started | 2025-10-31 14:10:00 | 10m |
| HPA Scaled to 5 Pods | 2025-10-31 14:13:15 | 13m 15s |
| HPA Load Test Complete | 2025-10-31 14:18:00 | 18m |
| Rollback Test Complete | 2025-10-31 14:20:30 | 20m 30s |
| Test End | 2025-10-31 14:21:00 | 21m |

**Total Test Duration**: 21 minutes (deployment + verification + testing)

---

## Appendix E: Screenshots Index

1. `01-docker-build-backend.png` - Backend Docker build output
2. `02-docker-build-frontend.png` - Frontend Docker build output
3. `03-helm-install.png` - Helm install command output
4. `04-migration-job.png` - Migration job status
5. `05-migration-logs.png` - Migration job logs
6. `06-pods-running.png` - All pods in Running state
7. `07-health-check.png` - Health endpoint response
8. `08-smoke-tests.png` - Smoke test output
9. `09-login.png` - Frontend login page
10. `10-dashboard.png` - Frontend dashboard after login
11. `11-vehicles.png` - Vehicles list page
12. `12-command-submit.png` - Command submission form
13. `13-websocket-responses.png` - Real-time WebSocket responses
14. `14-prometheus-targets.png` - Prometheus targets page
15. `15-grafana-operations.png` - Grafana operations dashboard
16. `16-grafana-commands.png` - Grafana commands dashboard
17. `17-grafana-vehicles.png` - Grafana vehicles dashboard
18. `18-hpa-before.png` - HPA status before load
19. `19-hpa-scaling.png` - HPA during scaling
20. `20-hpa-after.png` - HPA after scaling
21. `21-secretstore.png` - SecretStore status (if tested)
22. `22-externalsecret.png` - ExternalSecret status (if tested)
23. `23-rollback.png` - Rollback command output
24. `24-pods-after-rollback.png` - Pods after rollback

---

**Report Version**: 1.0
**Last Updated**: 2025-10-31
**Author**: [Your Name]
**Related Task**: I5.T10
```

---

## 6. Success Criteria Checklist

Use this checklist to ensure all acceptance criteria are met before marking the task complete:

### Deployment Criteria

- [ ] **Helm deploys successfully** - No errors during `helm upgrade --install`, all resources created
- [ ] **All pods Running and Ready** - `kubectl get pods` shows all pods with status "Running" and "1/1" ready
- [ ] **/health/ready returns 200** - `curl /health/ready` returns HTTP 200 with `{"status":"healthy",...}`
- [ ] **Frontend accessible** - Can load login page at http://localhost:3000 or via Ingress
- [ ] **Login works** - Can successfully authenticate with admin/admin123

### E2E Flow Criteria

- [ ] **Full E2E flow works** - Can complete: login → navigate to vehicles → submit command → see responses
- [ ] **WebSocket connected** - DevTools Network tab shows WebSocket connection with 101 status
- [ ] **Responses stream** - Real-time WebSocket messages appear in Response Viewer (2-3 chunks)

### Monitoring Criteria

- [ ] **Prometheus targets healthy** - All backend/frontend targets show "UP" status
- [ ] **Grafana shows data** - Operations, Commands, Vehicles dashboards display metrics

### Scaling & Infrastructure Criteria

- [ ] **HPA scales 3→5 pods** - Load test triggers scale-up when CPU > 70%
- [ ] **Migration Job completed** - Job status "Completed 1/1" before deployment
- [ ] **Secrets synced from AWS** - ExternalSecret shows "Ready" status OR documented as not tested for local env
- [ ] **Rollback succeeds** - `helm rollback` completes without errors, app remains functional

### Testing Criteria

- [ ] **Smoke tests all pass** - All 8 smoke tests return PASS status (no fails)

### Documentation Criteria

- [ ] **deployment_test_report.md created** - File exists in `docs/runbooks/`
- [ ] **Test execution steps documented** - Each phase has commands, outputs, and results
- [ ] **Screenshots embedded** - Minimum 15 screenshots showing key steps (ideally 24)
- [ ] **Issues and resolutions documented** - Section filled with encountered problems and fixes
- [ ] **Performance metrics recorded** - Table with deployment time, pod startup, response times, etc.
- [ ] **Recommendations provided** - At least 3 recommendations based on test findings
- [ ] **Executive summary written** - High-level overview of test results and production readiness
- [ ] **No critical blockers** - All critical issues resolved, remaining issues documented as non-blocking

---

**Total Checklist Items**: 23
**Target**: 100% completion before marking task done

---

## 7. Quick Reference Commands

For easy copy-paste during testing:

```bash
# Build images
cd backend && docker build -f Dockerfile.prod -t sovd-backend:local . && cd ..
cd frontend && docker build -f Dockerfile.prod -t sovd-frontend:local . && cd ..

# Load images to minikube
minikube image load sovd-backend:local
minikube image load sovd-frontend:local

# Create namespace and secrets
kubectl create namespace staging
kubectl create secret generic sovd-webapp-secrets -n staging \
  --from-literal=database-url=postgresql://sovd_user:sovd_pass@192.168.49.2:5432/sovd \
  --from-literal=jwt-secret=$(openssl rand -base64 64 | tr -d '\n') \
  --from-literal=redis-url=redis://192.168.49.2:6379/0

# Deploy with Helm
cd infrastructure/helm
helm upgrade --install sovd-webapp ./sovd-webapp \
  -f values-local.yaml \
  -n staging \
  --create-namespace \
  --wait \
  --timeout 10m

# Monitor deployment
kubectl get pods -n staging --watch
kubectl get jobs -n staging
kubectl logs -n staging -f $(kubectl get pods -n staging -l app.kubernetes.io/component=migration -o name)

# Port-forward services
kubectl port-forward -n staging svc/sovd-webapp-backend 8000:8000 &
kubectl port-forward -n staging svc/sovd-webapp-frontend 3000:80 &
kubectl port-forward -n staging svc/prometheus 9090:9090 &
kubectl port-forward -n staging svc/grafana 3001:3000 &

# Health checks
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready

# Smoke tests
export API_BASE_URL=http://localhost:8000
export FRONTEND_BASE_URL=http://localhost:3000
./scripts/smoke_tests.sh

# HPA load test
kubectl run load-generator --image=busybox --restart=Never -n staging -- \
  /bin/sh -c "while true; do wget -q -O- http://sovd-webapp-backend:8000/api/v1/vehicles; done"
kubectl get hpa -n staging --watch

# Rollback
helm history sovd-webapp -n staging
helm rollback sovd-webapp -n staging

# Cleanup
helm uninstall sovd-webapp -n staging
kubectl delete namespace staging
```

---

**Good luck with the deployment test! This is the final task of Iteration 5 and the entire project - make it comprehensive and thorough! 🚀**
