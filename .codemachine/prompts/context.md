# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T8",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Establish production database migration strategy using Alembic. Create migration workflow: 1) Developers create migrations locally using `alembic revision --autogenerate`, 2) Review generated migration for correctness (manual verification), 3) Test migration on local database (`alembic upgrade head`, verify schema, `alembic downgrade -1`, verify rollback), 4) Commit migration file to version control, 5) CI pipeline runs migration in staging environment automatically, 6) Production migration runs as Kubernetes Job before application deployment (Helm pre-upgrade hook). Implement Kubernetes Job manifest `infrastructure/helm/sovd-webapp/templates/migration-job.yaml`: runs Alembic upgrade command, uses same backend image, has access to database credentials from Secrets, runs as pre-upgrade hook (ensures migrations complete before new pods start). Create migration testing script `scripts/test_migration.sh`: applies migration, seeds test data, runs basic queries, rolls back. Document migration best practices in `docs/runbooks/database_migrations.md`: how to create migration, testing checklist, rollback procedures, handling migration conflicts.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.9 (Deployment - Database Scaling); Alembic documentation; Kubernetes Job patterns.",
  "target_files": [
    "infrastructure/helm/sovd-webapp/templates/migration-job.yaml",
    "scripts/test_migration.sh",
    "docs/runbooks/database_migrations.md",
    ".github/workflows/ci-cd.yml"
  ],
  "input_files": [
    "backend/alembic/env.py",
    "backend/alembic.ini"
  ],
  "deliverables": "Kubernetes migration Job with Helm hook; migration testing script; documentation; CI integration.",
  "acceptance_criteria": "`migration-job.yaml` defines Kubernetes Job with Alembic upgrade command; Job runs as Helm pre-upgrade hook (annotation: `\"helm.sh/hook\": pre-upgrade`); Job has access to database URL from Secret; Job uses `restartPolicy: OnFailure` and `backoffLimit: 3`; `test_migration.sh` applies latest migration, verifies schema, rolls back successfully; CI pipeline runs migration test in integration test stage; `database_migrations.md` includes: migration creation steps, testing checklist, rollback procedure, conflict resolution; Migration workflow documented: local development → staging → production; Helm upgrade in staging/production waits for migration Job to complete before deploying pods; Test migration Job in local Kubernetes cluster (minikube or kind) successfully",
  "dependencies": [
    "I1.T8",
    "I5.T2"
  ],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: deployment-strategy (from 05_Operational_Architecture.md)

```markdown
#### Deployment Strategy

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

**CI/CD Pipeline (GitHub Actions)**

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

### Context: database-schema-validation (from 03_Verification_and_Glossary.md)

```markdown
#### Database Schema Validation

**SQL DDL Scripts**
*   **Validation**: Execute SQL script against clean PostgreSQL instance, verify no errors
*   **Tool**: psql or pgAdmin
*   **Execution**: `scripts/init_db.sh` runs DDL, reports errors
*   **Acceptance**: All tables, indexes, constraints created successfully

**Alembic Migrations**
*   **Validation**: Migration applies (`alembic upgrade head`) and rolls back (`alembic downgrade -1`) without errors
*   **Execution**: CI pipeline runs migration tests in integration stage
*   **Acceptance**: Schema after migration matches expected state, no data loss on rollback
```

### Context: continuous-deployment (from 03_Verification_and_Glossary.md)

```markdown
#### Continuous Deployment

**Staging Environment**
*   **Trigger**: Automatic on merge to develop branch
*   **Target**: Kubernetes staging namespace
*   **Database**: Shared staging RDS instance (separate from production)
*   **Secrets**: AWS Secrets Manager staging secrets
*   **Monitoring**: Prometheus/Grafana available for debugging

**Production Environment**
*   **Trigger**: Manual approval after merge to main branch
*   **Target**: Kubernetes production namespace
*   **Deployment Strategy**: Rolling update (zero-downtime) or canary (gradual rollout)
*   **Database Migrations**: Automated via Kubernetes Job (Helm pre-upgrade hook)
*   **Smoke Tests**: Automated health checks, sample API calls
*   **Rollback**: Automatic on smoke test failure, manual via `helm rollback` if needed
*   **Monitoring**: Real-time alerts on error rate, response time anomalies
```

### Context: task-i5-t8 (from 02_Iteration_I5.md)

```markdown
*   **Task 5.8: Implement Database Migration Strategy for Production**
    *   **Task ID:** `I5.T8`
    *   **Description:** Establish production database migration strategy using Alembic. Create migration workflow: 1) Developers create migrations locally using `alembic revision --autogenerate`, 2) Review generated migration for correctness (manual verification), 3) Test migration on local database (`alembic upgrade head`, verify schema, `alembic downgrade -1`, verify rollback), 4) Commit migration file to version control, 5) CI pipeline runs migration in staging environment automatically, 6) Production migration runs as Kubernetes Job before application deployment (Helm pre-upgrade hook). Implement Kubernetes Job manifest `infrastructure/helm/sovd-webapp/templates/migration-job.yaml`: runs Alembic upgrade command, uses same backend image, has access to database credentials from Secrets, runs as pre-upgrade hook (ensures migrations complete before new pods start). Create migration testing script `scripts/test_migration.sh`: applies migration, seeds test data, runs basic queries, rolls back. Document migration best practices in `docs/runbooks/database_migrations.md`: how to create migration, testing checklist, rollback procedures, handling migration conflicts.
    *   **Agent Type Hint:** `BackendAgent` or `DatabaseAgent`
    *   **Inputs:** Architecture Blueprint Section 3.9 (Deployment - Database Scaling); Alembic documentation; Kubernetes Job patterns.
    *   **Input Files:** [`backend/alembic/env.py`, `backend/alembic.ini`]
    *   **Target Files:**
        *   `infrastructure/helm/sovd-webapp/templates/migration-job.yaml`
        *   `scripts/test_migration.sh`
        *   `docs/runbooks/database_migrations.md`
        *   Updates to `.github/workflows/ci-cd.yml` (add migration testing step)
    *   **Deliverables:** Kubernetes migration Job with Helm hook; migration testing script; documentation; CI integration.
    *   **Acceptance Criteria:**
        *   `migration-job.yaml` defines Kubernetes Job with Alembic upgrade command
        *   Job runs as Helm pre-upgrade hook (annotation: `"helm.sh/hook": pre-upgrade`)
        *   Job has access to database URL from Secret
        *   Job uses `restartPolicy: OnFailure` and `backoffLimit: 3`
        *   `test_migration.sh` applies latest migration, verifies schema, rolls back successfully
        *   CI pipeline runs migration test in integration test stage
        *   `database_migrations.md` includes: migration creation steps, testing checklist, rollback procedure, conflict resolution
        *   Migration workflow documented: local development → staging → production
        *   Helm upgrade in staging/production waits for migration Job to complete before deploying pods
        *   Test migration Job in local Kubernetes cluster (minikube or kind) successfully
    *   **Dependencies:** `I1.T8` (Alembic setup), `I5.T2` (Helm chart)
    *   **Parallelizable:** Yes (database operations independent of app features)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/alembic/env.py`
    *   **Summary:** This file configures Alembic to work with SQLAlchemy 2.0's async engine using asyncpg driver. It reads the DATABASE_URL from environment variables and supports both offline (SQL generation) and online (database execution) migration modes.
    *   **Recommendation:** Your Kubernetes Job MUST set the `DATABASE_URL` environment variable in the exact same format that this file expects: `postgresql+asyncpg://user:pass@host:port/database`. The env.py file reads from `os.getenv("DATABASE_URL")` on line 40.
    *   **Key Implementation Detail:** The env.py uses `asyncio.run(run_async_migrations())` for online migrations and `async_engine_from_config()` with `NullPool` to avoid connection pooling during migrations. Your Job will execute `alembic upgrade head` which will invoke this logic.

*   **File:** `backend/alembic.ini`
    *   **Summary:** Standard Alembic configuration with script location, logging, and post-write hooks for black and ruff formatting.
    *   **Recommendation:** The Job MUST run with the working directory set to `/app` (the backend directory) so that Alembic can find this .ini file at the default location.
    *   **Key Configuration:** `script_location = %(here)s/alembic` and `prepend_sys_path = .` mean Alembic expects to run from the backend root with the alembic/ directory present.

*   **File:** `infrastructure/helm/sovd-webapp/templates/backend-deployment.yaml`
    *   **Summary:** The main backend deployment template that defines how pods are deployed, including environment variables, secrets, and health checks.
    *   **Recommendation:** Your migration Job MUST use the same database connection pattern. Notice lines 52-58 show how to inject DATABASE_PASSWORD from Secrets and construct DATABASE_URL using the helper function.
    *   **Key Pattern to Reuse:**
        ```yaml
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: {{ include "sovd-webapp.fullname" . }}-secrets
              key: database-password
        - name: DATABASE_URL
          value: {{ include "sovd-webapp.databaseUrl" . | quote }}
        ```
    *   **CRITICAL:** The backend image is referenced using `{{ include "sovd-webapp.backend.image" . }}` helper function. You MUST use the same image for the migration Job.

*   **File:** `infrastructure/helm/sovd-webapp/templates/_helpers.tpl`
    *   **Summary:** Contains Helm template helper functions for generating names, labels, and configuration values.
    *   **Recommendation:** You MUST use these helpers in your migration-job.yaml:
        - `{{ include "sovd-webapp.fullname" . }}-migration` for the Job name
        - `{{ include "sovd-webapp.backend.image" . }}` for the container image
        - `{{ include "sovd-webapp.databaseUrl" . }}` for constructing the DATABASE_URL
        - `{{ include "sovd-webapp.labels" . }}` for standard labels
    *   **Critical Helper Functions:**
        - Line 54-58: `sovd-webapp.backend.labels` - Use this for consistent labeling
        - The databaseUrl helper: `postgresql+asyncpg://%s:$(DATABASE_PASSWORD)@%s:%s/%s` with values from .Values.config.database

*   **File:** `backend/alembic/versions/001_initial_schema.py`
    *   **Summary:** The initial database migration that creates all tables, indexes, and constraints.
    *   **Recommendation:** Your test script (`test_migration.sh`) can verify this migration by checking that tables exist after upgrade and are removed after downgrade.
    *   **Testing Strategy:** Use `psql` commands to query `information_schema.tables` to verify the migration worked.

*   **File:** `infrastructure/helm/sovd-webapp/values.yaml`
    *   **Summary:** Default Helm values including database configuration, resource limits, and deployment settings.
    *   **Recommendation:** The database configuration is in `.Values.config.database` with fields: host, port, name, user. Your Job template should use these same values.
    *   **Resource Requirements:** Notice backend pods request `memory: 256Mi, cpu: 250m`. Your migration Job should use similar or slightly lower resources since it's a one-time task.

*   **File:** `backend/Dockerfile.prod`
    *   **Summary:** Multi-stage production Dockerfile that builds a minimal Python 3.11 image with non-root user execution.
    *   **Recommendation:** Your migration Job will use this same image. The working directory in the image is `/app`, and the non-root user is `appuser` (UID 1001).
    *   **CRITICAL:** The Job must run as the same user (runAsUser: 1001) and have the PYTHONPATH set to /app. The image already has all dependencies including Alembic installed.

*   **File:** `.github/workflows/ci-cd.yml`
    *   **Summary:** Existing CI/CD pipeline with jobs for linting, testing, building, and deployment.
    *   **Recommendation:** You need to add a new job or step to run migration tests. Based on the existing structure, add it in the integration test section (after unit tests, before E2E tests).
    *   **Existing Pattern:** Jobs use `working-directory: ./backend` and run commands like `pytest`. You should add a step that runs `bash scripts/test_migration.sh` in a similar pattern.

*   **File:** `infrastructure/helm/sovd-webapp/templates/secrets.yaml`
    *   **Summary:** Defines how secrets are managed, with support for both static values and External Secrets Operator.
    *   **Recommendation:** Your Job MUST reference the same secret name: `{{ include "sovd-webapp.fullname" . }}-secrets` and the same key `database-password`.
    *   **Note:** The file shows the pattern for future External Secrets integration (lines 29-60), but for now, your Job will use the basic Kubernetes Secret approach (lines 1-28).

### Implementation Tips & Notes

*   **Tip:** Kubernetes Jobs with Helm pre-upgrade hooks MUST include these specific annotations:
    ```yaml
    annotations:
      "helm.sh/hook": pre-upgrade
      "helm.sh/hook-weight": "-5"
      "helm.sh/hook-delete-policy": before-hook-creation
    ```
    The `hook-weight` ensures the migration runs before other pre-upgrade hooks, and `hook-delete-policy` ensures old Job pods are cleaned up.

*   **Tip:** The migration Job should use `restartPolicy: OnFailure` and `backoffLimit: 3` as specified in acceptance criteria. This allows retries for transient database connection failures but eventually fails the deployment if the migration truly cannot succeed.

*   **Tip:** Your `test_migration.sh` script should:
    1. Set `DATABASE_URL` environment variable (read from env or use default localhost)
    2. Run `alembic upgrade head`
    3. Use `psql` to verify tables exist (query `pg_tables` or count tables)
    4. Run `alembic downgrade -1`
    5. Verify tables are removed (for the initial migration, all should be gone after downgrade base)
    6. Exit with non-zero code if any step fails

*   **Warning:** Alembic requires write access to the alembic/versions/ directory to create new migrations, but the migration Job only needs READ access since it's just running existing migrations. However, the production Docker image uses `readOnlyRootFilesystem: false` in the backend-deployment.yaml (line 81), so this shouldn't be an issue.

*   **Note:** The CI pipeline integration should run the migration test in the existing "Backend Integration Tests" job or create a new "Migration Tests" job that runs between unit tests and E2E tests. It should use the same docker-compose setup that's likely used for integration tests.

*   **Note:** For the runbook documentation (`database_migrations.md`), structure it with these sections:
    1. **Overview** - Brief description of the migration strategy
    2. **Creating Migrations** - Step-by-step guide using `alembic revision --autogenerate`
    3. **Testing Migrations Locally** - Using `test_migration.sh` and manual verification
    4. **Testing in Staging** - How CI automatically tests migrations
    5. **Production Deployment** - How Helm pre-upgrade hook works
    6. **Rollback Procedures** - Using `alembic downgrade` and `helm rollback`
    7. **Troubleshooting** - Common issues (connection failures, migration conflicts, data migration errors)
    8. **Migration Conflicts** - How to resolve when multiple developers create migrations simultaneously

*   **Critical Security Note:** Never commit the actual DATABASE_URL with credentials to Git. The Job template should construct it from Secret values, and the test script should read from environment variables with safe defaults for local testing.

*   **Compatibility Note:** The Alembic env.py uses SQLAlchemy 2.0 async patterns with `asyncio.run()`. Make sure your documentation mentions that all migrations must be compatible with async SQLAlchemy and that developers should test both upgrade and downgrade paths.

*   **Performance Note:** Database migrations can take time, especially with large datasets. The Helm hook mechanism will wait for the Job to complete before proceeding with the deployment. Consider adding a `activeDeadlineSeconds: 600` (10 minutes) to the Job spec to prevent hanging indefinitely if a migration gets stuck.

*   **Tip:** For the CI integration, add a step in the existing "backend-integration" job (or create a new "migration-test" job). The step should:
    1. Start docker-compose services (db and redis)
    2. Wait for database to be ready
    3. Run `scripts/test_migration.sh`
    4. Capture exit code and fail the job if migration test fails
    5. Stop docker-compose services

*   **Best Practice:** The migration Job should have appropriate resource limits to prevent runaway migrations from consuming all cluster resources:
    ```yaml
    resources:
      requests:
        memory: "128Mi"
        cpu: "100m"
      limits:
        memory: "256Mi"
        cpu: "250m"
    ```

*   **Best Practice:** Include detailed logging in the migration Job by setting environment variable `PYTHONUNBUFFERED=1` to ensure Python output is not buffered and appears in real-time in `kubectl logs`.

---

## Final Recommendations for the Coder Agent

1. **Start with migration-job.yaml:** This is the core deliverable. Model it closely after backend-deployment.yaml but as a Job resource instead of Deployment.

2. **Use Helm helpers consistently:** Don't hardcode values - use the existing helper functions for names, images, and URLs.

3. **Test locally first:** Before relying on Kubernetes, create the test_migration.sh script and verify it works with docker-compose locally.

4. **Documentation is critical:** The database_migrations.md runbook will be the primary reference for developers. Make it detailed, clear, and include examples.

5. **CI integration last:** Add the CI step after you've verified the test script works locally. This ensures the CI job won't fail unnecessarily.

6. **Consider edge cases:** What happens if a migration fails halfway? What if the database is locked? Document these scenarios in the troubleshooting section.

7. **Version compatibility:** Ensure the migration strategy works with the existing Alembic setup (I1.T8) and doesn't require changes to env.py or alembic.ini.

8. **Security first:** Never expose database credentials. Always use Secret references and environment variable substitution.

9. **Idempotency:** Alembic migrations are naturally idempotent (running `alembic upgrade head` multiple times is safe), but document this behavior.

10. **Testing the Job:** The acceptance criteria require testing in local Kubernetes (minikube/kind). Include a section in the runbook explaining how to test the Helm hook locally before deploying to staging/production.
