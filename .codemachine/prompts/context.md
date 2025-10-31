# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T2",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Create Helm chart in infrastructure/helm/sovd-webapp/. Structure: Chart.yaml, values.yaml, values-production.yaml, templates/. Templates: backend/frontend/vehicle-connector deployments (3 replicas, health checks, resources), services, ingress (ALB with TLS), configmap, secrets, HPA (CPU 70%, 3-10 replicas). Configure resource requests/limits. Document in README.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.9; Kubernetes/Helm best practices.",
  "target_files": [
    "infrastructure/helm/sovd-webapp/Chart.yaml",
    "infrastructure/helm/sovd-webapp/values.yaml",
    "infrastructure/helm/sovd-webapp/values-production.yaml",
    "infrastructure/helm/sovd-webapp/templates/backend-deployment.yaml",
    "infrastructure/helm/sovd-webapp/templates/frontend-deployment.yaml",
    "infrastructure/helm/sovd-webapp/templates/vehicle-connector-deployment.yaml",
    "infrastructure/helm/sovd-webapp/templates/services.yaml",
    "infrastructure/helm/sovd-webapp/templates/ingress.yaml",
    "infrastructure/helm/sovd-webapp/templates/configmap.yaml",
    "infrastructure/helm/sovd-webapp/templates/secrets.yaml",
    "infrastructure/helm/sovd-webapp/templates/hpa.yaml",
    "infrastructure/helm/sovd-webapp/README.md"
  ],
  "input_files": [],
  "deliverables": "Complete Helm chart; production values; HPA; documentation.",
  "acceptance_criteria": "helm lint passes; helm template generates valid YAML; All resources present; 3 replicas, health checks, resources set; Ingress for ALB; HPA targets 70% CPU; ConfigMap/Secrets placeholders; README documents install/upgrade",
  "dependencies": ["I5.T1"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: production-deployment (from 05_Operational_Architecture.md)

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

### Context: task-i5-t2 (from 02_Iteration_I5.md)

```markdown
*   **Task 5.2: Create Kubernetes Helm Chart**
    *   **Task ID:** `I5.T2`
    *   **Description:** Create Helm chart for Kubernetes deployment in `infrastructure/helm/sovd-webapp/`. Chart structure: `Chart.yaml` (metadata), `values.yaml` (default values), `values-production.yaml` (production overrides), `templates/` directory with Kubernetes manifests. Templates to create: 1) `backend-deployment.yaml`: Deployment for backend (3 replicas, resource requests/limits, health checks using /health/live and /health/ready, environment variables from ConfigMap and Secrets), 2) `frontend-deployment.yaml`: Deployment for frontend (3 replicas, Nginx container), 3) `vehicle-connector-deployment.yaml`: Deployment for vehicle connector (2 replicas, can be same image as backend with different entrypoint or CMD), 4) `services.yaml`: ClusterIP Services for backend, frontend, vehicle-connector, 5) `ingress.yaml`: Ingress for ALB (AWS Application Load Balancer) with TLS termination, routes for frontend (/) and backend (/api/*), 6) `configmap.yaml`: ConfigMap for non-sensitive config (database host, Redis host, log level), 7) `secrets.yaml`: placeholder for Secrets (database password, JWT secret, Redis password) - note: use External Secrets Operator in real deployment, 8) `hpa.yaml`: HorizontalPodAutoscaler for backend (target CPU 70%, min 3, max 10 replicas). Configure resource requests/limits: backend (requests: 256Mi memory, 250m CPU; limits: 512Mi, 500m), frontend (requests: 64Mi, 100m; limits: 128Mi, 200m). Document Helm chart usage in `infrastructure/helm/sovd-webapp/README.md`.
    *   **Acceptance Criteria:**
        *   `helm lint infrastructure/helm/sovd-webapp` passes without errors
        *   `helm template sovd-webapp infrastructure/helm/sovd-webapp` generates valid Kubernetes YAML
        *   Generated manifests include all specified resources (Deployments, Services, Ingress, ConfigMap, Secrets, HPA)
        *   Backend deployment has 3 replicas, health checks configured, resource limits set
        *   Ingress configured for ALB with annotations (AWS-specific: `alb.ingress.kubernetes.io/*`)
        *   HPA targets CPU utilization 70%, scales backend from 3 to 10 replicas
        *   ConfigMap includes: DATABASE_HOST, REDIS_HOST, LOG_LEVEL
        *   Secrets template includes placeholders for: DATABASE_PASSWORD, JWT_SECRET, REDIS_PASSWORD
        *   `values-production.yaml` overrides: image tags (use specific version, not `latest`), resource limits (higher than defaults), ingress host (production domain)
        *   README documents: installation (`helm install`), upgrade (`helm upgrade`), configuration options
```

### Context: horizontal-scaling (from 05_Operational_Architecture.md)

```markdown
**Horizontal Scaling Strategy**

The architecture is designed for horizontal scalability to handle increased load without modifying the application code.

**Stateless Application Design:**
- Backend (FastAPI) and Frontend (React SPA) are stateless and can scale horizontally by adding more pod replicas
- Session state stored externally in Redis (not in-memory within application)
- No sticky sessions required for load balancing

**Kubernetes Horizontal Pod Autoscaler (HPA):**
- **Backend HPA Configuration:**
  - Target Metric: Average CPU Utilization
  - Target Value: 70%
  - Min Replicas: 3 (high availability baseline)
  - Max Replicas: 10 (cost-controlled scaling limit)
  - Scaling Behavior: Scale up aggressively (add 2 replicas per interval), scale down conservatively (remove 1 replica per interval with 5-minute stabilization window)

- **Frontend HPA Configuration:**
  - Target Metric: Average CPU Utilization
  - Target Value: 70%
  - Min Replicas: 2
  - Max Replicas: 5
  - Rationale: Frontend is lightweight; typically constrained by backend capacity

**Load Balancer Configuration:**
- AWS Application Load Balancer (ALB) distributes traffic across backend replicas
- Health checks use `/health/ready` endpoint to ensure only healthy pods receive traffic
- Connection draining enabled (30 seconds) for graceful pod termination

**Database Scaling:**
- Vertical scaling for PostgreSQL RDS (upgrade instance class when needed)
- Read replicas can be added for read-heavy workloads (future enhancement)
- Connection pooling in application (SQLAlchemy pool_size=20) prevents connection exhaustion

**Redis Scaling:**
- ElastiCache cluster mode enables horizontal scaling by adding shards
- Replication group provides high availability (primary + replicas)
```

### Context: deployment-strategy (from docs/runbooks/deployment.md)

```markdown
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
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

*   **File:** `backend/Dockerfile.prod`
    *   **Summary:** This is the production Docker image for the backend FastAPI application. It uses multi-stage builds with Python 3.11, installs production dependencies, runs as non-root user (appuser, UID 1001), exposes port 8000, and includes a health check on `/health/ready`.
    *   **Recommendation:** You MUST reference this Dockerfile in your Helm chart backend deployment. The image should be built from this file and tagged appropriately. Note that it uses 4 workers with uvicorn, listens on port 8000, and has health check configured.
    *   **Port Configuration:** Backend listens on port 8000 inside the container.
    *   **Health Check Configuration:** The Dockerfile uses `/health/ready` for health checks with 30s interval, 10s timeout, 40s start period, and 3 retries.

*   **File:** `frontend/Dockerfile.prod`
    *   **Summary:** This is the production Docker image for the frontend React application. It uses multi-stage builds (Node 20 builder + nginx:alpine runtime), serves static files from `/usr/share/nginx/html`, exposes port 80, and runs as nginx user (UID 101).
    *   **Recommendation:** You MUST reference this Dockerfile in your Helm chart frontend deployment. The nginx configuration is copied from `frontend/nginx.conf` which includes API proxying to the backend service.
    *   **Port Configuration:** Frontend Nginx listens on port 80 inside the container.
    *   **Health Check:** Simple nc check on port 80 with 30s interval.

*   **File:** `infrastructure/docker/nginx.conf`
    *   **Summary:** This is the Nginx configuration for the frontend that includes gzip compression, security headers, SPA routing, and critical proxy configurations for `/api/` and `/ws/` endpoints.
    *   **Recommendation:** Note that the nginx.conf proxies `/api/` requests to `http://backend:8000` and `/ws/` to the same backend for WebSocket support. In your Helm chart, the Service for backend MUST be named `backend` (or update nginx.conf accordingly), and it must expose port 8000.
    *   **WebSocket Support:** The nginx.conf includes special WebSocket upgrade headers for `/ws/` location with 7-day timeouts.
    *   **Important:** The proxy_pass uses service name `backend:8000`, so your backend Service name in Kubernetes MUST be `backend`.

*   **File:** `backend/app/config.py`
    *   **Summary:** This file defines the application configuration using Pydantic Settings. It loads the following environment variables: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM` (default HS256), `JWT_EXPIRATION_MINUTES` (default 15), `LOG_LEVEL` (default INFO), `CORS_ORIGINS` (default localhost:3000).
    *   **Recommendation:** Your ConfigMap MUST include these configuration keys (non-sensitive ones like LOG_LEVEL, CORS_ORIGINS), and your Secrets MUST include the sensitive ones (JWT_SECRET, database password, Redis password). You should construct DATABASE_URL and REDIS_URL from these components in the deployment environment variables.
    *   **Environment Variables Structure:**
        - DATABASE_URL format: `postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd`
        - REDIS_URL format: `redis://redis:6379/0`
        - In Kubernetes, replace `db` with RDS endpoint and `redis` with ElastiCache endpoint.

*   **File:** `docker-compose.yml`
    *   **Summary:** This shows the development environment setup with all services. It includes PostgreSQL (port 5432), Redis (port 6379), backend (port 8000), frontend (port 3000), Prometheus (port 9090), and Grafana (port 3001).
    *   **Recommendation:** Use this as a reference for service dependencies and configurations. The backend depends on both db and redis with health check conditions. Your Kubernetes deployment should reflect these dependencies using init containers or readiness probes.
    *   **Service Names:** In docker-compose, services are named: `db`, `redis`, `backend`, `frontend`, `prometheus`, `grafana`. In Kubernetes, you'll need Services with similar names for internal communication.

### Implementation Tips & Notes

*   **Tip:** The production Dockerfiles (I5.T1) are already created and working. You SHOULD use image references like `{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}` in your deployment templates and define these in values.yaml.

*   **Tip:** For AWS ALB Ingress, you MUST use specific annotations. The essential ones are:
    - `kubernetes.io/ingress.class: alb` (or use ingressClassName: alb in newer versions)
    - `alb.ingress.kubernetes.io/scheme: internet-facing`
    - `alb.ingress.kubernetes.io/target-type: ip` (for EKS with VPC CNI)
    - `alb.ingress.kubernetes.io/listen-ports: '[{"HTTP": 80}, {"HTTPS": 443}]'`
    - `alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:...` (for TLS)
    - `alb.ingress.kubernetes.io/ssl-redirect: '443'` (redirect HTTP to HTTPS)

*   **Note:** The backend has both liveness (`/health/live`) and readiness (`/health/ready`) endpoints implemented in `backend/app/api/health.py`. Your deployment SHOULD use:
    - `livenessProbe` → `/health/live` (checks if container is alive)
    - `readinessProbe` → `/health/ready` (checks if container can serve traffic, includes DB and Redis checks)
    - Use appropriate initialDelaySeconds (30-40s for backend), periodSeconds (10s), timeoutSeconds (5s), failureThreshold (3)

*   **Tip:** For the HPA (HorizontalPodAutoscaler), target the backend deployment with `apiVersion: autoscaling/v2` (or v2beta2). Specify:
    - `scaleTargetRef` pointing to backend deployment
    - `minReplicas: 3`, `maxReplicas: 10`
    - `metrics` with `type: Resource`, `resource.name: cpu`, `target.type: Utilization`, `target.averageUtilization: 70`
    - Include `behavior` section for controlled scale-down (e.g., stabilizationWindowSeconds: 300)

*   **Note:** The architecture blueprint specifies vehicle-connector as a separate deployment (2 replicas). However, this component hasn't been fully implemented yet as a standalone service. For now, you can create the deployment template using the same backend image but with a different command/args that would be configured when the gRPC vehicle connector is implemented (that's task I5.T6). Use a placeholder in values.yaml like `vehicleConnector.enabled: false` to allow disabling it initially.

*   **Warning:** For the ConfigMap, DO NOT hardcode database credentials or JWT secrets. Only include non-sensitive configuration like:
    - `LOG_LEVEL: INFO`
    - `CORS_ORIGINS: https://your-domain.com`
    - Database and Redis hosts/ports (not passwords)
    - Environment-specific settings

*   **Tip:** For the Secrets template, create placeholder base64-encoded values that will be replaced by External Secrets Operator in real deployments. Document in comments that these are placeholders and should not be used in production. Example structure:
    ```yaml
    apiVersion: v1
    kind: Secret
    metadata:
      name: sovd-secrets
    type: Opaque
    data:
      database-password: cGxhY2Vob2xkZXI=  # placeholder - use External Secrets Operator in production
      jwt-secret: cGxhY2Vob2xkZXI=  # placeholder
      redis-password: ""  # Redis may not require password in some setups
    ```

*   **Tip:** In your values.yaml, structure the configuration hierarchically:
    ```yaml
    global:
      namespace: production
      domain: sovd.example.com

    backend:
      replicaCount: 3
      image:
        repository: YOUR_ECR_REGISTRY/sovd-backend
        tag: latest  # Override in production with specific SHA
      resources:
        requests:
          memory: "256Mi"
          cpu: "250m"
        limits:
          memory: "512Mi"
          cpu: "500m"

    frontend:
      replicaCount: 3
      image:
        repository: YOUR_ECR_REGISTRY/sovd-frontend
        tag: latest
      resources:
        requests:
          memory: "64Mi"
          cpu: "100m"
        limits:
          memory: "128Mi"
          cpu: "200m"

    hpa:
      enabled: true
      minReplicas: 3
      maxReplicas: 10
      targetCPUUtilizationPercentage: 70

    ingress:
      enabled: true
      className: alb
      annotations:
        alb.ingress.kubernetes.io/scheme: internet-facing
      hosts:
        - host: sovd.example.com
      tls:
        - secretName: sovd-tls
          hosts:
            - sovd.example.com
    ```

*   **Tip:** Your values-production.yaml should override only production-specific values:
    ```yaml
    backend:
      image:
        tag: "v1.0.0"  # Specific version, not latest
      replicaCount: 5  # More replicas in production
      resources:
        requests:
          memory: "512Mi"  # Higher than default
          cpu: "500m"

    frontend:
      image:
        tag: "v1.0.0"

    ingress:
      hosts:
        - host: sovd.production.com  # Production domain
      annotations:
        alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:us-east-1:123456789:certificate/abc123
        alb.ingress.kubernetes.io/ssl-redirect: '443'
    ```

*   **Note:** The Chart.yaml should follow Helm v3 format:
    ```yaml
    apiVersion: v2
    name: sovd-webapp
    description: A Helm chart for SOVD Command WebApp
    type: application
    version: 1.0.0  # Chart version
    appVersion: "1.0.0"  # Application version
    keywords:
      - sovd
      - automotive
      - vehicle-diagnostics
    maintainers:
      - name: SOVD Team
    ```

*   **Tip:** For the Services template, you'll need three services:
    1. **backend-service**: ClusterIP, port 8000, selector matches backend deployment
    2. **frontend-service**: ClusterIP, port 80, selector matches frontend deployment (this is what ALB Ingress will target)
    3. **vehicle-connector-service**: ClusterIP, port 50051 (gRPC), selector matches vehicle-connector deployment

*   **Important:** Remember that the nginx.conf in the frontend expects to proxy to a service named `backend`. So your backend Service MUST be named `backend`, or you need to update the nginx configuration. Since the nginx.conf is baked into the frontend Docker image, it's easier to name the Service `backend` to match.

*   **Tip:** Use Helm template functions for flexibility:
    - `{{ include "sovd-webapp.fullname" . }}` for resource names
    - `{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag | default .Chart.AppVersion }}` for images
    - `{{ .Release.Namespace }}` for namespace
    - Define helper templates in `_helpers.tpl` for common labels and selectors

*   **Tip:** For health checks in deployments, use this pattern:
    ```yaml
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8000
      initialDelaySeconds: 40
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3

    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    ```

*   **Note:** Create a comprehensive README.md in the helm chart directory that documents:
    - Chart overview and purpose
    - Prerequisites (kubectl, helm, AWS credentials)
    - Installation instructions with examples
    - Configuration options (all values.yaml parameters)
    - Upgrade and rollback procedures
    - Troubleshooting common issues
    - Links to architecture documentation

### Deployment Strategy Notes

*   The deployment runbook (docs/runbooks/deployment.md) shows that production deployments use rolling updates with `maxSurge: 1` and `maxUnavailable: 0` to ensure zero-downtime deployments. Your deployment templates should include this strategy configuration.

*   The architecture specifies a 3-node EKS cluster across 3 AZs. Consider adding pod anti-affinity rules to spread replicas across different nodes/AZs for high availability.

*   Resource requests are critical for HPA to work correctly. The HPA scales based on actual CPU usage vs requested CPU, so requests must be realistic (not too low, not too high).
