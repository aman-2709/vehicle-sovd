# Deployment Runbook

This runbook provides step-by-step deployment procedures for the SOVD Web Application across all environments: local development, staging, and production.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Local Development Deployment](#local-development-deployment)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Rollback Procedures](#rollback-procedures)
- [Post-Deployment Verification](#post-deployment-verification)

---

## Prerequisites

### General Requirements
- Docker and Docker Compose installed (v20.10+)
- Git access to the repository
- Access to AWS credentials (for staging/production)
- kubectl configured (for Kubernetes deployments)
- Helm 3 installed (for staging/production)

### Access Requirements
- **Local**: None (runs on localhost)
- **Staging**: AWS credentials with EKS access, `staging` namespace permissions
- **Production**: AWS credentials with EKS access, `production` namespace permissions, approval rights

---

## Local Development Deployment

Local deployment uses Docker Compose to run all services on your development machine.

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd sovd
```

**Verification**: Confirm you're in the project root:
```bash
ls -la
# Should see: docker-compose.yml, Makefile, backend/, frontend/, etc.
```

### Step 2: Configure Environment Variables

Create a `.env` file in the project root (if not already present):

```bash
# Database Configuration
DATABASE_URL=postgresql://sovd_user:sovd_password@db:5432/sovd_db
POSTGRES_USER=sovd_user
POSTGRES_PASSWORD=sovd_password
POSTGRES_DB=sovd_db

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO

# API Configuration
API_V1_PREFIX=/api/v1
```

**Important**: For local development, these values match `docker-compose.yml` defaults. Never commit `.env` to version control.

**Verification**: Check the file exists:
```bash
cat .env
```

### Step 3: Start All Services

Use the Makefile for convenience:

```bash
make up
```

Or use Docker Compose directly:
```bash
docker-compose up -d
```

This command starts 6 services:
1. **PostgreSQL** (port 5432)
2. **Redis** (port 6379)
3. **Backend API** (port 8000)
4. **Frontend** (port 5173)
5. **Prometheus** (port 9090)
6. **Grafana** (port 3001)

**Verification**: Check all containers are running:
```bash
docker-compose ps
# All services should show "Up" status
```

### Step 4: Initialize the Database

Run the database initialization script:

```bash
docker-compose exec backend /bin/bash -c "cd /app && bash /app/scripts/init_db.sh"
```

This creates tables, indexes, and inserts seed data:
- **Users**:
  - Admin: `admin` / `admin123` (role: admin)
  - Engineer: `engineer` / `engineer123` (role: engineer)
- **Vehicles**:
  - Vehicle 1: VIN `WDD1234567890ABCD` (IP: 192.168.1.10)
  - Vehicle 2: VIN `WDD0987654321ZYXW` (IP: 192.168.1.11)

**Verification**: Check database initialization:
```bash
docker-compose logs backend | grep "Database initialized"
```

### Step 5: Access the Application

Open your browser and navigate to:

- **Frontend UI**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health/ready
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin)

**Verification**:
1. Frontend loads without errors
2. Backend API docs are accessible
3. Health check returns `{"status": "healthy", "database": "connected", "redis": "connected"}`

### Step 6: Log In to the Application

1. Navigate to http://localhost:5173
2. Log in with:
   - Username: `admin`
   - Password: `admin123`
3. You should see the dashboard with navigation to Vehicles and Commands

**Verification**: After login, you should see a JWT token stored in localStorage and the user's role displayed.

### Common Local Deployment Issues

**Issue**: Port conflicts (e.g., "port 5432 already allocated")
- **Solution**: Check for existing services: `lsof -i :5432` and stop them, or change ports in `docker-compose.yml`

**Issue**: Database connection errors
- **Solution**: Ensure the database service is healthy: `docker-compose ps db`. Check logs: `make logs db`

**Issue**: Frontend can't reach backend
- **Solution**: Verify backend is listening: `curl http://localhost:8000/health/live`. Check `VITE_API_BASE_URL` in frontend/.env

---

## Staging Deployment

Staging deployment uses Kubernetes (AWS EKS) with Helm charts. The staging environment mirrors production but with reduced resources.

### Prerequisites
- AWS CLI configured: `aws configure`
- kubectl configured for staging cluster: `aws eks update-kubeconfig --region us-east-1 --name sovd-staging-cluster`
- Helm 3 installed
- Docker images pushed to ECR

### Step 1: Authenticate to AWS ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

**Verification**: Login should succeed with "Login Succeeded" message.

### Step 2: Build and Push Docker Images

Build frontend and backend images:

```bash
# Backend
cd backend
docker build -t sovd-backend:${COMMIT_SHA} .
docker tag sovd-backend:${COMMIT_SHA} <ecr-repo>/sovd-backend:${COMMIT_SHA}
docker tag sovd-backend:${COMMIT_SHA} <ecr-repo>/sovd-backend:latest
docker push <ecr-repo>/sovd-backend:${COMMIT_SHA}
docker push <ecr-repo>/sovd-backend:latest

# Frontend
cd ../frontend
docker build -t sovd-frontend:${COMMIT_SHA} .
docker tag sovd-frontend:${COMMIT_SHA} <ecr-repo>/sovd-frontend:${COMMIT_SHA}
docker tag sovd-frontend:${COMMIT_SHA} <ecr-repo>/sovd-frontend:latest
docker push <ecr-repo>/sovd-frontend:${COMMIT_SHA}
docker push <ecr-repo>/sovd-frontend:latest
```

**Verification**: Check images are in ECR:
```bash
aws ecr list-images --repository-name sovd-backend --region us-east-1
aws ecr list-images --repository-name sovd-frontend --region us-east-1
```

### Step 3: Configure Secrets

Staging secrets are stored in AWS Secrets Manager and synced to Kubernetes via External Secrets Operator.

Ensure the following secrets exist:
- `staging/sovd/database` (contains DATABASE_URL)
- `staging/sovd/redis` (contains REDIS_URL)
- `staging/sovd/jwt` (contains JWT_SECRET_KEY)

**Verification**: Check secrets are synced:
```bash
kubectl get secrets -n staging | grep sovd
```

### Step 4: Deploy with Helm

Navigate to the Helm chart directory:

```bash
cd sovd-helm-chart
```

Deploy or upgrade the release:

```bash
helm upgrade --install sovd-webapp . \
  -f values-staging.yaml \
  -n staging \
  --set backend.image.tag=${COMMIT_SHA} \
  --set frontend.image.tag=${COMMIT_SHA} \
  --wait \
  --timeout 5m
```

**Verification**: Check all pods are running:
```bash
kubectl get pods -n staging
# All pods should be in "Running" state with 1/1 ready
```

### Step 5: Verify Deployment

Check the health endpoints:

```bash
# Get the ALB URL
ALB_URL=$(kubectl get ingress sovd-ingress -n staging -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

# Test health endpoints
curl http://${ALB_URL}/health/ready
curl http://${ALB_URL}/api/v1/health
```

**Expected Response**:
```json
{"status": "healthy", "database": "connected", "redis": "connected"}
```

### Step 6: Run Smoke Tests

Execute automated smoke tests:

```bash
# From project root
export API_BASE_URL=http://${ALB_URL}
pytest tests/smoke/ -v
```

**Verification**: All smoke tests should pass. If any fail, investigate before proceeding.

---

## Production Deployment

Production deployment follows the same Helm-based process as staging but includes additional safeguards and a blue-green deployment strategy.

### Prerequisites
- All staging smoke tests passed
- Change ticket approved (for tracking)
- Rollback plan prepared
- On-call engineer available

### Step 1: Pre-Deployment Checklist

- [ ] Staging deployment successful
- [ ] Smoke tests passed in staging
- [ ] Database migrations tested (if any)
- [ ] Rollback procedure reviewed
- [ ] Monitoring dashboards open (Grafana)
- [ ] On-call engineer notified

### Step 2: Authenticate to Production

```bash
aws eks update-kubeconfig --region us-east-1 --name sovd-production-cluster
```

**Verification**: Check you're in the production context:
```bash
kubectl config current-context
# Should show production cluster
```

### Step 3: Deploy with Gradual Rollout

Production uses a gradual rollout strategy (10% → 50% → 100%) with automatic rollback on errors.

```bash
cd sovd-helm-chart

# Deploy with gradual rollout
helm upgrade --install sovd-webapp . \
  -f values-production.yaml \
  -n production \
  --set backend.image.tag=${COMMIT_SHA} \
  --set frontend.image.tag=${COMMIT_SHA} \
  --set deployment.strategy.type=RollingUpdate \
  --set deployment.strategy.rollingUpdate.maxSurge=1 \
  --set deployment.strategy.rollingUpdate.maxUnavailable=0 \
  --wait \
  --timeout 10m
```

### Step 4: Monitor Deployment Progress

Watch the rollout in real-time:

```bash
# Watch pods being updated
kubectl rollout status deployment/backend-deployment -n production
kubectl rollout status deployment/frontend-deployment -n production

# Monitor error rates in Prometheus
# Navigate to Grafana: http://<grafana-url>
# Check "Operations Dashboard" for error rate spikes
```

**Success Criteria**:
- All pods transition to "Running" state
- Error rate remains <1%
- P95 latency remains <3s
- No increase in 5xx responses

### Step 5: Post-Deployment Verification

Run production smoke tests:

```bash
export API_BASE_URL=https://sovd.yourdomain.com
pytest tests/smoke/ -v --production
```

**Verification**:
- Smoke tests pass
- Health endpoints return 200
- Login functionality works
- Command submission works

### Step 6: Monitor for 30 Minutes

Keep monitoring dashboards open for 30 minutes post-deployment:

1. **Grafana Operations Dashboard**: Watch error rates, latency, throughput
2. **CloudWatch Logs**: Check for unexpected errors
3. **AWS RDS Metrics**: Ensure database performance is stable
4. **ElastiCache Metrics**: Verify Redis latency is normal

**If issues arise**: Proceed to [Rollback Procedures](#rollback-procedures)

---

## Rollback Procedures

### When to Rollback

Rollback immediately if:
- Error rate >5%
- P95 latency >5s (sustained)
- Database connection failures
- Critical functionality broken (auth, command submission)

### Rollback Steps

#### Kubernetes Rollback (Staging/Production)

```bash
# Rollback to previous revision
kubectl rollout undo deployment/backend-deployment -n <namespace>
kubectl rollout undo deployment/frontend-deployment -n <namespace>

# Or rollback to specific revision
kubectl rollout history deployment/backend-deployment -n <namespace>
kubectl rollout undo deployment/backend-deployment --to-revision=<revision-number> -n <namespace>
```

**Verification**: Check pods are running the old version:
```bash
kubectl get pods -n <namespace> -o jsonpath='{.items[*].spec.containers[0].image}'
```

#### Helm Rollback

```bash
# List release history
helm history sovd-webapp -n <namespace>

# Rollback to previous release
helm rollback sovd-webapp -n <namespace>

# Or rollback to specific revision
helm rollback sovd-webapp <revision-number> -n <namespace>
```

**Verification**: Check release status:
```bash
helm status sovd-webapp -n <namespace>
```

#### Local Rollback

```bash
# Stop all services
make down

# Checkout previous version
git checkout <previous-commit>

# Restart services
make up
```

### Post-Rollback Actions

1. Verify application is functional
2. Document the incident (what failed, why, impact)
3. Create tickets for fixes
4. Schedule post-mortem meeting

---

## Post-Deployment Verification

Use this checklist after every deployment to ensure everything is working correctly.

### Health Checks

```bash
# Backend health
curl http://<url>/health/ready
# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}

# API documentation
curl http://<url>/docs
# Expected: 200 OK with OpenAPI docs
```

### Functional Tests

1. **Authentication**:
   - Log in with admin credentials
   - Verify JWT token is returned
   - Access protected endpoint

2. **Vehicle Management**:
   - List vehicles: `GET /api/v1/vehicles`
   - Get vehicle details: `GET /api/v1/vehicles/{id}`

3. **Command Execution**:
   - Submit command: `POST /api/v1/commands`
   - Verify command status: `GET /api/v1/commands/{id}`
   - Check command history: `GET /api/v1/commands/history`

4. **WebSocket Connection**:
   - Connect to `/ws/commands`
   - Verify real-time updates

### Monitoring Verification

1. **Prometheus Targets**:
   - Navigate to http://<prometheus-url>/targets
   - Verify all targets are "UP"

2. **Grafana Dashboards**:
   - Open http://<grafana-url>
   - Check "Operations Dashboard" for healthy metrics
   - Verify "Commands Dashboard" shows recent activity

3. **Logs**:
   ```bash
   # Check recent logs for errors
   kubectl logs -n <namespace> -l app=backend --tail=100 | grep ERROR
   ```

### Database Verification

```bash
# Connect to database
kubectl exec -it -n <namespace> <backend-pod> -- psql $DATABASE_URL

# Check recent commands
SELECT COUNT(*) FROM commands WHERE created_at > NOW() - INTERVAL '5 minutes';

# Check audit logs
SELECT COUNT(*) FROM audit_logs WHERE timestamp > NOW() - INTERVAL '5 minutes';

# Exit
\q
```

---

## Deployment Schedule

### Recommended Deployment Windows

- **Local**: Anytime (no restrictions)
- **Staging**: Anytime during business hours (9 AM - 5 PM)
- **Production**: Tuesday or Thursday, 10 AM - 2 PM (avoid Mondays and Fridays)

### Deployment Frequency

- **Staging**: Multiple times per day (as needed)
- **Production**: 1-2 times per week (scheduled releases)

---

## Troubleshooting

For deployment-related issues, refer to:
- [Troubleshooting Runbook](troubleshooting.md)
- [Monitoring Guide](monitoring.md)

For disaster recovery scenarios, see:
- [Disaster Recovery Runbook](disaster_recovery.md)

---

## Contact & Escalation

- **DevOps Team**: devops@yourdomain.com
- **On-Call Engineer**: PagerDuty escalation
- **Slack Channel**: #sovd-deployments

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Owner**: DevOps Team
