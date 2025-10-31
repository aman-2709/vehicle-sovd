# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

**Task ID**: I5.T9
**Description**: Integrate AWS Secrets Manager. Create secrets: sovd/database/credentials (JSON), sovd/redis/password, sovd/jwt/secret. Install External Secrets Operator. Create SecretStore (points to Secrets Manager, uses IRSA). Create ExternalSecret (maps Secrets Manager → K8s Secrets). Update backend deployment to use K8s Secrets for env vars. Configure IAM role for service account (secretsmanager:GetSecretValue). Create create_aws_secrets.sh script. Document in secrets_management.md.

**Acceptance Criteria**: External Secrets Operator installed; SecretStore created, points to AWS; ExternalSecret syncs to K8s Secrets; Backend pods use K8s Secrets for DATABASE_URL, REDIS_URL, JWT_SECRET; IAM role with GetSecretValue policy; create_aws_secrets.sh creates all secrets; **Rotation: changing AWS secret updates K8s within 5min**; secrets_management.md: setup, rotation, troubleshooting; No secrets in Git

---

## Issues Detected

### 1. **IAM Role ARN Mismatch (CRITICAL)**
- **Location**: `infrastructure/helm/sovd-webapp/values-production.yaml:181`
- **Current Value**: `eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/sovd-webapp-production"`
- **Expected Value**: `eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/sovd-production-service-account-role"`
- **Issue**: The IAM role name in Terraform (`infrastructure/terraform/modules/iam/main.tf:7`) creates a role named `sovd-${environment}-service-account-role`, which for production would be `sovd-production-service-account-role`. The values-production.yaml file specifies a different role name `sovd-webapp-production`, causing a mismatch.
- **Impact**: The ServiceAccount will fail to assume the IAM role, and External Secrets Operator will not be able to fetch secrets from AWS Secrets Manager.

### 2. **ExternalSecret Refresh Interval Does Not Meet Acceptance Criteria (CRITICAL)**
- **Location**: `infrastructure/helm/sovd-webapp/templates/secrets.yaml:40`
- **Current Value**: `refreshInterval: 1h`
- **Required Value**: `refreshInterval: 5m` (or less)
- **Issue**: The acceptance criteria explicitly states: "Rotation: changing AWS secret updates K8s within 5min". The current 1-hour refresh interval means secrets will take up to 60 minutes to sync after rotation, which fails the 5-minute requirement.
- **Impact**: Secret rotation will not meet the acceptance criteria timeframe.

### 3. **Shellcheck Warnings in create_aws_secrets.sh (MINOR)**
- **Location**: `scripts/create_aws_secrets.sh:68, 90, 91, 93, 109`
- **Issue**: Shellcheck reports several minor warnings:
  - Line 68: SC2155 - Declare and assign separately to avoid masking return values
  - Lines 90, 91, 93, 109: SC2162 - read without -r will mangle backslashes
- **Impact**: These are coding style issues that don't affect functionality but reduce code quality.

---

## Best Approach to Fix

You MUST perform the following modifications:

### Fix 1: Correct IAM Role ARN in values-production.yaml

Edit `infrastructure/helm/sovd-webapp/values-production.yaml` and update line 181 from:

```yaml
eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/sovd-webapp-production"
```

To:

```yaml
eks.amazonaws.com/role-arn: "arn:aws:iam::123456789012:role/sovd-production-service-account-role"
```

This aligns with the Terraform IAM role naming convention: `sovd-${environment}-service-account-role`.

### Fix 2: Reduce ExternalSecret Refresh Interval

Edit `infrastructure/helm/sovd-webapp/templates/secrets.yaml` and change line 40 from:

```yaml
refreshInterval: 1h
```

To:

```yaml
refreshInterval: 5m
```

This ensures that AWS Secrets Manager changes propagate to Kubernetes Secrets within 5 minutes, meeting the acceptance criteria.

### Fix 3: Address Shellcheck Warnings (Optional but Recommended)

Edit `scripts/create_aws_secrets.sh` to fix the shellcheck warnings:

**Line 68** - Split declaration and assignment:
```bash
# Before
local value=$(cd "$TERRAFORM_DIR/environments/$ENVIRONMENT" && terraform output -raw "$output_name" 2>/dev/null || echo "")

# After
local value
value=$(cd "$TERRAFORM_DIR/environments/$ENVIRONMENT" && terraform output -raw "$output_name" 2>/dev/null || echo "")
```

**Lines 90, 91, 93, 109** - Add `-r` flag to read commands:
```bash
# Before
read -p "Database endpoint (host:port): " DB_ENDPOINT

# After
read -r -p "Database endpoint (host:port): " DB_ENDPOINT
```

Apply the same `-r` flag to all other `read` commands on lines 91, 93, and 109.

---

## Verification Steps

After making these changes, verify:

1. **Helm template renders correctly**:
   ```bash
   helm template sovd-webapp infrastructure/helm/sovd-webapp -f infrastructure/helm/sovd-webapp/values-production.yaml | grep -A 5 "eks.amazonaws.com/role-arn"
   ```
   Expected output should show: `arn:aws:iam::123456789012:role/sovd-production-service-account-role`

2. **ExternalSecret has correct refresh interval**:
   ```bash
   helm template sovd-webapp infrastructure/helm/sovd-webapp -f infrastructure/helm/sovd-webapp/values-production.yaml | grep refreshInterval
   ```
   Expected output should show: `refreshInterval: 5m`

3. **Script passes shellcheck**:
   ```bash
   shellcheck scripts/create_aws_secrets.sh
   ```
   Expected: No warnings or errors (or only informational messages)

4. **Script syntax is still valid**:
   ```bash
   bash -n scripts/create_aws_secrets.sh
   ```
   Expected: No output (silent success)

---

## Summary

The implementation is mostly correct but has two critical issues:

1. **IAM role ARN mismatch** - will prevent External Secrets from authenticating to AWS
2. **Refresh interval too long** - violates acceptance criteria for 5-minute secret rotation

Fix these two issues by updating the specified lines in `values-production.yaml` and `secrets.yaml`. Optionally improve the shell script quality by addressing shellcheck warnings.
