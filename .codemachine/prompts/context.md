# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T9",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Integrate AWS Secrets Manager. Create secrets: sovd/database/credentials (JSON), sovd/redis/password, sovd/jwt/secret. Install External Secrets Operator. Create SecretStore (points to Secrets Manager, uses IRSA). Create ExternalSecret (maps Secrets Manager → K8s Secrets). Update backend deployment to use K8s Secrets for env vars. Configure IAM role for service account (secretsmanager:GetSecretValue). Create create_aws_secrets.sh script. Document in secrets_management.md.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8; External Secrets Operator docs.",
  "target_files": [
    "infrastructure/helm/sovd-webapp/templates/secretstore.yaml",
    "infrastructure/helm/sovd-webapp/templates/externalsecret.yaml",
    "infrastructure/helm/sovd-webapp/templates/backend-deployment.yaml",
    "scripts/create_aws_secrets.sh",
    "docs/runbooks/secrets_management.md"
  ],
  "input_files": [],
  "deliverables": "External Secrets integration; SecretStore/ExternalSecret; IAM role; secrets script; documentation.",
  "acceptance_criteria": "External Secrets Operator installed; SecretStore created, points to AWS; ExternalSecret syncs to K8s Secrets; Backend pods use K8s Secrets for DATABASE_URL, REDIS_URL, JWT_SECRET; IAM role with GetSecretValue policy; create_aws_secrets.sh creates all secrets; Rotation: changing AWS secret updates K8s within 5min; secrets_management.md: setup, rotation, troubleshooting; No secrets in Git",
  "dependencies": [
    "I5.T2",
    "I5.T7"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: AWS Secrets Manager Integration (from infrastructure_setup.md)

The infrastructure setup guide already documents the complete flow for creating AWS Secrets Manager secrets and configuring External Secrets Operator. Key points:

**AWS Secrets Created:**
1. `sovd/production/database` - Contains JSON with DATABASE_URL
2. `sovd/production/jwt` - Contains JSON with JWT_SECRET
3. `sovd/production/redis` - Contains JSON with REDIS_URL

**External Secrets Operator Installation:**
```bash
helm repo add external-secrets https://charts.external-secrets.io
helm repo update

helm install external-secrets \
  external-secrets/external-secrets \
  -n external-secrets-system \
  --create-namespace \
  --set installCRDs=true
```

**SecretStore Configuration:**
- Uses IAM Roles for Service Accounts (IRSA)
- Points to AWS Secrets Manager in us-east-1 region
- Service account: `sovd-webapp-production-sa`
- Namespace: `production`

**ExternalSecret Configuration:**
- Refresh interval: 1 hour
- Maps AWS Secrets Manager keys to Kubernetes Secret keys
- Creation policy: Owner
- Target secret names defined per resource (database-secret, jwt-secret, redis-secret)

### Context: IAM Role Configuration (from iam/main.tf)

The Terraform IAM module already creates the service account role with Secrets Manager permissions:

**IAM Role:**
- Name: `sovd-{environment}-service-account-role`
- Trust policy: Allows OIDC provider (EKS) to assume role
- Condition: Only service account `sovd-webapp-{environment}-sa` in namespace `{environment}`

**Secrets Manager Policy:**
- Policy name: `sovd-{environment}-secrets-manager-access`
- Permissions: `secretsmanager:GetSecretValue`, `secretsmanager:DescribeSecret`
- Resource scope: `arn:aws:secretsmanager:*:{account_id}:secret:sovd/{environment}/*`

**IMPORTANT:** The IAM role is already created by Terraform (task I5.T7). You do NOT need to create it again.

### Context: Helm Chart Structure (from values.yaml)

The Helm chart has placeholders for External Secrets integration:

**External Secrets Configuration (values.yaml):**
```yaml
externalSecrets:
  enabled: false  # Default disabled
  secretStoreName: "aws-secrets-manager"
  databaseSecretKey: "sovd/production/database"
  jwtSecretKey: "sovd/production/jwt"
  redisSecretKey: "sovd/production/redis"
```

**Existing Secrets Template (secrets.yaml):**
- Currently uses static base64 placeholders
- Has conditional block for ExternalSecret (lines 29-60)
- Already defines ExternalSecret spec with remoteRef mappings
- Maps to secret keys: `database-password`, `jwt-secret`, `redis-password`

### Context: Backend Deployment Environment Variables (from backend-deployment.yaml)

The backend deployment currently loads secrets from Kubernetes Secrets:

**Current Configuration:**
- DATABASE_PASSWORD from secret key `database-password`
- JWT_SECRET from secret key `jwt-secret`
- REDIS_PASSWORD from secret key `redis-password` (optional)
- DATABASE_URL and REDIS_URL are constructed using helpers with password injected

**CRITICAL ISSUE:** The ExternalSecret in secrets.yaml maps AWS Secrets Manager properties to K8s secret keys, but the property names don't match the secret structure documented in infrastructure_setup.md.

**Current mapping (secrets.yaml):**
```yaml
- secretKey: database-password
  remoteRef:
    key: sovd/production/database
    property: password  # ❌ Should be DATABASE_URL or the password field from JSON
```

**Expected AWS Secret Structure (infrastructure_setup.md):**
```json
{
  "DATABASE_URL": "postgresql://user:pass@host:port/db"
}
```

**You MUST align these structures.**

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `infrastructure/helm/sovd-webapp/templates/secrets.yaml`
    *   **Summary:** This file already contains a partial ExternalSecret implementation (lines 29-60) that is conditionally enabled when `externalSecrets.enabled` is true.
    *   **Recommendation:** You SHOULD update this existing file rather than creating a new `externalsecret.yaml`. The ExternalSecret is already defined here but needs corrections to the property mappings.
    *   **Critical Issue:** The `property` fields in the remoteRef sections (lines 51, 55, 59) do not match the secret structure created by `infrastructure_setup.md`. Update them to match the JSON structure.

*   **File:** `infrastructure/helm/sovd-webapp/templates/backend-deployment.yaml`
    *   **Summary:** This file defines the backend Deployment and already references secrets from Kubernetes Secrets (lines 52-76).
    *   **Recommendation:** You MUST modify this file to simplify environment variable loading. Instead of constructing DATABASE_URL and REDIS_URL using helpers and password injection, load them directly from the K8s Secret as complete URLs (since ExternalSecret will sync complete URLs from AWS Secrets Manager).
    *   **Current Pattern (lines 52-69):** Loads `DATABASE_PASSWORD` from secret, then constructs URL using helper. This is overly complex when ExternalSecret can provide the complete URL.
    *   **New Pattern:** Load `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET` directly from secret keys without URL construction.

*   **File:** `infrastructure/helm/sovd-webapp/values.yaml`
    *   **Summary:** Contains the `externalSecrets` configuration block (lines 370-378) with default values.
    *   **Recommendation:** You SHOULD create a `values-production.yaml` file that sets `externalSecrets.enabled: true` and configures the secret keys for production environment. Do NOT modify the default values.yaml for this.

*   **File:** `infrastructure/terraform/modules/iam/main.tf`
    *   **Summary:** Defines the IAM role and Secrets Manager policy for IRSA. This is already provisioned by task I5.T7.
    *   **Recommendation:** You MUST reference the existing IAM role ARN (output from Terraform) in the ServiceAccount annotation. DO NOT create a new IAM role. The role ARN should be: `arn:aws:iam::{account_id}:role/sovd-{environment}-service-account-role`.

*   **File:** `docs/runbooks/infrastructure_setup.md`
    *   **Summary:** Comprehensive guide for infrastructure provisioning, including detailed steps for creating AWS secrets and installing External Secrets Operator.
    *   **Recommendation:** You SHOULD reference this guide when writing `secrets_management.md`. Many procedures are already documented here. Your new runbook should focus specifically on secrets management operations (creation, rotation, troubleshooting) without duplicating infrastructure setup content.

*   **File:** `backend/app/config.py`
    *   **Summary:** Pydantic Settings class that loads configuration from environment variables. It expects `DATABASE_URL`, `REDIS_URL`, and `JWT_SECRET` as environment variables.
    *   **Recommendation:** Your ExternalSecret configuration MUST populate these exact environment variable names. The backend code expects these specific names and will not work with different variable names.

*   **File:** `infrastructure/helm/sovd-webapp/templates/_helpers.tpl`
    *   **Summary:** Contains Helm helper functions for generating database URLs and other configuration.
    *   **Recommendation:** The `sovd-webapp.databaseUrl` helper is currently used to construct DATABASE_URL from components. When using ExternalSecret, you will NO LONGER need this helper for DATABASE_URL construction. However, keep the helper for backwards compatibility with non-ExternalSecret deployments.

### Implementation Tips & Notes

*   **Tip:** The `secretstore.yaml` template does NOT currently exist. You MUST create it from scratch. However, there is a detailed example in `infrastructure_setup.md` (lines 465-537) that you can use as a reference.

*   **Tip:** The ExternalSecret already exists in `secrets.yaml` but is incomplete. Focus on fixing the `property` mappings in the `remoteRef` sections to match the actual AWS secret structure.

*   **Note:** The AWS Secrets Manager secrets store JSON objects, but the secret keys in Kubernetes need to be extracted from specific JSON properties. Use the `property` field in ExternalSecret to extract the correct field.

*   **Warning:** The current ExternalSecret configuration maps all secrets to a single Kubernetes Secret (`{{ include "sovd-webapp.fullname" . }}-secrets`). This means you cannot have separate ExternalSecret resources for database, JWT, and Redis secrets - they all must merge into one K8s Secret. This is correct and matches the backend deployment expectations.

*   **Critical:** When creating `create_aws_secrets.sh`, you MUST follow the exact secret structure documented in `infrastructure_setup.md` (lines 438-458). The script should:
  - Create `sovd/{environment}/database` with JSON: `{"DATABASE_URL": "postgresql://..."}`
  - Create `sovd/{environment}/jwt` with JSON: `{"JWT_SECRET": "..."}`
  - Create `sovd/{environment}/redis` with JSON: `{"REDIS_URL": "redis://..."}`

*   **Best Practice:** The `create_aws_secrets.sh` script should:
  1. Accept environment as a parameter (production, staging)
  2. Read credentials from Terraform outputs where possible
  3. Generate secure random values for JWT_SECRET
  4. Include error handling for existing secrets
  5. Provide clear output messages

*   **Security:** Ensure the script uses `--force-overwrite-replica-secret` flag when updating existing secrets to handle rotation scenarios.

*   **Testing Approach:** Document in `secrets_management.md` how to verify the ExternalSecret sync:
  ```bash
  kubectl get externalsecrets -n production
  kubectl describe externalsecret {name} -n production
  kubectl get secret {name} -n production -o yaml
  ```

*   **Secret Rotation:** The ExternalSecret refreshInterval is set to 1 hour. Document that secret rotation requires updating the AWS Secrets Manager secret, then waiting up to 1 hour for automatic sync (or forcing sync by deleting the K8s Secret).

*   **Namespace Considerations:** The SecretStore and ExternalSecret must be created in the same namespace as the application (`production`). The ServiceAccount annotation for IRSA must match the namespace in the IAM role trust policy.

### Secret Structure Alignment - CRITICAL

**You MUST ensure these structures align:**

**AWS Secrets Manager (created by script):**
```json
// sovd/production/database
{
  "DATABASE_URL": "postgresql://sovd_admin:password@rds-endpoint:5432/sovd_production"
}

// sovd/production/jwt
{
  "JWT_SECRET": "generated-random-secret"
}

// sovd/production/redis
{
  "REDIS_URL": "redis://redis-endpoint:6379"
}
```

**ExternalSecret mapping (in secrets.yaml):**
```yaml
data:
  - secretKey: database-url  # Maps to DATABASE_URL env var
    remoteRef:
      key: sovd/production/database
      property: DATABASE_URL  # Extract DATABASE_URL from JSON

  - secretKey: jwt-secret  # Maps to JWT_SECRET env var
    remoteRef:
      key: sovd/production/jwt
      property: JWT_SECRET

  - secretKey: redis-url  # Maps to REDIS_URL env var
    remoteRef:
      key: sovd/production/redis
      property: REDIS_URL
```

**Backend deployment usage (MUST UPDATE):**
```yaml
env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: sovd-webapp-secrets
        key: database-url

  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: sovd-webapp-secrets
        key: jwt-secret

  - name: REDIS_URL
    valueFrom:
      secretKeyRef:
        name: sovd-webapp-secrets
        key: redis-url
```

**CRITICAL:** You MUST update backend-deployment.yaml to use the new secret keys (`database-url`, `jwt-secret`, `redis-url`) instead of the old pattern (loading `database-password` and constructing URL with helper). The ExternalSecret provides complete URLs, not individual password components.

### Documentation Structure for secrets_management.md

Your documentation should include:

1. **Overview** - Purpose of secrets management with AWS Secrets Manager
2. **Architecture** - Diagram/explanation of External Secrets Operator flow
3. **Prerequisites** - Terraform outputs, AWS CLI, kubectl, helm
4. **Initial Setup** - Installing External Secrets Operator (reference infrastructure_setup.md)
5. **Creating Secrets** - Using create_aws_secrets.sh script
6. **Configuring External Secrets** - SecretStore and ExternalSecret setup
7. **Verification** - How to verify secrets are syncing correctly
8. **Secret Rotation** - How to rotate secrets and force sync
9. **Troubleshooting** - Common issues (IRSA permissions, sync failures, etc.)
10. **Security Best Practices** - Least privilege, audit logging, encryption

### Files You Should NOT Modify

- `infrastructure/terraform/modules/iam/main.tf` - IAM role already exists (from I5.T7)
- `backend/app/config.py` - Already expects correct environment variables
- `infrastructure/helm/sovd-webapp/values.yaml` - Only create values-production.yaml overlay
- `infrastructure/helm/sovd-webapp/templates/_helpers.tpl` - Keep database URL helper for backwards compatibility

### Files You MUST Create

1. `infrastructure/helm/sovd-webapp/templates/secretstore.yaml` - New file
2. `scripts/create_aws_secrets.sh` - New file
3. `docs/runbooks/secrets_management.md` - New file
4. `infrastructure/helm/sovd-webapp/values-production.yaml` - New file (enable externalSecrets)

### Files You MUST Modify

1. `infrastructure/helm/sovd-webapp/templates/secrets.yaml` - Fix ExternalSecret property mappings (lines 47-59)
2. `infrastructure/helm/sovd-webapp/templates/backend-deployment.yaml` - Update env vars to load complete URLs from secrets (lines 51-80)

---

## Strategic Execution Plan

**Phase 1: Create SecretStore Template**
- Create new file `templates/secretstore.yaml`
- Use IRSA authentication with service account reference
- Set AWS region to us-east-1
- Conditionally enable based on `externalSecrets.enabled` flag

**Phase 2: Fix ExternalSecret Configuration**
- Update `templates/secrets.yaml` ExternalSecret block (lines 29-60)
- Correct property mappings to match AWS secret JSON structure
- Change secret keys to: `database-url`, `jwt-secret`, `redis-url`
- Ensure target secret name matches backend deployment expectations
- Set 1 hour refresh interval

**Phase 3: Update Backend Deployment**
- Modify `backend-deployment.yaml` environment variable section (lines 51-80)
- Remove DATABASE_PASSWORD loading and URL construction
- Add direct loading of DATABASE_URL, REDIS_URL from secret keys
- Keep JWT_SECRET loading pattern (already correct)
- Remove dependency on databaseUrl and redisUrl helpers

**Phase 4: Create AWS Secrets Script**
- Write `scripts/create_aws_secrets.sh`
- Accept environment parameter (production/staging)
- Extract RDS/Redis endpoints from Terraform outputs
- Generate secure random JWT secret (openssl rand -base64 32)
- Create all three AWS Secrets Manager secrets with correct JSON structure
- Include error handling and --force-overwrite-replica-secret for updates
- Provide clear output messages

**Phase 5: Create Production Values Override**
- Create `values-production.yaml`
- Enable External Secrets (`externalSecrets.enabled: true`)
- Configure correct secret keys for production
- Set service account annotation with IAM role ARN placeholder (to be filled from Terraform output)
- Override other production-specific values if needed

**Phase 6: Documentation**
- Create comprehensive `secrets_management.md` runbook
- Include setup, verification, rotation, and troubleshooting procedures
- Reference infrastructure_setup.md where appropriate
- Add security best practices section
- Include examples of verifying ExternalSecret sync

---

## Validation Checklist

Before marking the task complete, verify:

- [ ] `helm template` command renders SecretStore and ExternalSecret without errors
- [ ] SecretStore points to AWS Secrets Manager with correct region (us-east-1)
- [ ] ExternalSecret property mappings match AWS secret JSON structure exactly
- [ ] Backend deployment loads DATABASE_URL, REDIS_URL, JWT_SECRET directly from secrets
- [ ] No URL construction helpers used for database/redis (simplified approach)
- [ ] `create_aws_secrets.sh` creates all three secrets with correct JSON structure
- [ ] Script accepts environment parameter and reads from Terraform outputs
- [ ] Script generates secure random JWT_SECRET
- [ ] Documentation includes all required sections (10 sections listed above)
- [ ] No secrets are hardcoded in Git (all use placeholders or references)
- [ ] ServiceAccount annotation includes correct IAM role ARN reference pattern
- [ ] values-production.yaml enables externalSecrets and configures properly
- [ ] All acceptance criteria from task specification are met

---

## Additional Context: ServiceAccount Configuration

**IMPORTANT:** The ServiceAccount for the backend deployment MUST have the IRSA annotation to assume the IAM role:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sovd-webapp-production-sa
  namespace: production
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::ACCOUNT_ID:role/sovd-production-service-account-role
```

This annotation is what allows the SecretStore to authenticate to AWS Secrets Manager using IRSA. Verify that:
1. The ServiceAccount is created by Helm (check `_helpers.tpl` for serviceAccountName reference)
2. The annotation is added in values-production.yaml under `serviceAccount.annotations`
3. The IAM role ARN matches the Terraform output from task I5.T7
