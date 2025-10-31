# Secrets Management with AWS Secrets Manager

This runbook covers the management of secrets for the SOVD WebApp using AWS Secrets Manager and External Secrets Operator.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Prerequisites](#prerequisites)
4. [Initial Setup](#initial-setup)
5. [Creating Secrets](#creating-secrets)
6. [Configuring External Secrets](#configuring-external-secrets)
7. [Verification](#verification)
8. [Secret Rotation](#secret-rotation)
9. [Troubleshooting](#troubleshooting)
10. [Security Best Practices](#security-best-practices)

---

## Overview

The SOVD WebApp uses **AWS Secrets Manager** to securely store sensitive configuration data such as database credentials, JWT signing secrets, and Redis connection strings. The **External Secrets Operator** automatically syncs these secrets from AWS Secrets Manager into Kubernetes Secrets, eliminating the need to store secrets in Git or manually manage Kubernetes Secret objects.

### Benefits

- **Centralized Secret Management**: Single source of truth in AWS Secrets Manager
- **Automatic Rotation**: Secrets can be rotated in AWS and automatically synced to Kubernetes
- **Audit Trail**: AWS CloudTrail logs all secret access for compliance
- **No Secrets in Git**: Secrets never stored in version control
- **IAM Integration**: Uses IAM Roles for Service Accounts (IRSA) for secure authentication

---

## Architecture

The secrets management flow works as follows:

```
┌─────────────────────┐
│ AWS Secrets Manager │  (Source of truth)
│  - sovd/prod/db     │
│  - sovd/prod/jwt    │
│  - sovd/prod/redis  │
└──────────┬──────────┘
           │
           │ (1) External Secrets Operator queries
           │     using IRSA authentication
           ▼
┌─────────────────────┐
│   SecretStore       │  (K8s CRD - defines connection to AWS)
│  - AWS Region       │
│  - IAM Role via SA  │
└──────────┬──────────┘
           │
           │ (2) ExternalSecret references SecretStore
           ▼
┌─────────────────────┐
│  ExternalSecret     │  (K8s CRD - defines mapping)
│  - Refresh: 1h      │
│  - Maps properties  │
└──────────┬──────────┘
           │
           │ (3) Creates/updates K8s Secret
           ▼
┌─────────────────────┐
│  Kubernetes Secret  │  (Native K8s Secret)
│  - database-url     │
│  - jwt-secret       │
│  - redis-url        │
└──────────┬──────────┘
           │
           │ (4) Mounted as env vars
           ▼
┌─────────────────────┐
│   Backend Pod       │
│  - DATABASE_URL     │
│  - JWT_SECRET       │
│  - REDIS_URL        │
└─────────────────────┘
```

### Key Components

1. **AWS Secrets Manager**: Stores secrets in JSON format
2. **IAM Role with IRSA**: Grants service account permission to read secrets
3. **SecretStore**: Kubernetes CRD that defines connection to AWS Secrets Manager
4. **ExternalSecret**: Kubernetes CRD that defines secret mapping and refresh interval
5. **Kubernetes Secret**: Native secret object created by External Secrets Operator
6. **Backend Deployment**: Consumes secrets as environment variables

---

## Prerequisites

Before setting up secrets management, ensure you have:

### Infrastructure

- [x] EKS cluster provisioned (from task I5.T2)
- [x] Terraform infrastructure deployed (from task I5.T7)
- [x] IAM role for service account created with Secrets Manager permissions
- [x] RDS and ElastiCache endpoints available

### Tools

- AWS CLI configured with appropriate credentials
- kubectl configured to access EKS cluster
- helm CLI installed (v3.x or later)
- jq (for JSON parsing)
- openssl (for generating secure secrets)

### Terraform Outputs

Retrieve the following outputs from Terraform:

```bash
cd infrastructure/terraform/environments/production
terraform output rds_endpoint
terraform output redis_endpoint
terraform output service_account_role_arn
```

---

## Initial Setup

### Step 1: Install External Secrets Operator

The External Secrets Operator must be installed in the cluster before deploying the application.

```bash
# Add External Secrets Helm repository
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

# Install External Secrets Operator
helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace \
  --set installCRDs=true \
  --set webhook.port=9443

# Verify installation
kubectl get pods -n external-secrets-system
kubectl get crds | grep external-secrets
```

**Expected CRDs:**
- `externalsecrets.external-secrets.io`
- `secretstores.external-secrets.io`
- `clustersecretstores.external-secrets.io`

For detailed installation instructions, see [infrastructure_setup.md](./infrastructure_setup.md#external-secrets-operator).

### Step 2: Verify IAM Role for Service Account

Ensure the IAM role created by Terraform has the correct trust policy and permissions:

```bash
# Get the role ARN from Terraform
ROLE_ARN=$(cd infrastructure/terraform/environments/production && terraform output -raw service_account_role_arn)

# Verify trust policy allows EKS service account
aws iam get-role --role-name sovd-production-service-account-role \
  --query 'Role.AssumeRolePolicyDocument' \
  --output json | jq

# Verify Secrets Manager permissions
aws iam list-attached-role-policies \
  --role-name sovd-production-service-account-role

aws iam get-policy-version \
  --policy-arn $(aws iam list-attached-role-policies --role-name sovd-production-service-account-role --query 'AttachedPolicies[0].PolicyArn' --output text) \
  --version-id v1 \
  --query 'PolicyVersion.Document' \
  --output json | jq
```

**Expected Permissions:**
- `secretsmanager:GetSecretValue`
- `secretsmanager:DescribeSecret`

**Expected Trust Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/OIDC_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/OIDC_ID:sub": "system:serviceaccount:production:sovd-webapp-production-sa"
        }
      }
    }
  ]
}
```

---

## Creating Secrets

### Using the Automated Script

We provide a script to create all required secrets in AWS Secrets Manager:

```bash
# Navigate to scripts directory
cd scripts

# Run the script for production environment
./create_aws_secrets.sh production us-east-1
```

The script will:
1. Extract RDS and Redis endpoints from Terraform outputs
2. Generate secure random passwords and JWT secrets
3. Create three secrets in AWS Secrets Manager:
   - `sovd/production/database`
   - `sovd/production/jwt`
   - `sovd/production/redis`
4. Display the generated database password (store this securely!)
5. Provide instructions for updating the RDS master password

### Manual Secret Creation

If you prefer to create secrets manually or need to customize values:

#### Database Secret

```bash
# Generate secure password
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Get RDS endpoint from Terraform
DB_ENDPOINT=$(cd ../infrastructure/terraform/environments/production && terraform output -raw rds_endpoint)

# Create secret
aws secretsmanager create-secret \
  --name sovd/production/database \
  --description "SOVD production database credentials" \
  --secret-string "{
    \"DATABASE_URL\": \"postgresql+asyncpg://sovd_admin:${DB_PASSWORD}@${DB_ENDPOINT}/sovd_production\",
    \"DB_HOST\": \"${DB_ENDPOINT%:*}\",
    \"DB_PORT\": \"${DB_ENDPOINT#*:}\",
    \"DB_NAME\": \"sovd_production\",
    \"DB_USERNAME\": \"sovd_admin\",
    \"DB_PASSWORD\": \"${DB_PASSWORD}\"
  }" \
  --region us-east-1

# Update RDS master password to match
aws rds modify-db-instance \
  --db-instance-identifier sovd-production-db \
  --master-user-password "${DB_PASSWORD}" \
  --apply-immediately \
  --region us-east-1
```

#### JWT Secret

```bash
# Generate secure JWT secret (64 characters)
JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)

# Create secret
aws secretsmanager create-secret \
  --name sovd/production/jwt \
  --description "SOVD production JWT signing secret" \
  --secret-string "{\"JWT_SECRET\": \"${JWT_SECRET}\"}" \
  --region us-east-1
```

#### Redis Secret

```bash
# Get Redis endpoint from Terraform
REDIS_ENDPOINT=$(cd ../infrastructure/terraform/environments/production && terraform output -raw redis_endpoint)

# Create secret (ElastiCache typically doesn't use passwords with encryption in-transit)
aws secretsmanager create-secret \
  --name sovd/production/redis \
  --description "SOVD production Redis connection string" \
  --secret-string "{
    \"REDIS_URL\": \"redis://${REDIS_ENDPOINT}/0\",
    \"REDIS_HOST\": \"${REDIS_ENDPOINT%:*}\",
    \"REDIS_PORT\": \"${REDIS_ENDPOINT#*:}\"
  }" \
  --region us-east-1
```

### Verify Secrets Created

```bash
# List all SOVD secrets
aws secretsmanager list-secrets \
  --filters Key=name,Values=sovd/production/ \
  --region us-east-1

# Retrieve a secret value (testing only - do not expose in logs)
aws secretsmanager get-secret-value \
  --secret-id sovd/production/jwt \
  --region us-east-1 \
  --query 'SecretString' \
  --output text | jq
```

---

## Configuring External Secrets

### Deploy Application with External Secrets Enabled

The Helm chart includes all necessary External Secrets resources. Deploy with production values:

```bash
cd infrastructure/helm

# Verify values-production.yaml has externalSecrets.enabled: true
grep -A 5 "externalSecrets:" sovd-webapp/values-production.yaml

# Deploy the application
helm upgrade --install sovd-webapp \
  ./sovd-webapp \
  -f sovd-webapp/values-production.yaml \
  -n production \
  --create-namespace \
  --wait \
  --timeout 10m
```

This creates:
- **ServiceAccount** with IRSA annotation
- **SecretStore** pointing to AWS Secrets Manager
- **ExternalSecret** defining secret mappings
- **Kubernetes Secret** (automatically created by operator)
- **Deployments** consuming the secret

### Verify Resources Created

```bash
# Check ServiceAccount has correct IAM role annotation
kubectl get serviceaccount sovd-webapp-production-sa -n production -o yaml | grep eks.amazonaws.com/role-arn

# Check SecretStore is ready
kubectl get secretstore -n production
kubectl describe secretstore aws-secrets-manager -n production

# Check ExternalSecret status
kubectl get externalsecret -n production
kubectl describe externalsecret sovd-webapp-external-secrets -n production
```

**Expected ExternalSecret Status:**
```yaml
Status:
  Binding:
    Name: sovd-webapp-secrets
  Conditions:
    Last Transition Time:  2025-10-31T12:00:00Z
    Message:               Secret was synced
    Reason:                SecretSynced
    Status:                True
    Type:                  Ready
  Refresh Time:            2025-10-31T12:00:00Z
  Synced Resource Version: 1-abc123def456
```

---

## Verification

### Step 1: Verify SecretStore Connectivity

The SecretStore should successfully authenticate to AWS Secrets Manager using IRSA:

```bash
# Check SecretStore status
kubectl get secretstore aws-secrets-manager -n production -o jsonpath='{.status.conditions[0]}' | jq

# Expected: status: "True", type: "Ready"
```

If not ready, check:
- IAM role ARN in ServiceAccount annotation
- Trust policy allows the specific service account
- Secrets Manager permissions on IAM role
- OIDC provider configured on EKS cluster

### Step 2: Verify ExternalSecret Sync

The ExternalSecret should create a Kubernetes Secret with synced values:

```bash
# Check ExternalSecret status
kubectl get externalsecret -n production
kubectl describe externalsecret sovd-webapp-external-secrets -n production

# Verify Kubernetes Secret was created
kubectl get secret sovd-webapp-secrets -n production
kubectl describe secret sovd-webapp-secrets -n production
```

**Verify secret contains expected keys:**

```bash
kubectl get secret sovd-webapp-secrets -n production -o json | jq '.data | keys'
```

Expected keys: `["database-url", "jwt-secret", "redis-url"]`

### Step 3: Verify Secret Values (Decode)

**WARNING**: Only perform this in a secure environment. Do not expose secrets in logs or shared terminals.

```bash
# Decode DATABASE_URL
kubectl get secret sovd-webapp-secrets -n production -o jsonpath='{.data.database-url}' | base64 -d
echo ""

# Decode JWT_SECRET (first 20 chars only for verification)
kubectl get secret sovd-webapp-secrets -n production -o jsonpath='{.data.jwt-secret}' | base64 -d | cut -c1-20
echo "..."

# Decode REDIS_URL
kubectl get secret sovd-webapp-secrets -n production -o jsonpath='{.data.redis-url}' | base64 -d
echo ""
```

### Step 4: Verify Backend Pod Uses Secrets

Check that the backend pods have the correct environment variables:

```bash
# Get a backend pod name
BACKEND_POD=$(kubectl get pods -n production -l app.kubernetes.io/name=sovd-webapp,app.kubernetes.io/component=backend -o jsonpath='{.items[0].metadata.name}')

# Verify environment variables are set (without exposing values)
kubectl exec -n production $BACKEND_POD -- env | grep -E "DATABASE_URL|JWT_SECRET|REDIS_URL" | sed 's/=.*/=***/'

# Expected output:
# DATABASE_URL=***
# JWT_SECRET=***
# REDIS_URL=***
```

### Step 5: Test Application Connectivity

Verify the application can connect to database and Redis:

```bash
# Check backend logs for successful startup
kubectl logs -n production -l app.kubernetes.io/component=backend --tail=50 | grep -E "database|redis|started"

# Test health endpoint
kubectl port-forward -n production svc/sovd-webapp-backend 8000:8000 &
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

---

## Secret Rotation

### Automatic Rotation

The ExternalSecret is configured with a 1-hour refresh interval. After updating a secret in AWS Secrets Manager, the change will propagate to Kubernetes within 1 hour (or sooner).

### Manual Secret Rotation

#### Step 1: Update Secret in AWS Secrets Manager

```bash
# Example: Rotate JWT secret
NEW_JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)

aws secretsmanager put-secret-value \
  --secret-id sovd/production/jwt \
  --secret-string "{\"JWT_SECRET\": \"${NEW_JWT_SECRET}\"}" \
  --region us-east-1
```

#### Step 2: Force Immediate Sync (Optional)

To sync immediately instead of waiting for the refresh interval:

```bash
# Delete the Kubernetes Secret (External Secrets Operator will recreate it)
kubectl delete secret sovd-webapp-secrets -n production

# Wait for ExternalSecret to recreate it (usually 10-30 seconds)
kubectl wait --for=condition=Ready externalsecret/sovd-webapp-external-secrets -n production --timeout=2m

# Verify secret was recreated
kubectl get secret sovd-webapp-secrets -n production
```

#### Step 3: Restart Pods to Pick Up New Secret

Pods do not automatically reload environment variables when secrets change. Restart deployments:

```bash
# Restart backend deployment
kubectl rollout restart deployment sovd-webapp-backend -n production

# Wait for rollout to complete
kubectl rollout status deployment sovd-webapp-backend -n production

# Verify new pods are running
kubectl get pods -n production -l app.kubernetes.io/component=backend
```

### Database Password Rotation

Database password rotation requires coordination with RDS:

```bash
# 1. Generate new password
NEW_DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# 2. Update RDS master password
aws rds modify-db-instance \
  --db-instance-identifier sovd-production-db \
  --master-user-password "${NEW_DB_PASSWORD}" \
  --apply-immediately \
  --region us-east-1

# 3. Wait for RDS modification to complete (usually 1-2 minutes)
aws rds wait db-instance-available \
  --db-instance-identifier sovd-production-db \
  --region us-east-1

# 4. Update AWS Secrets Manager with new password
DB_ENDPOINT=$(cd ../infrastructure/terraform/environments/production && terraform output -raw rds_endpoint)
aws secretsmanager put-secret-value \
  --secret-id sovd/production/database \
  --secret-string "{
    \"DATABASE_URL\": \"postgresql+asyncpg://sovd_admin:${NEW_DB_PASSWORD}@${DB_ENDPOINT}/sovd_production\",
    \"DB_HOST\": \"${DB_ENDPOINT%:*}\",
    \"DB_PORT\": \"${DB_ENDPOINT#*:}\",
    \"DB_NAME\": \"sovd_production\",
    \"DB_USERNAME\": \"sovd_admin\",
    \"DB_PASSWORD\": \"${NEW_DB_PASSWORD}\"
  }" \
  --region us-east-1 \
  --force-overwrite-replica-secret

# 5. Force sync and restart pods (as shown above)
kubectl delete secret sovd-webapp-secrets -n production
kubectl wait --for=condition=Ready externalsecret/sovd-webapp-external-secrets -n production --timeout=2m
kubectl rollout restart deployment sovd-webapp-backend -n production
```

### Rotation Schedule Recommendations

- **JWT Secret**: Rotate every 90 days
- **Database Password**: Rotate every 90 days (coordinate with maintenance window)
- **Redis Password**: N/A if using encryption in-transit without passwords

---

## Troubleshooting

### ExternalSecret Not Syncing

**Symptom**: ExternalSecret status shows `SecretSyncedError` or not ready.

**Diagnosis**:

```bash
kubectl describe externalsecret sovd-webapp-external-secrets -n production
```

**Common Issues**:

1. **IAM Permission Denied**
   ```
   Error: AccessDeniedException: User is not authorized to perform: secretsmanager:GetSecretValue
   ```
   **Solution**: Verify IAM role has correct permissions and trust policy:
   ```bash
   aws iam get-role --role-name sovd-production-service-account-role
   aws iam list-attached-role-policies --role-name sovd-production-service-account-role
   ```

2. **Secret Not Found**
   ```
   Error: ResourceNotFoundException: Secrets Manager can't find the specified secret
   ```
   **Solution**: Verify secret exists in correct region:
   ```bash
   aws secretsmanager list-secrets --region us-east-1 | grep sovd/production
   ```

3. **Invalid JSON Property**
   ```
   Error: cannot find key JWT_SECRET in secret
   ```
   **Solution**: Verify secret JSON structure matches ExternalSecret property names:
   ```bash
   aws secretsmanager get-secret-value --secret-id sovd/production/jwt --region us-east-1 --query SecretString --output text | jq
   ```

4. **ServiceAccount Not Annotated**
   ```
   Error: failed to assume role
   ```
   **Solution**: Ensure ServiceAccount has correct IAM role annotation:
   ```bash
   kubectl get serviceaccount sovd-webapp-production-sa -n production -o yaml | grep role-arn
   ```

### SecretStore Not Ready

**Symptom**: SecretStore status not ready.

**Diagnosis**:

```bash
kubectl describe secretstore aws-secrets-manager -n production
```

**Common Issues**:

1. **IRSA Not Configured**
   - Verify OIDC provider exists on EKS cluster
   - Verify IAM role trust policy allows service account
   - Verify ServiceAccount annotation matches IAM role ARN

2. **External Secrets Operator Not Running**
   ```bash
   kubectl get pods -n external-secrets-system
   ```
   **Solution**: Reinstall operator if pods are not running

### Backend Pods Crashing

**Symptom**: Backend pods crash with database connection errors.

**Diagnosis**:

```bash
kubectl logs -n production -l app.kubernetes.io/component=backend --tail=100
```

**Common Issues**:

1. **DATABASE_URL Not Set**
   ```
   Error: DATABASE_URL environment variable not set
   ```
   **Solution**: Verify secret exists and is mounted:
   ```bash
   kubectl get secret sovd-webapp-secrets -n production
   BACKEND_POD=$(kubectl get pods -n production -l app.kubernetes.io/component=backend -o jsonpath='{.items[0].metadata.name}')
   kubectl exec -n production $BACKEND_POD -- env | grep DATABASE_URL
   ```

2. **Incorrect Password**
   ```
   Error: password authentication failed for user "sovd_admin"
   ```
   **Solution**: Verify RDS password matches AWS Secrets Manager secret. Update RDS password:
   ```bash
   aws secretsmanager get-secret-value --secret-id sovd/production/database --region us-east-1 --query SecretString --output text | jq -r .DB_PASSWORD
   # Use this password to update RDS
   ```

### Force Resync

If secrets are out of sync, force a complete resync:

```bash
# Delete ExternalSecret (will be recreated by Helm)
kubectl delete externalsecret sovd-webapp-external-secrets -n production

# Delete Kubernetes Secret
kubectl delete secret sovd-webapp-secrets -n production

# Trigger Helm reconciliation
helm upgrade sovd-webapp ./sovd-webapp -f ./sovd-webapp/values-production.yaml -n production

# Verify resources recreated
kubectl get externalsecret,secret -n production
```

---

## Security Best Practices

### 1. Least Privilege IAM Permissions

The IAM role should only have access to secrets for the specific environment:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:*:ACCOUNT_ID:secret:sovd/production/*"
    }
  ]
}
```

**Do NOT grant**:
- `secretsmanager:*` (wildcard permissions)
- `secretsmanager:PutSecretValue` (pods should not update secrets)
- Access to secrets outside `sovd/production/*` prefix

### 2. Audit Secret Access

Enable AWS CloudTrail logging for Secrets Manager:

```bash
# View recent secret access
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=sovd/production/database \
  --region us-east-1 \
  --max-results 50 \
  --query 'Events[*].[EventTime,Username,EventName]' \
  --output table
```

### 3. Encrypt Secrets at Rest

AWS Secrets Manager encrypts secrets at rest using AWS KMS by default. For additional security, use a customer-managed KMS key:

```bash
# Create KMS key for secrets
aws kms create-key \
  --description "SOVD production secrets encryption key" \
  --key-policy file://kms-key-policy.json \
  --region us-east-1

# Update secret to use custom KMS key
aws secretsmanager update-secret \
  --secret-id sovd/production/database \
  --kms-key-id arn:aws:kms:us-east-1:ACCOUNT_ID:key/KEY_ID \
  --region us-east-1
```

### 4. Rotate Secrets Regularly

Implement a rotation schedule:
- JWT secrets: Every 90 days
- Database passwords: Every 90 days
- Automate rotation using AWS Secrets Manager rotation features

### 5. Monitor for Unauthorized Access

Set up CloudWatch alarms for suspicious secret access patterns:

```bash
# Example: Alert on GetSecretValue calls from unknown IPs
aws cloudwatch put-metric-alarm \
  --alarm-name sovd-secrets-unauthorized-access \
  --alarm-description "Alert on unauthorized secret access" \
  --metric-name UnauthorizedSecretAccess \
  --namespace SOVD/Security \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold
```

### 6. Avoid Exposing Secrets in Logs

Never log secret values:

```bash
# BAD - exposes secret in kubectl output
kubectl get secret sovd-webapp-secrets -n production -o yaml

# GOOD - verify secret exists without exposing value
kubectl get secret sovd-webapp-secrets -n production
```

Configure application logging to redact secrets:

```python
# In backend code
import logging
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # Redact DB URLs
```

### 7. Restrict Network Access to Secrets Manager

Use VPC endpoints for Secrets Manager to keep traffic within AWS network:

```bash
# Create VPC endpoint for Secrets Manager
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-xxxxx \
  --service-name com.amazonaws.us-east-1.secretsmanager \
  --route-table-ids rtb-xxxxx \
  --region us-east-1
```

### 8. Enable Secret Versioning

Secrets Manager maintains version history. Use version IDs for rollback:

```bash
# List secret versions
aws secretsmanager list-secret-version-ids \
  --secret-id sovd/production/jwt \
  --region us-east-1

# Retrieve previous version if needed
aws secretsmanager get-secret-value \
  --secret-id sovd/production/jwt \
  --version-id PREVIOUS_VERSION_ID \
  --region us-east-1
```

### 9. Implement Secret Scanning

Use tools to detect accidentally committed secrets:

```bash
# Install git-secrets
git clone https://github.com/awslabs/git-secrets.git
cd git-secrets && make install

# Configure for SOVD repo
cd /path/to/sovd-webapp
git secrets --install
git secrets --register-aws
git secrets --add 'sovd/(production|staging)/(database|jwt|redis)'
```

### 10. Document Secret Ownership

Maintain a secret inventory:

| Secret Name | Owner | Purpose | Rotation Schedule | Last Rotated |
|------------|-------|---------|------------------|--------------|
| sovd/production/database | Platform Team | RDS connection | 90 days | 2025-10-31 |
| sovd/production/jwt | Platform Team | JWT signing | 90 days | 2025-10-31 |
| sovd/production/redis | Platform Team | Redis connection | N/A | 2025-10-31 |

---

## Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [External Secrets Operator Documentation](https://external-secrets.io/)
- [IAM Roles for Service Accounts (IRSA)](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html)
- [Infrastructure Setup Guide](./infrastructure_setup.md)
- [Terraform IAM Module](../../infrastructure/terraform/modules/iam/README.md)

---

## Support

For issues or questions:
- Check [Troubleshooting](#troubleshooting) section above
- Review External Secrets Operator logs: `kubectl logs -n external-secrets-system -l app.kubernetes.io/name=external-secrets`
- Open an issue in the SOVD WebApp repository
- Contact the Platform Team

---

**Last Updated**: 2025-10-31
**Maintained By**: Platform Team
**Related Tasks**: I5.T9 (AWS Secrets Manager Integration)
