# Infrastructure Setup Guide

This document provides comprehensive instructions for provisioning and managing the SOVD WebApp production infrastructure on AWS using Terraform.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture Overview](#architecture-overview)
3. [Initial Setup](#initial-setup)
4. [Provisioning Infrastructure](#provisioning-infrastructure)
5. [Post-Provisioning Configuration](#post-provisioning-configuration)
6. [Verification](#verification)
7. [Teardown](#teardown)
8. [Cost Estimates](#cost-estimates)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Tools

Ensure the following tools are installed and configured:

- **AWS CLI** (v2.x or higher)
  ```bash
  aws --version
  # Install: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
  ```

- **Terraform** (v1.5.0 or higher)
  ```bash
  terraform --version
  # Install: https://developer.hashicorp.com/terraform/downloads
  ```

- **kubectl** (matching your EKS cluster version)
  ```bash
  kubectl version --client
  # Install: https://kubernetes.io/docs/tasks/tools/
  ```

- **Helm** (v3.x)
  ```bash
  helm version
  # Install: https://helm.sh/docs/intro/install/
  ```

### AWS Account Requirements

- AWS account with administrative access
- AWS CLI configured with credentials:
  ```bash
  aws configure
  # Enter your AWS Access Key ID, Secret Access Key, and default region (us-east-1)
  ```

- Verify credentials:
  ```bash
  aws sts get-caller-identity
  ```

### Required IAM Permissions

Your AWS user/role must have permissions to create:
- VPC, Subnets, Route Tables, NAT Gateways, Internet Gateway
- EKS Clusters, Node Groups, EKS Add-ons
- RDS Instances, DB Subnet Groups, DB Parameter Groups
- ElastiCache Replication Groups, Subnet Groups, Parameter Groups
- S3 Buckets, Bucket Policies
- ECR Repositories, Repository Policies
- IAM Roles, Policies, OIDC Providers
- Secrets Manager Secrets
- CloudWatch Log Groups, Alarms
- Security Groups

**Recommended**: Use the `AdministratorAccess` managed policy for initial setup, then create a custom policy with least-privilege permissions for ongoing operations.

---

## Architecture Overview

The Terraform infrastructure creates the following AWS resources:

### Core Infrastructure (VPC Module)
- **VPC**: 10.0.0.0/16 CIDR block
- **Public Subnets**: 3 subnets across 3 Availability Zones (us-east-1a, us-east-1b, us-east-1c)
  - 10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24
- **Private Subnets**: 3 subnets across 3 Availability Zones
  - 10.0.10.0/24, 10.0.11.0/24, 10.0.12.0/24
- **NAT Gateways**: 3 NAT Gateways (one per AZ) for high availability in production, or 1 NAT Gateway for staging (cost savings)
- **Internet Gateway**: For public subnet internet access
- **VPC Flow Logs**: Network traffic logging to CloudWatch

### Compute (EKS Module)
- **EKS Cluster**: Kubernetes v1.28
- **Managed Node Group**: 3 worker nodes (t3.large instances)
  - Auto-scaling: Min 3, Max 6 nodes
  - Deployed in private subnets
- **EKS Add-ons**: VPC CNI, CoreDNS, kube-proxy, EBS CSI Driver
- **OIDC Provider**: For IAM Roles for Service Accounts (IRSA)

### Database (RDS Module)
- **PostgreSQL 15.5**: Multi-AZ deployment for high availability
- **Instance Class**: db.t3.large (production) or db.t3.medium (staging)
- **Storage**: 100 GB gp3 with auto-scaling up to 500 GB
- **Backups**: 7-day retention (production) or 1-day (staging)
- **Encryption**: At-rest encryption enabled
- **Enhanced Monitoring**: 60-second interval
- **Performance Insights**: Enabled for production
- **Security**: Deployed in private subnets, accessible only from EKS worker nodes

### Cache (ElastiCache Module)
- **Redis 7.1**: For caching and pub/sub messaging
- **Node Type**: cache.t3.medium (production) or cache.t3.small (staging)
- **Configuration**: 1 node (production can scale to 2+ for automatic failover)
- **Encryption**: At-rest encryption enabled
- **Backups**: 7-day snapshots (production) or 1-day (staging)

### Container Registry (ECR Module)
- **Backend Repository**: `sovd-{environment}-backend`
- **Frontend Repository**: `sovd-{environment}-frontend`
- **Lifecycle Policy**: Keep last 10 tagged images, delete untagged after 7 days
- **Image Scanning**: Enabled on push
- **Encryption**: AES256

### Storage (S3 Module)
- **Logs Bucket**: Application logs with lifecycle policy (30d → IA, 90d → Glacier, 365d → Delete)
- **Backups Bucket**: Database backups with lifecycle policy (30d → IA, 90d → Glacier, 365d/30d → Delete)
- **Versioning**: Enabled on both buckets
- **Encryption**: AES256
- **Public Access**: Blocked

### Security (IAM Module)
- **Service Account Role**: IRSA role for Kubernetes pods to access AWS services
  - Secrets Manager read access for `sovd/{environment}/*` secrets
  - S3 read/write access for logs and backups
  - CloudWatch Logs write access

---

## Initial Setup

### 1. Clone Repository and Navigate to Terraform Directory

```bash
cd /home/aman/dev/personal-projects/sovd/infrastructure/terraform
```

### 2. Create Terraform Backend Resources

Before running Terraform, you must manually create the S3 bucket and DynamoDB table for remote state storage:

```bash
# Get your AWS account ID
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create S3 bucket for Terraform state
aws s3 mb s3://sovd-terraform-state-${AWS_ACCOUNT_ID} --region us-east-1

# Enable versioning on state bucket
aws s3api put-bucket-versioning \
  --bucket sovd-terraform-state-${AWS_ACCOUNT_ID} \
  --versioning-configuration Status=Enabled

# Enable encryption on state bucket
aws s3api put-bucket-encryption \
  --bucket sovd-terraform-state-${AWS_ACCOUNT_ID} \
  --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

# Block public access on state bucket
aws s3api put-public-access-block \
  --bucket sovd-terraform-state-${AWS_ACCOUNT_ID} \
  --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name sovd-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### 3. Update Terraform Backend Configuration

Edit `main.tf` and replace the placeholder in the backend configuration:

```hcl
backend "s3" {
  bucket         = "sovd-terraform-state-123456789012" # Replace with your bucket name
  key            = "sovd-webapp/terraform.tfstate"
  region         = "us-east-1"
  encrypt        = true
  dynamodb_table = "sovd-terraform-locks"
}
```

Replace `123456789012` with your actual AWS account ID (from the `$AWS_ACCOUNT_ID` variable).

### 4. Configure Terraform Variables

Create a `terraform.tfvars` file from the example:

```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and configure for your environment:

**Production Configuration:**
```hcl
aws_region  = "us-east-1"
environment = "production"

# VPC
vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
enable_nat_gateway   = true
single_nat_gateway   = false # Use 3 NAT Gateways for HA

# RDS
rds_instance_class          = "db.t3.large"
rds_multi_az                = true
rds_backup_retention_period = 7
rds_deletion_protection     = true

# ElastiCache
elasticache_node_type = "cache.t3.medium"

# EKS
eks_node_instance_type = "t3.large"
eks_node_desired_size  = 3
eks_node_max_size      = 6
```

**Staging Configuration (Cost-Optimized):**
```hcl
environment = "staging"
single_nat_gateway          = true  # Use 1 NAT Gateway
rds_instance_class          = "db.t3.medium"
rds_multi_az                = false
rds_backup_retention_period = 1
rds_deletion_protection     = false
elasticache_node_type       = "cache.t3.small"
eks_node_instance_type      = "t3.medium"
```

---

## Provisioning Infrastructure

### 1. Initialize Terraform

```bash
terraform init
```

This will:
- Download required providers (AWS ~> 5.0)
- Configure the S3 backend for state storage
- Initialize modules

**Expected Output:**
```
Terraform has been successfully initialized!
```

### 2. Review the Execution Plan

```bash
terraform plan -out=tfplan
```

This generates an execution plan showing all resources that will be created. Review carefully:

**Expected Resources (~60-70 resources):**
- VPC, Subnets, Route Tables, NAT Gateways, Internet Gateway
- EKS Cluster, Node Group, Security Groups, IAM Roles
- RDS Instance, DB Subnet Group, Parameter Group, Security Group
- ElastiCache Replication Group, Subnet Group, Parameter Group
- ECR Repositories (2)
- S3 Buckets (2)
- IAM Roles and Policies for IRSA
- CloudWatch Log Groups and Alarms
- Secrets Manager secret (for RDS password)

**Example Plan Output Snippet:**
```
Plan: 68 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + eks_cluster_name           = "sovd-production-cluster"
  + rds_endpoint               = (known after apply)
  + elasticache_endpoint       = (known after apply)
  + ecr_backend_repository_url = (known after apply)
  + service_account_role_arn   = (known after apply)
  ...
```

### 3. Apply the Configuration

```bash
terraform apply tfplan
```

Terraform will create all resources. **This takes approximately 15-25 minutes**, with the EKS cluster creation being the longest operation (~15 minutes).

**Progress Indicators:**
- VPC and networking: ~2 minutes
- RDS instance: ~5-8 minutes
- ElastiCache: ~3-5 minutes
- EKS cluster: ~15 minutes
- EKS node group: ~3-5 minutes
- Other resources: ~1-2 minutes

**Expected Final Output:**
```
Apply complete! Resources: 68 added, 0 changed, 0 destroyed.

Outputs:

eks_cluster_name = "sovd-production-cluster"
rds_endpoint = "sovd-production.c9akciq32.us-east-1.rds.amazonaws.com:5432"
elasticache_endpoint = "sovd-production.abc123.ng.0001.use1.cache.amazonaws.com"
ecr_backend_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-production-backend"
ecr_frontend_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-production-frontend"
service_account_role_arn = "arn:aws:iam::123456789012:role/sovd-production-service-account-role"
helm_values_snippet = <<-EOT
  # Update infrastructure/helm/sovd-webapp/values-production.yaml with these values:
  ...
EOT
```

### 4. Save Terraform Outputs

Save the outputs for use in post-provisioning configuration:

```bash
terraform output > terraform-outputs.txt
terraform output -json > terraform-outputs.json
```

---

## Post-Provisioning Configuration

After Terraform completes, perform the following manual configuration steps:

### 1. Configure kubectl for EKS Cluster

```bash
aws eks update-kubeconfig --region us-east-1 --name sovd-production-cluster

# Verify connection
kubectl get nodes
```

**Expected Output:**
```
NAME                             STATUS   ROLES    AGE   VERSION
ip-10-0-10-123.ec2.internal      Ready    <none>   5m    v1.28.x
ip-10-0-11-456.ec2.internal      Ready    <none>   5m    v1.28.x
ip-10-0-12-789.ec2.internal      Ready    <none>   5m    v1.28.x
```

### 2. Install AWS Load Balancer Controller (for ALB Ingress)

The AWS Load Balancer Controller is required for the Helm chart's Ingress resource to create an Application Load Balancer.

```bash
# Add EKS Helm repository
helm repo add eks https://aws.github.io/eks-charts
helm repo update

# Create IAM policy for ALB controller
curl -o iam_policy.json https://raw.githubusercontent.com/kubernetes-sigs/aws-load-balancer-controller/v2.7.0/docs/install/iam_policy.json

aws iam create-policy \
  --policy-name AWSLoadBalancerControllerIAMPolicy \
  --policy-document file://iam_policy.json

# Create IAM service account (IRSA)
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

eksctl create iamserviceaccount \
  --cluster=sovd-production-cluster \
  --namespace=kube-system \
  --name=aws-load-balancer-controller \
  --attach-policy-arn=arn:aws:iam::${AWS_ACCOUNT_ID}:policy/AWSLoadBalancerControllerIAMPolicy \
  --override-existing-serviceaccounts \
  --approve

# Install AWS Load Balancer Controller
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system \
  --set clusterName=sovd-production-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller

# Verify installation
kubectl get deployment -n kube-system aws-load-balancer-controller
```

### 3. Install External Secrets Operator (for AWS Secrets Manager Integration)

The External Secrets Operator syncs secrets from AWS Secrets Manager to Kubernetes Secrets.

```bash
# Add External Secrets Helm repository
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace \
  --set installCRDs=true

# Verify installation
kubectl get pods -n external-secrets-system
```

### 4. Create AWS Secrets Manager Secrets

Create secrets for database, JWT, and Redis:

```bash
# Get RDS password from Terraform-generated secret
export RDS_SECRET_ARN=$(terraform output -raw rds_secret_arn)
export RDS_PASSWORD=$(aws secretsmanager get-secret-value --secret-id $RDS_SECRET_ARN --query SecretString --output text | jq -r '.password')
export RDS_ENDPOINT=$(terraform output -raw rds_address)
export RDS_PORT=$(terraform output -raw rds_port)
export RDS_DATABASE=$(terraform output -raw rds_database_name)
export RDS_USERNAME=$(terraform output -raw rds_master_username)

# Create database secret
aws secretsmanager create-secret \
  --name sovd/production/database \
  --description "SOVD production database connection string" \
  --secret-string "{\"DATABASE_URL\":\"postgresql://${RDS_USERNAME}:${RDS_PASSWORD}@${RDS_ENDPOINT}:${RDS_PORT}/${RDS_DATABASE}\"}"

# Create JWT secret (generate random secret)
export JWT_SECRET=$(openssl rand -base64 32)
aws secretsmanager create-secret \
  --name sovd/production/jwt \
  --description "SOVD production JWT secret" \
  --secret-string "{\"JWT_SECRET\":\"${JWT_SECRET}\"}"

# Create Redis secret (no password for now, can be added later)
export REDIS_ENDPOINT=$(terraform output -raw elasticache_endpoint)
export REDIS_PORT=$(terraform output -raw elasticache_port)
aws secretsmanager create-secret \
  --name sovd/production/redis \
  --description "SOVD production Redis connection string" \
  --secret-string "{\"REDIS_URL\":\"redis://${REDIS_ENDPOINT}:${REDIS_PORT}\"}"
```

### 5. Create SecretStore and ExternalSecret Resources

Create Kubernetes resources to sync AWS Secrets Manager secrets:

**File: `infrastructure/kubernetes/secret-store.yaml`**
```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets-manager
  namespace: production
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: sovd-webapp-production-sa
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: sovd-database-secret
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: sovd-database-secret
    creationPolicy: Owner
  data:
    - secretKey: DATABASE_URL
      remoteRef:
        key: sovd/production/database
        property: DATABASE_URL
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: sovd-jwt-secret
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: sovd-jwt-secret
    creationPolicy: Owner
  data:
    - secretKey: JWT_SECRET
      remoteRef:
        key: sovd/production/jwt
        property: JWT_SECRET
---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: sovd-redis-secret
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: SecretStore
  target:
    name: sovd-redis-secret
    creationPolicy: Owner
  data:
    - secretKey: REDIS_URL
      remoteRef:
        key: sovd/production/redis
        property: REDIS_URL
```

Apply the resources:
```bash
kubectl create namespace production
kubectl apply -f infrastructure/kubernetes/secret-store.yaml
```

### 6. Install Metrics Server (for HPA)

The Horizontal Pod Autoscaler requires the Metrics Server to scale based on CPU/memory.

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# Verify installation
kubectl get deployment metrics-server -n kube-system
```

### 7. Update Helm Values with Terraform Outputs

Copy the `helm_values_snippet` from Terraform outputs and update `infrastructure/helm/sovd-webapp/values-production.yaml`:

```bash
# Display the snippet
terraform output helm_values_snippet

# Manually update values-production.yaml with:
# - backend.image.repository
# - frontend.image.repository
# - config.database.host
# - config.database.port
# - config.redis.host
# - config.redis.port
# - serviceAccount.annotations.eks.amazonaws.com/role-arn
```

### 8. Build and Push Docker Images to ECR

```bash
# Get ECR login command
terraform output ecr_login_command | bash

# Build backend image
cd backend
docker build -t sovd-backend:latest .
docker tag sovd-backend:latest $(terraform output -raw ecr_backend_repository_url):latest
docker push $(terraform output -raw ecr_backend_repository_url):latest

# Build frontend image
cd ../frontend
docker build -t sovd-frontend:latest .
docker tag sovd-frontend:latest $(terraform output -raw ecr_frontend_repository_url):latest
docker push $(terraform output -raw ecr_frontend_repository_url):latest
```

### 9. Deploy SOVD Application with Helm

```bash
cd infrastructure/helm

# Install the Helm chart
helm install sovd-webapp ./sovd-webapp \
  -n production \
  --create-namespace \
  -f sovd-webapp/values-production.yaml

# Verify deployment
kubectl get pods -n production
kubectl get ingress -n production
```

### 10. Configure DNS (Route53 or External DNS Provider)

After the ALB is created, configure DNS to point to the ALB endpoint:

```bash
# Get ALB DNS name
kubectl get ingress -n production sovd-webapp-ingress -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'

# Create Route53 A record (ALIAS) pointing to the ALB
# Or configure your external DNS provider to CNAME to the ALB hostname
```

---

## Verification

### 1. Verify All AWS Resources Created

**VPC and Networking:**
```bash
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=sovd-production-vpc"
aws ec2 describe-subnets --filters "Name=tag:Environment,Values=production"
aws ec2 describe-nat-gateways --filter "Name=tag:Environment,Values=production"
```

**EKS Cluster:**
```bash
aws eks describe-cluster --name sovd-production-cluster
kubectl get nodes
kubectl get pods -A
```

**RDS Instance:**
```bash
aws rds describe-db-instances --db-instance-identifier sovd-production
```

**ElastiCache:**
```bash
aws elasticache describe-replication-groups --replication-group-id sovd-production
```

**ECR Repositories:**
```bash
aws ecr describe-repositories --repository-names sovd-production-backend sovd-production-frontend
```

**S3 Buckets:**
```bash
aws s3 ls | grep sovd-production
```

### 2. Test Database Connectivity

From a pod in the EKS cluster:

```bash
# Create a temporary PostgreSQL client pod
kubectl run psql-test --rm -it --image=postgres:15 --namespace=production -- /bin/bash

# Inside the pod, test connection
export RDS_ENDPOINT=$(terraform output -raw rds_address)
psql -h $RDS_ENDPOINT -U sovd_admin -d sovd_production

# Enter password when prompted (from Secrets Manager)
# If successful, you'll see the PostgreSQL prompt: sovd_production=>
```

### 3. Test Redis Connectivity

```bash
# Create a temporary Redis client pod
kubectl run redis-test --rm -it --image=redis:7 --namespace=production -- /bin/bash

# Inside the pod, test connection
export REDIS_ENDPOINT=$(terraform output -raw elasticache_endpoint)
redis-cli -h $REDIS_ENDPOINT

# If successful, you'll see the Redis prompt: 127.0.0.1:6379>
# Test with: PING (should return PONG)
```

### 4. Verify Application Health

```bash
# Check pod status
kubectl get pods -n production

# Check pod logs
kubectl logs -n production -l app=sovd-backend --tail=50
kubectl logs -n production -l app=sovd-frontend --tail=50

# Check ingress
kubectl get ingress -n production

# Test API endpoint (replace with your actual domain)
curl https://sovd.production.com/api/health
```

### 5. Verify Secrets Synced from AWS Secrets Manager

```bash
kubectl get secrets -n production
kubectl get externalsecrets -n production

# Check specific secret (should show 'SecretSynced')
kubectl describe externalsecret sovd-database-secret -n production
```

### 6. Verify HPA Scaling

```bash
kubectl get hpa -n production

# Generate load to test scaling (optional)
kubectl run -it --rm load-generator --image=busybox --namespace=production -- /bin/sh
# Inside the pod: while true; do wget -q -O- http://sovd-backend-service:8000/api/health; done

# Watch HPA scale up
kubectl get hpa -n production -w
```

---

## Teardown

To delete all infrastructure and avoid ongoing costs:

### 1. Uninstall Helm Chart First

```bash
helm uninstall sovd-webapp -n production

# Wait for LoadBalancer to be deleted
kubectl get svc -n production -w

# Delete namespace
kubectl delete namespace production
```

### 2. Delete Kubernetes Add-ons

```bash
helm uninstall aws-load-balancer-controller -n kube-system
helm uninstall external-secrets -n external-secrets-system
kubectl delete namespace external-secrets-system
```

### 3. Delete AWS Secrets Manager Secrets (Optional)

```bash
aws secretsmanager delete-secret --secret-id sovd/production/database --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id sovd/production/jwt --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id sovd/production/redis --force-delete-without-recovery
```

### 4. Run Terraform Destroy

```bash
terraform destroy
```

Review the plan carefully, then confirm with `yes`.

**Teardown Duration:** ~15-20 minutes

**Resources Deleted:**
- EKS cluster and node group
- RDS instance (snapshot created if `skip_final_snapshot = false`)
- ElastiCache replication group
- VPC, subnets, NAT gateways, internet gateway
- ECR repositories (images deleted)
- S3 buckets (must be empty; delete objects manually if needed)
- IAM roles and policies
- CloudWatch log groups
- Security groups

### 5. Delete Terraform State Backend (Optional)

If you want to completely remove the Terraform state storage:

```bash
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Empty the S3 bucket
aws s3 rm s3://sovd-terraform-state-${AWS_ACCOUNT_ID} --recursive

# Delete the S3 bucket
aws s3 rb s3://sovd-terraform-state-${AWS_ACCOUNT_ID}

# Delete the DynamoDB table
aws dynamodb delete-table --table-name sovd-terraform-locks
```

### 6. Verify All Resources Deleted

```bash
# Check VPC
aws ec2 describe-vpcs --filters "Name=tag:Environment,Values=production"

# Check EKS
aws eks list-clusters

# Check RDS
aws rds describe-db-instances

# Check ElastiCache
aws elasticache describe-replication-groups

# Check S3
aws s3 ls | grep sovd
```

---

## Cost Estimates

### Production Environment (~$793/month)

| Service | Configuration | Monthly Cost (USD) |
|---------|--------------|-------------------|
| **EKS Control Plane** | 1 cluster | $73 |
| **EKS Worker Nodes** | 3x t3.large (on-demand) | $270 |
| **RDS PostgreSQL** | db.t3.large Multi-AZ, 100GB gp3 | $220 |
| **ElastiCache Redis** | cache.t3.medium, 1 node | $85 |
| **NAT Gateways** | 3x NAT @ $0.045/hr + data transfer (~$10/NAT) | $100 |
| **Application Load Balancer** | 1 ALB + data transfer | $25 |
| **S3 Storage** | Logs, backups (~100GB) | $3 |
| **ECR Storage** | Docker images (~50GB) | $5 |
| **CloudWatch Logs** | ~50GB ingestion, retention | $10 |
| **Data Transfer** | Inter-AZ, outbound | $12 |
| **TOTAL** | | **~$793/month** |

**Notes:**
- Costs are estimates based on us-east-1 pricing (as of January 2025)
- Actual costs vary based on data transfer, storage usage, and additional features
- Does not include costs for Route53, ACM certificates (free), or Secrets Manager (<$1/month)

### Staging Environment (~$348/month)

| Service | Configuration | Monthly Cost (USD) |
|---------|--------------|-------------------|
| **EKS Control Plane** | 1 cluster | $73 |
| **EKS Worker Nodes** | 3x t3.medium (on-demand) | $90 |
| **RDS PostgreSQL** | db.t3.medium Single-AZ, 100GB gp3 | $70 |
| **ElastiCache Redis** | cache.t3.small, 1 node | $40 |
| **NAT Gateway** | 1x NAT @ $0.045/hr + data transfer | $35 |
| **Application Load Balancer** | 1 ALB + data transfer | $25 |
| **S3 Storage** | Logs, backups (~50GB) | $2 |
| **ECR Storage** | Docker images (~30GB) | $3 |
| **CloudWatch Logs** | ~20GB ingestion, retention | $5 |
| **Data Transfer** | Inter-AZ, outbound | $5 |
| **TOTAL** | | **~$348/month** |

### Cost Optimization Strategies

1. **Use Spot Instances for EKS Workers** (savings: ~60%)
   - Configure node group with spot instances
   - Trade-off: Nodes may be interrupted

2. **Use Single NAT Gateway in Staging** (savings: ~$70/month)
   - Already configured in staging

3. **Use Aurora Serverless v2 for RDS** (savings: variable)
   - Pay per ACU (Aurora Capacity Unit) instead of instance hours
   - Better for variable workloads

4. **Use Reserved Instances** (savings: ~40% for 1-year commitment)
   - Purchase 1-year or 3-year reserved instances for RDS and ElastiCache

5. **Automate Environment Teardown** (savings: 100% when not in use)
   - Use CI/CD to destroy staging environment outside business hours
   - Recreate on-demand

6. **Reduce Backup Retention** (savings: ~$5-10/month)
   - Staging: 1 day retention
   - Production: 7 days (can reduce to 3-5 days)

7. **Use S3 Intelligent-Tiering** (savings: ~20-30%)
   - Automatically moves objects between access tiers

**Estimated Savings with Optimizations:**
- Production: $793 → $550/month (use RIs, optimize backups)
- Staging: $348 → $180/month (use spot instances, reduce retention, automated teardown)

---

## Troubleshooting

### Issue: Terraform `apply` fails with "InvalidParameterException: The following supplied instance types do not exist"

**Cause:** Instance type not available in selected AZ.

**Solution:**
1. Check available instance types:
   ```bash
   aws ec2 describe-instance-type-offerings --location-type availability-zone --filters "Name=instance-type,Values=t3.large" --region us-east-1
   ```
2. Update `availability_zones` in `terraform.tfvars` to use AZs that support your instance type.

### Issue: EKS cluster creation times out

**Cause:** Network connectivity or IAM permissions issue.

**Solution:**
1. Verify VPC and subnets are created correctly
2. Check EKS service role has required permissions
3. Retry: `terraform apply` (Terraform will resume from last checkpoint)

### Issue: `kubectl get nodes` returns "No resources found"

**Cause:** Worker nodes not yet ready or security group misconfiguration.

**Solution:**
1. Wait 5 minutes (node group initialization takes time)
2. Check node group status:
   ```bash
   aws eks describe-nodegroup --cluster-name sovd-production-cluster --nodegroup-name sovd-production-node-group
   ```
3. Verify security group allows worker nodes to communicate with control plane

### Issue: RDS connection fails from EKS pods

**Cause:** Security group ingress rule missing or incorrect.

**Solution:**
1. Verify RDS security group allows ingress from EKS worker security group:
   ```bash
   aws ec2 describe-security-groups --group-ids $(terraform output -raw rds_security_group_id)
   ```
2. Check ingress rules include EKS worker security group on port 5432

### Issue: External Secrets not syncing from AWS Secrets Manager

**Cause:** IAM role permissions issue or IRSA configuration incorrect.

**Solution:**
1. Verify service account has correct annotation:
   ```bash
   kubectl get sa sovd-webapp-production-sa -n production -o yaml
   # Should have annotation: eks.amazonaws.com/role-arn: arn:aws:iam::...
   ```
2. Check IAM role trust policy allows OIDC provider:
   ```bash
   aws iam get-role --role-name sovd-production-service-account-role
   ```
3. Check ExternalSecret status:
   ```bash
   kubectl describe externalsecret sovd-database-secret -n production
   # Look for events indicating permission errors
   ```

### Issue: ALB Ingress not creating LoadBalancer

**Cause:** AWS Load Balancer Controller not installed or misconfigured.

**Solution:**
1. Verify controller is running:
   ```bash
   kubectl get deployment -n kube-system aws-load-balancer-controller
   ```
2. Check controller logs:
   ```bash
   kubectl logs -n kube-system deployment/aws-load-balancer-controller
   ```
3. Verify Ingress has correct annotations (see Helm chart `ingress.yaml`)

### Issue: High costs due to data transfer

**Cause:** Excessive cross-AZ or outbound data transfer.

**Solution:**
1. Review VPC Flow Logs to identify traffic patterns
2. Consider using VPC endpoints for AWS services (S3, Secrets Manager)
3. Deploy pods in the same AZ as RDS/ElastiCache when possible

### Issue: `terraform destroy` fails with "DependencyViolation"

**Cause:** Resources still in use (e.g., LoadBalancer attached to VPC).

**Solution:**
1. Delete all Kubernetes resources first (especially LoadBalancer services)
2. Manually delete the ALB in AWS Console
3. Retry `terraform destroy`

---

## Next Steps

After successful infrastructure provisioning:

1. **Configure Monitoring:**
   - Deploy Prometheus and Grafana (see `docs/runbooks/deployment.md`)
   - Import pre-configured dashboards from `infrastructure/docker/grafana/dashboards/`

2. **Set up CI/CD:**
   - Configure GitHub Actions to build and push images to ECR
   - Automate Helm chart upgrades on new commits

3. **Enable TLS:**
   - Request ACM certificate for your domain
   - Update Ingress annotation with certificate ARN

4. **Configure Backups:**
   - Set up automated RDS snapshots export to S3
   - Configure backup monitoring and alerts

5. **Security Hardening:**
   - Enable RDS/ElastiCache encryption in transit (TLS)
   - Configure network policies in Kubernetes
   - Enable AWS GuardDuty and Security Hub

6. **Disaster Recovery:**
   - Document RDS snapshot restore procedure
   - Test failover for Multi-AZ RDS
   - Create runbook for incident response

---

## Additional Resources

- **Terraform AWS Provider Docs:** https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **EKS Best Practices:** https://aws.github.io/aws-eks-best-practices/
- **SOVD Deployment Runbook:** `docs/runbooks/deployment.md`
- **Helm Chart Documentation:** `infrastructure/helm/sovd-webapp/README.md`

---

## Support

For issues or questions:
- Open a GitHub issue in the repository
- Contact the DevOps team
- Refer to AWS Support (if you have a support plan)
