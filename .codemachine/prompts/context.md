# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T7",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Create infrastructure provisioning scripts. Option 1 (Terraform - preferred): modules for VPC, EKS, RDS, ElastiCache, ALB, Route53, S3, IAM. Option 2: CloudFormation or AWS CLI scripts. Document in infrastructure_setup.md: prerequisites, provisioning steps, verification, teardown, cost estimates ($500-800/month). Optional for MVP; can use existing cluster.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.9, 3.8.",
  "target_files": [
    "infrastructure/terraform/main.tf",
    "infrastructure/terraform/variables.tf",
    "infrastructure/terraform/outputs.tf",
    "infrastructure/terraform/modules/vpc/main.tf",
    "infrastructure/terraform/modules/eks/main.tf",
    "infrastructure/terraform/modules/rds/main.tf",
    "docs/runbooks/infrastructure_setup.md"
  ],
  "input_files": [],
  "deliverables": "Infrastructure as Code; provisioning documentation; cost estimates.",
  "acceptance_criteria": "If Terraform: plan shows all resources; apply provisions VPC (3 public+3 private subnets, AZs), EKS (3 nodes, t3.large), RDS Multi-AZ, ElastiCache, ALB (HTTPS); infrastructure_setup.md: prerequisites, steps, verification, teardown; Cost ~$500-800/month documented; Alternative: manual setup steps detailed",
  "dependencies": ["I5.T2"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Deployment Architecture (from docs/runbooks/deployment.md)

```markdown
## Production Deployment

Production deployment uses Kubernetes (AWS EKS) with Helm charts.

### Prerequisites
- AWS CLI configured: `aws configure`
- kubectl configured for staging cluster: `aws eks update-kubeconfig --region us-east-1 --name sovd-staging-cluster`
- Helm 3 installed
- Docker images pushed to ECR

Key Infrastructure Components:
- **AWS EKS Cluster**: Kubernetes cluster named `sovd-production-cluster` in `us-east-1`
- **ECR**: Docker image registry for backend and frontend images
- **RDS**: PostgreSQL database (Multi-AZ for production)
  - Production endpoint: `sovd-production.c9akciq32.us-east-1.rds.amazonaws.com`
  - Database name: `sovd_production`
  - User: `sovd_admin`
- **ElastiCache**: Redis cache
  - Production endpoint: `sovd-production.abc123.ng.0001.use1.cache.amazonaws.com`
- **AWS ALB**: Application Load Balancer via Ingress Controller
  - TLS termination with ACM certificate
- **AWS Secrets Manager**: For database credentials, JWT secrets, Redis passwords
- **External Secrets Operator**: Syncs secrets from AWS to Kubernetes

Production Configuration:
- Backend replicas: 5
- Frontend replicas: 3
- HPA: Backend scales from 5 to 20 pods based on 70% CPU
- Instance types: t3.large worker nodes
- Multi-AZ deployment for high availability
```

### Context: Production Helm Values (from infrastructure/helm/sovd-webapp/values-production.yaml)

```yaml
global:
  namespace: production
  domain: sovd.production.com

backend:
  replicaCount: 5
  image:
    repository: 123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-backend
  resources:
    requests:
      memory: "512Mi"
      cpu: "500m"
    limits:
      memory: "1Gi"
      cpu: "1000m"

config:
  database:
    host: "sovd-production.c9akciq32.us-east-1.rds.amazonaws.com"
    port: "5432"
    name: "sovd_production"
    user: "sovd_admin"

  redis:
    host: "sovd-production.abc123.ng.0001.use1.cache.amazonaws.com"
    port: "6379"

ingress:
  enabled: true
  className: "alb"
  annotations:
    alb.ingress.kubernetes.io/certificate-arn: "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id"
    alb.ingress.kubernetes.io/ssl-redirect: "443"

serviceAccount:
  create: true
  annotations:
    eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/sovd-webapp-production"
  name: "sovd-webapp-production-sa"
```

### Context: Application Configuration (from backend/app/config.py)

```python
class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    DATABASE_URL: str

    # Redis configuration
    REDIS_URL: str

    # JWT authentication configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15

    # gRPC vehicle communication configuration
    VEHICLE_ENDPOINT_URL: str = "localhost:50051"
    VEHICLE_USE_TLS: bool = False
    VEHICLE_GRPC_TIMEOUT: int = 30
```

### Context: Project Technology Stack (from README.md)

```markdown
## Technology Stack

### Infrastructure
- **Database:** PostgreSQL 15+
- **Cache/Messaging:** Redis 7
- **Vehicle Communication:** gRPC (primary), WebSocket (fallback)
- **API Gateway:** Nginx (production)
- **Containerization:** Docker, Docker Compose (local), Kubernetes/Helm (production)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana, structlog
- **Tracing:** OpenTelemetry + Jaeger

### Cloud Platform
- **Primary:** AWS (EKS, RDS, ElastiCache, ALB, Route53, S3, Secrets Manager)
- **Region:** us-east-1
- **Multi-AZ:** Production deployments use 3 Availability Zones
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **Directory:** `infrastructure/terraform/`
    *   **Summary:** This directory currently exists but is **empty**. You will be creating all Terraform infrastructure code from scratch.
    *   **Recommendation:** You MUST create a modular Terraform structure with separate modules for each major AWS service (VPC, EKS, RDS, ElastiCache, etc.).

*   **Directory:** `infrastructure/helm/sovd-webapp/`
    *   **Summary:** Complete Helm chart already exists with deployments, services, ingress, HPA, and ConfigMaps/Secrets.
    *   **Files Present:**
        - `Chart.yaml` - Helm chart metadata
        - `values.yaml` - Default values for local/dev
        - `values-production.yaml` - Production-specific overrides with real AWS resource references
        - `templates/backend-deployment.yaml` - Backend deployment with 5 replicas in production
        - `templates/frontend-deployment.yaml` - Frontend deployment with 3 replicas
        - `templates/ingress.yaml` - AWS ALB Ingress configuration with TLS
        - `templates/hpa.yaml` - Horizontal Pod Autoscaler (5-20 backend pods, 3-8 frontend pods)
        - `templates/configmap.yaml` - Non-sensitive configuration
        - `templates/secrets.yaml` - Secrets (should use External Secrets Operator in production)
    *   **Recommendation:** Your Terraform code MUST provision infrastructure that matches the expectations in `values-production.yaml`. Key mappings:
        - RDS endpoint → `config.database.host` value
        - ElastiCache endpoint → `config.redis.host` value
        - ACM certificate ARN → `ingress.annotations.alb.ingress.kubernetes.io/certificate-arn`
        - IAM role ARN → `serviceAccount.annotations.eks.amazonaws.com/role-arn`

*   **File:** `docs/runbooks/deployment.md`
    *   **Summary:** Comprehensive deployment runbook documenting local, staging, and production deployment procedures. Contains specific AWS resource references.
    *   **Key Information Extracted:**
        - Cluster naming: `sovd-staging-cluster`, `sovd-production-cluster`
        - ECR repository naming: `sovd-backend`, `sovd-frontend`
        - AWS region: `us-east-1`
        - Database configuration: PostgreSQL, Multi-AZ, database name `sovd_production`
        - ElastiCache configuration: Redis 7
        - Secrets in AWS Secrets Manager: `sovd/production/database`, `sovd/production/jwt`, `sovd/production/redis`
    *   **Recommendation:** Your infrastructure_setup.md documentation SHOULD reference and be consistent with the deployment runbook. The Terraform outputs should generate values that can be directly copied into the Helm values file.

*   **File:** `backend/app/config.py`
    *   **Summary:** Application configuration showing all required environment variables and connection settings.
    *   **Recommendation:** Your Terraform RDS module MUST output a connection string in the format expected by `DATABASE_URL` (PostgreSQL connection string). Similarly, ElastiCache must output Redis URL format expected by `REDIS_URL`.

*   **File:** `infrastructure/helm/sovd-webapp/README.md`
    *   **Summary:** Helm chart documentation with detailed installation, upgrade, and troubleshooting guidance.
    *   **Key Requirements:**
        - ECR image pull secrets required
        - External Secrets Operator integration for production secrets
        - AWS ALB Ingress Controller must be installed
        - Metrics server required for HPA
    *   **Recommendation:** Your Terraform EKS module SHOULD provision the cluster with necessary add-ons (AWS ALB Ingress Controller, External Secrets Operator, Metrics Server) OR document manual installation steps in infrastructure_setup.md.

### Implementation Tips & Notes

*   **Tip:** The task description marks this as **"Optional for MVP; can use existing cluster"**. This means you have two valid approaches:
    1. **Full Terraform (Preferred):** Create complete Terraform modules for all infrastructure from scratch
    2. **Hybrid/Documentation:** Document how to use an existing EKS cluster and only provision RDS, ElastiCache, and supporting resources with Terraform

    **Recommendation:** I suggest the hybrid approach as more practical for this task, focusing Terraform on stateful resources (RDS, ElastiCache, S3, Secrets Manager) and documenting EKS cluster prerequisites.

*   **Note:** The `values-production.yaml` file contains **placeholder AWS account IDs** (`123456789012`). Your Terraform code should use variables for the AWS account ID and output the real ARNs/endpoints that need to be updated in this file.

*   **Warning:** Cost estimation is a **critical acceptance criterion**. You MUST document estimated monthly costs for:
    - EKS cluster (control plane: ~$75/month, 3x t3.large workers: ~$270/month)
    - RDS Multi-AZ PostgreSQL (db.t3.large or similar: ~$200/month)
    - ElastiCache Redis (cache.t3.medium: ~$80/month)
    - ALB (~$25/month + data transfer)
    - Total: $500-800/month range as specified

*   **Tip:** The existing Helm chart expects **External Secrets Operator** for production secrets management. Your infrastructure_setup.md SHOULD include:
    1. How to install External Secrets Operator on the cluster
    2. How to create secrets in AWS Secrets Manager (naming: `sovd/production/database`, etc.)
    3. How to configure SecretStore and ExternalSecret resources

*   **Note:** The deployment runbook references **ECR repositories** for Docker images. Your Terraform SHOULD create:
    - ECR repository: `sovd-backend`
    - ECR repository: `sovd-frontend`
    - ECR lifecycle policies (retain last 10 images, auto-delete untagged)

*   **Warning:** The Helm chart configures **IRSA (IAM Roles for Service Accounts)** via the annotation `eks.amazonaws.com/role-arn`. Your Terraform MUST:
    1. Create an IAM role for the service account
    2. Attach policies for Secrets Manager read access
    3. Configure the OIDC provider trust relationship
    4. Output the role ARN for use in Helm values

*   **Tip:** For the **VPC module**, the acceptance criteria specify "3 public+3 private subnets, AZs". The standard AWS best practice is:
    - 3 Availability Zones (us-east-1a, us-east-1b, us-east-1c)
    - 3 public subnets (one per AZ) for ALB and NAT gateways
    - 3 private subnets (one per AZ) for EKS worker nodes, RDS, ElastiCache
    - NAT Gateway in each public subnet (or single NAT for cost savings)
    - Internet Gateway for public subnet routing
    - VPC CIDR: 10.0.0.0/16 (or similar RFC1918 range)

*   **Tip:** For the **RDS module**, key configurations:
    - Engine: PostgreSQL 15.x
    - Instance class: db.t3.large (or db.t3.medium for staging)
    - Multi-AZ: `true` for production
    - Storage: 100GB gp3, autoscaling enabled
    - Backup retention: 7 days production, 1 day staging
    - Database name: `sovd_production` (or parameterized)
    - Master username: `sovd_admin` (or parameterized)
    - Master password: Store in Secrets Manager, reference in RDS config
    - Security group: Allow ingress from EKS worker node security group on port 5432

*   **Tip:** For the **ElastiCache module**, key configurations:
    - Engine: Redis 7.x
    - Node type: cache.t3.medium (or cache.t3.small for staging)
    - Number of cache nodes: 1 (or 2 with read replica for production)
    - Automatic failover: Enable for production
    - Security group: Allow ingress from EKS worker nodes on port 6379

*   **Note:** The project includes **Prometheus and Grafana** for monitoring (already in docker-compose.yml for local dev). For production on EKS, you SHOULD document in infrastructure_setup.md how to:
    - Deploy Prometheus via Helm (kube-prometheus-stack)
    - Configure ServiceMonitor for backend `/metrics` endpoint
    - Deploy Grafana dashboards (existing dashboards in `infrastructure/docker/grafana/`)

*   **Critical:** The **infrastructure_setup.md** document is a key deliverable. It MUST include:
    1. **Prerequisites:** AWS CLI, Terraform 1.5+, kubectl, Helm 3, AWS account, permissions required
    2. **Initial Setup:** Clone repo, configure AWS credentials, update variables.tf
    3. **Provisioning Steps:**
        - `terraform init`
        - `terraform plan` (review output)
        - `terraform apply` (confirm and wait ~20 minutes)
        - Capture outputs (RDS endpoint, ElastiCache endpoint, ECR URLs, IAM role ARN)
    4. **Post-Provisioning:**
        - Update Helm `values-production.yaml` with Terraform outputs
        - Install External Secrets Operator
        - Create secrets in AWS Secrets Manager
        - Deploy Helm chart
    5. **Verification:**
        - Check all resources in AWS Console
        - Verify kubectl can access cluster
        - Test database connectivity
        - Test Redis connectivity
    6. **Teardown:**
        - `helm uninstall` first
        - `terraform destroy` (confirm, takes ~15 minutes)
        - Verify all resources deleted in AWS Console
    7. **Cost Estimates:** Breakdown by service, monthly totals for staging and production

*   **Best Practice:** Use Terraform **workspaces** or separate state files for staging vs production environments. Document this in infrastructure_setup.md.

*   **Best Practice:** Include a **terraform.tfvars.example** file with all required variables and example values (but DO NOT commit real credentials).

### Acceptance Criteria Checklist

Based on the task acceptance criteria, ensure your implementation includes:

- [ ] **Terraform main.tf** with provider configuration, backend (S3 + DynamoDB for state locking), and module invocations
- [ ] **Terraform variables.tf** with all configurable parameters (region, environment, instance types, etc.)
- [ ] **Terraform outputs.tf** with all critical outputs (VPC ID, subnet IDs, RDS endpoint, ElastiCache endpoint, EKS cluster name, ECR repository URLs, IAM role ARN)
- [ ] **VPC Module** (infrastructure/terraform/modules/vpc/main.tf): 3 public + 3 private subnets across 3 AZs
- [ ] **EKS Module** (infrastructure/terraform/modules/eks/main.tf): Cluster with 3 t3.large worker nodes, OIDC provider, node IAM role
- [ ] **RDS Module** (infrastructure/terraform/modules/rds/main.tf): PostgreSQL 15, Multi-AZ, security group, subnet group
- [ ] **ElastiCache Module** (infrastructure/terraform/modules/elasticache/main.tf or similar): Redis 7, subnet group, security group
- [ ] **ALB Module or Documented** (can be created by Ingress Controller, document this)
- [ ] **Route53 Module or Documented** (optional, document manual DNS setup as alternative)
- [ ] **S3 Module** (for Terraform state backend, logs, or backups)
- [ ] **IAM Module** (service account role, policies for Secrets Manager, ECR, etc.)
- [ ] **Infrastructure Setup Documentation** (docs/runbooks/infrastructure_setup.md) with all 7 sections listed above
- [ ] **Cost Estimates** documented: $500-800/month total, breakdown by service

### Alternative Approach (If Full Terraform is Too Complex)

If full Terraform modules are overly complex for this iteration, the task description allows for:
> "Alternative: manual setup steps detailed"

In this case, you COULD:
1. Create **simplified Terraform** for core stateful resources (RDS, ElastiCache only)
2. Document **manual AWS Console steps** for EKS cluster creation in infrastructure_setup.md
3. Use **eksctl** (AWS EKS CLI tool) for cluster creation and document the commands
4. Focus on making the documentation **extremely detailed and reproducible**

This approach still satisfies the acceptance criteria by providing "manual setup steps detailed" as an alternative.

---

## Final Recommendations for the Coder Agent

1. **Start with the documentation:** Create `docs/runbooks/infrastructure_setup.md` first with the full structure, then fill in details as you create Terraform modules.

2. **Use modular Terraform:** Each AWS service should be a separate module under `infrastructure/terraform/modules/`. This makes the code reusable and testable.

3. **Output everything:** Your `outputs.tf` should output every value needed in the Helm `values-production.yaml` file. Make it easy to copy-paste.

4. **Cost calculator:** Use the [AWS Pricing Calculator](https://calculator.aws) to generate detailed cost estimates for the documentation.

5. **Test plan:** Include `terraform plan` output examples in the documentation showing what resources will be created.

6. **Security:** Never hardcode secrets. Use AWS Secrets Manager references and Terraform data sources where possible.

7. **State management:** Configure S3 backend for Terraform state with DynamoDB locking in `main.tf`.

8. **Tagging strategy:** Tag ALL resources with `Environment`, `Application`, `ManagedBy` tags for cost tracking and resource management.

9. **Dependencies:** The task depends on I5.T2 (Helm chart creation), which is done. Ensure your infrastructure matches what the Helm chart expects.

10. **Optional vs Required:** Since the task is marked "Optional for MVP", prioritize creating excellent documentation that allows both automated (Terraform) AND manual approaches. This gives users flexibility.
