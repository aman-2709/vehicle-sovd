# Database Migrations Runbook

## Overview

This runbook provides comprehensive guidance for managing database schema changes in the SOVD Command WebApp using Alembic migrations. The migration strategy ensures zero-downtime deployments and maintains database consistency across all environments (local, staging, production).

### Migration Strategy Summary

1. **Local Development**: Developers create and test migrations on local database
2. **Version Control**: Migration files committed to Git after validation
3. **CI Pipeline**: Automated migration tests run in staging environment
4. **Production**: Kubernetes Job executes migrations before application deployment (Helm pre-upgrade hook)

### Key Principles

- **Always test migrations locally** before committing
- **Always test both upgrade AND downgrade** paths
- **Never modify existing migration files** (create new ones instead)
- **Never skip migrations** in sequence
- **Always backup production database** before major migrations

---

## Prerequisites

### Local Development Environment

- PostgreSQL 15+ installed and running
- Python 3.11+ with virtual environment activated
- Alembic configured (see `backend/alembic/env.py` and `backend/alembic.ini`)
- Database connection: `postgresql+asyncpg://sovd_user:sovd_pass@localhost:5432/sovd`

### Required Tools

```bash
# Python dependencies (already in requirements.txt)
pip install alembic sqlalchemy asyncpg psycopg2-binary

# PostgreSQL client tools
sudo apt-get install postgresql-client  # Ubuntu/Debian
brew install libpq                       # macOS
```

### Environment Variables

```bash
# Required for all Alembic commands
export DATABASE_URL="postgresql+asyncpg://user:password@host:port/database"

# Example for local development
export DATABASE_URL="postgresql+asyncpg://sovd_user:sovd_pass@localhost:5432/sovd"

# Example for staging
export DATABASE_URL="postgresql+asyncpg://sovd_user:password@staging-rds.amazonaws.com:5432/sovd"
```

---

## Creating Migrations

### Step 1: Ensure Clean State

Before creating a new migration, ensure your local database is at the latest migration:

```bash
cd backend/

# Check current migration revision
alembic current

# Apply latest migrations if needed
alembic upgrade head
```

### Step 2: Modify SQLAlchemy Models

Edit models in `backend/app/models/` to reflect schema changes:

```python
# Example: Adding a new column to vehicles table
# File: backend/app/models/vehicle.py

class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vin = Column(String(17), unique=True, nullable=False, index=True)
    license_plate = Column(String(20), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # NEW COLUMN
    manufacturer = Column(String(50), nullable=True)  # New field
```

### Step 3: Generate Migration

Use Alembic's autogenerate feature to create the migration:

```bash
cd backend/

# Generate migration with descriptive message
alembic revision --autogenerate -m "Add manufacturer column to vehicles table"

# Output will show:
#   Generating /path/to/backend/alembic/versions/abc123_add_manufacturer_column_to_vehicles_table.py
```

### Step 4: Review Generated Migration

**CRITICAL**: Always manually review the generated migration file:

```bash
# Open the generated file
vim alembic/versions/abc123_add_manufacturer_column_to_vehicles_table.py
```

**Check for**:
- Correct table and column names
- Appropriate data types
- Proper nullable/default values
- Index creation (if needed)
- Foreign key constraints
- Data migrations (if needed)

**Example migration file**:

```python
"""Add manufacturer column to vehicles table

Revision ID: abc123
Revises: xyz789
Create Date: 2025-10-31 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123'
down_revision = 'xyz789'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add manufacturer column
    op.add_column('vehicles',
        sa.Column('manufacturer', sa.String(length=50), nullable=True)
    )

def downgrade() -> None:
    # Remove manufacturer column
    op.drop_column('vehicles', 'manufacturer')
```

### Step 5: Test Migration Locally

Use the provided test script to validate the migration:

```bash
# Run comprehensive migration test
./scripts/test_migration.sh

# Or manually test
cd backend/

# Apply migration
alembic upgrade head

# Verify schema in database
psql -U sovd_user -d sovd -c "\d vehicles"

# Test downgrade
alembic downgrade -1

# Verify rollback
psql -U sovd_user -d sovd -c "\d vehicles"

# Re-apply for clean state
alembic upgrade head
```

### Step 6: Commit Migration to Version Control

After successful testing, commit the migration file:

```bash
git add backend/alembic/versions/abc123_add_manufacturer_column_to_vehicles_table.py
git commit -m "feat(db): add manufacturer column to vehicles table"
git push origin feature/add-vehicle-manufacturer
```

---

## Testing Migrations

### Automated Testing with test_migration.sh

The `scripts/test_migration.sh` script performs comprehensive migration validation:

```bash
# Test with default local database
./scripts/test_migration.sh

# Test with custom database URL
./scripts/test_migration.sh "postgresql+asyncpg://user:pass@host:5432/db"

# Test with environment variable
export DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/db"
./scripts/test_migration.sh
```

**What the script tests**:
1. Database connectivity
2. Current migration state
3. Migration upgrade (`alembic upgrade head`)
4. Schema verification (checks expected tables exist)
5. Test data insertion and verification
6. Migration rollback (`alembic downgrade -1`)
7. Rollback verification (tables removed/modified correctly)
8. Re-application of migration

### Manual Testing Checklist

- [ ] Migration applies without errors
- [ ] All expected tables/columns created
- [ ] Indexes created correctly
- [ ] Foreign keys enforced properly
- [ ] Default values applied correctly
- [ ] Migration is idempotent (can run multiple times safely)
- [ ] Rollback removes all changes
- [ ] No data loss during migration
- [ ] Application code works with new schema
- [ ] Existing data migrated correctly (if data migration included)

### Testing in CI Pipeline

The CI pipeline automatically runs migration tests during the `integration-tests` stage:

```yaml
# In .github/workflows/ci-cd.yml
- name: Run migration tests
  working-directory: ./backend
  env:
    DATABASE_URL: postgresql+asyncpg://sovd_user:sovd_pass@localhost:5432/sovd
  run: |
    bash ../scripts/test_migration.sh
```

---

## Production Deployment Workflow

### Migration Workflow Stages

```
Local Development → Git Commit → CI Tests → Staging → Production
```

### Staging Deployment (Automatic)

When code is merged to `develop` branch:

1. CI pipeline runs migration tests
2. Docker images built and pushed
3. Helm deploys to staging namespace
4. **Kubernetes Job runs migrations** (Helm pre-upgrade hook)
5. Backend pods deploy with new code

**Kubernetes migration Job behavior**:
- Runs `alembic upgrade head` before backend pods start
- Uses same Docker image as backend
- Has access to database credentials from Secrets
- Retries up to 3 times on failure
- Deployment fails if migration fails (prevents broken deployments)

### Production Deployment (Manual Approval)

When code is merged to `main` branch:

1. **Manual approval required** (GitHub environment protection)
2. CI pipeline runs all tests
3. Docker images built and scanned (Trivy)
4. Helm deploys to production namespace
5. **Kubernetes Job runs migrations** (Helm pre-upgrade hook)
6. Backend pods deploy with rolling update strategy
7. Smoke tests verify deployment health
8. Automatic rollback on failure

### Monitoring Migration Job in Kubernetes

```bash
# Watch migration Job status
kubectl get jobs -n production -w

# View migration Job logs
kubectl logs -n production job/sovd-webapp-migration

# Check Job status
kubectl describe job -n production sovd-webapp-migration

# If Job failed, check pod logs
kubectl get pods -n production | grep migration
kubectl logs -n production <migration-pod-name>
```

### Helm Pre-Upgrade Hook Details

The migration Job uses Helm hooks to ensure migrations run before deployment:

```yaml
annotations:
  "helm.sh/hook": pre-upgrade,pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": before-hook-creation
```

**Behavior**:
- `pre-upgrade`: Runs before `helm upgrade` applies changes
- `pre-install`: Runs before `helm install` on first deployment
- `hook-weight: -5`: Ensures migrations run before other pre-upgrade hooks
- `before-hook-creation`: Deletes old migration Job pods before creating new ones

---

## Rollback Procedures

### Rolling Back Migrations Locally

```bash
cd backend/

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations (DANGEROUS)
alembic downgrade base

# View migration history
alembic history --verbose
```

### Rolling Back Production Deployment

If a deployment causes issues due to migrations:

#### Option 1: Rollback Application Only (Safe)

If migration is backward-compatible:

```bash
# Rollback Helm release to previous version
helm rollback sovd-webapp -n production

# This reverts application code but keeps database at new schema
# Only works if new schema is backward-compatible with old code
```

#### Option 2: Rollback Both Application and Database (Complex)

If migration is NOT backward-compatible:

```bash
# Step 1: Scale down backend pods to prevent writes
kubectl scale deployment -n production sovd-webapp-backend --replicas=0

# Step 2: Backup database
pg_dump -h <rds-endpoint> -U sovd_user -d sovd > backup_before_rollback.sql

# Step 3: Connect to database and rollback migration
kubectl run -it --rm postgres-client --image=postgres:15 --restart=Never -- \
  psql postgresql://sovd_user:password@<rds-endpoint>:5432/sovd

# Inside psql session:
# \q to exit and use kubectl exec instead

# Alternative: Run migration rollback via Job
kubectl run migration-rollback -n production \
  --image=ghcr.io/<repo>/sovd-backend:previous-sha \
  --env="DATABASE_URL=postgresql+asyncpg://sovd_user:password@<rds>:5432/sovd" \
  --restart=Never \
  -- alembic downgrade -1

# Step 4: Wait for rollback to complete
kubectl logs -n production migration-rollback -f

# Step 5: Rollback Helm release
helm rollback sovd-webapp -n production

# Step 6: Verify backend pods healthy
kubectl get pods -n production -l app=backend
```

### Emergency Rollback Checklist

- [ ] Database backup created (CRITICAL)
- [ ] Application pods scaled down
- [ ] Migration rollback tested in staging first
- [ ] Rollback script reviewed and approved
- [ ] Operations team notified
- [ ] Rollback executed during maintenance window
- [ ] Database schema verified post-rollback
- [ ] Application pods restarted and healthy
- [ ] Smoke tests passed
- [ ] Incident postmortem scheduled

---

## Handling Migration Conflicts

### Scenario: Two Developers Create Migrations Simultaneously

**Problem**: Developer A creates migration `abc123` and Developer B creates migration `def456`, both with `down_revision = 'xyz789'`.

**Symptoms**:
```bash
alembic upgrade head
# Error: Multiple heads detected: abc123, def456
```

**Resolution**:

1. **Identify conflicting migrations**:
   ```bash
   alembic heads
   # Output: abc123, def456
   ```

2. **Merge migrations**:
   ```bash
   # Create merge migration
   alembic merge -m "Merge abc123 and def456" abc123 def456

   # This creates a new migration with both as down_revisions
   ```

3. **Test merged migration**:
   ```bash
   ./scripts/test_migration.sh
   ```

4. **Commit merge migration**:
   ```bash
   git add alembic/versions/<merge_revision>_merge_abc123_and_def456.py
   git commit -m "fix(db): merge conflicting migrations"
   git push
   ```

### Scenario: Migration Fails Halfway

**Problem**: Migration applies some changes but fails partway through.

**Symptoms**:
- Database in inconsistent state
- Alembic version table shows old revision
- Some schema changes applied, others not

**Resolution**:

1. **Check current state**:
   ```bash
   alembic current
   psql -U sovd_user -d sovd -c "\dt"  # List tables
   ```

2. **Manual intervention**:
   ```bash
   # Option A: Manually complete the migration (if safe)
   psql -U sovd_user -d sovd
   # Run remaining DDL statements from migration file

   # Option B: Manually rollback partial changes
   psql -U sovd_user -d sovd
   # Run reverse DDL statements

   # Mark migration as completed (only if manually fixed)
   alembic stamp <revision_id>
   ```

3. **Re-run migration**:
   ```bash
   alembic upgrade head
   ```

### Scenario: Data Migration Takes Too Long

**Problem**: Migration modifying large dataset exceeds Kubernetes Job timeout (10 minutes).

**Solution**:

1. **Increase Job timeout** (temporarily):
   ```yaml
   # In migration-job.yaml
   spec:
     activeDeadlineSeconds: 1800  # 30 minutes
   ```

2. **Split migration into two**:
   ```python
   # Migration 1: Add column with nullable
   def upgrade():
       op.add_column('vehicles', sa.Column('status', sa.String(20), nullable=True))

   # Migration 2 (after deployment): Populate data and make non-nullable
   def upgrade():
       # Populate in batches
       op.execute("""
           UPDATE vehicles SET status = 'active' WHERE status IS NULL
       """)
       op.alter_column('vehicles', 'status', nullable=False)
   ```

3. **Use batch processing**:
   ```python
   def upgrade():
       # Process in chunks to avoid locks
       op.execute("""
           UPDATE vehicles SET status = 'active'
           WHERE id IN (
               SELECT id FROM vehicles WHERE status IS NULL LIMIT 1000
           )
       """)
   ```

---

## Best Practices

### Migration Design

1. **Always make migrations reversible**: Implement both `upgrade()` and `downgrade()`
2. **Keep migrations small**: One logical change per migration
3. **Avoid breaking changes**: Design backward-compatible schema changes when possible
4. **Use transactions**: Alembic wraps migrations in transactions automatically (PostgreSQL)
5. **Test with production data volume**: Test migrations with realistic data sizes

### Backward Compatibility Pattern

Example: Adding a required field without breaking existing code

```python
# Migration 1: Add column as nullable
def upgrade():
    op.add_column('vehicles', sa.Column('manufacturer', sa.String(50), nullable=True))

# Deploy new application code that handles nullable manufacturer

# Migration 2 (later): Make column non-nullable with default
def upgrade():
    op.execute("UPDATE vehicles SET manufacturer = 'Unknown' WHERE manufacturer IS NULL")
    op.alter_column('vehicles', 'manufacturer', nullable=False, server_default='Unknown')
```

### Data Migration Best Practices

1. **Separate DDL and data migrations**: Schema changes in one migration, data updates in another
2. **Use batch updates**: Process large datasets in chunks
3. **Avoid ORM in migrations**: Use raw SQL for data migrations (ORM models may change)
4. **Test performance**: Measure execution time on production-sized datasets
5. **Plan for rollback**: Ensure data migrations can be reversed

### Security Considerations

1. **Never commit database passwords**: Use environment variables
2. **Restrict migration Job permissions**: Use dedicated service account with minimal privileges
3. **Audit migrations**: Log all production migrations
4. **Review before production**: Require code review for all migration PRs
5. **Backup before major changes**: Always backup production database

---

## Common Alembic Commands Reference

```bash
# View current migration revision
alembic current

# View migration history
alembic history --verbose

# Show pending migrations
alembic heads

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Rollback all migrations (DANGEROUS)
alembic downgrade base

# Generate migration with autogenerate
alembic revision --autogenerate -m "description"

# Create empty migration (for data migrations)
alembic revision -m "description"

# Merge conflicting migrations
alembic merge -m "merge description" head1 head2

# Stamp database at specific revision (without running migration)
alembic stamp <revision_id>

# Show SQL for migration without executing
alembic upgrade --sql head > migration.sql

# Generate SQL for downgrade
alembic downgrade -1 --sql > rollback.sql
```

---

## Troubleshooting

### Problem: "Multiple head revisions are present"

**Cause**: Two migrations created with same parent revision

**Solution**: Create merge migration (see "Handling Migration Conflicts")

### Problem: "Can't locate revision identified by 'abc123'"

**Cause**: Migration file missing or not committed to Git

**Solution**: Ensure all migration files are tracked in version control

### Problem: "Target database is not up to date"

**Cause**: Alembic version table out of sync with actual schema

**Solution**:
```bash
# Check actual schema vs. expected
alembic current
psql -U sovd_user -d sovd -c "\dt"

# Stamp to correct revision if manually fixed
alembic stamp <correct_revision>
```

### Problem: Migration Job fails with "connection refused"

**Cause**: Database not reachable from Kubernetes cluster

**Solution**:
```bash
# Check database connection from within cluster
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- \
  psql postgresql://sovd_user:password@<db-host>:5432/sovd -c "SELECT 1;"

# Verify Secret contains correct credentials
kubectl get secret -n production sovd-webapp-secrets -o yaml
```

### Problem: Migration succeeds but application fails

**Cause**: Application code not compatible with new schema

**Solution**:
1. Ensure backward-compatible migrations
2. Use feature flags for new features requiring schema changes
3. Deploy code and schema changes in compatible order

---

## Testing Migration Job in Local Kubernetes

### Using Minikube

```bash
# Start minikube
minikube start

# Build Docker image locally
cd backend/
docker build -t sovd-backend:test -f Dockerfile.prod .

# Load image into minikube
minikube image load sovd-backend:test

# Create test namespace
kubectl create namespace migration-test

# Create database Secret
kubectl create secret generic sovd-webapp-secrets \
  -n migration-test \
  --from-literal=database-password=sovd_pass

# Create ConfigMap
kubectl create configmap sovd-webapp-config \
  -n migration-test \
  --from-literal=LOG_LEVEL=INFO \
  --from-literal=ENVIRONMENT=test

# Install Helm chart with migration Job
cd ../infrastructure/helm/sovd-webapp/
helm install sovd-test . \
  -n migration-test \
  --set backend.image.repository=sovd-backend \
  --set backend.image.tag=test \
  --set config.database.host=host.minikube.internal \
  --set config.database.port=5432 \
  --set config.database.name=sovd \
  --set config.database.user=sovd_user

# Watch migration Job
kubectl get jobs -n migration-test -w

# View migration logs
kubectl logs -n migration-test job/sovd-test-migration

# Cleanup
helm uninstall sovd-test -n migration-test
kubectl delete namespace migration-test
```

### Using Kind (Kubernetes in Docker)

```bash
# Create Kind cluster
kind create cluster --name sovd-test

# Load image into Kind
kind load docker-image sovd-backend:test --name sovd-test

# Follow same steps as minikube above
# (replace minikube commands with kubectl)

# Cleanup
kind delete cluster --name sovd-test
```

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Kubernetes Jobs Documentation](https://kubernetes.io/docs/concepts/workloads/controllers/job/)
- [Helm Hooks Documentation](https://helm.sh/docs/topics/charts_hooks/)

---

## Migration Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│ LOCAL DEVELOPMENT                                               │
├─────────────────────────────────────────────────────────────────┤
│ 1. Modify SQLAlchemy models                                     │
│ 2. alembic revision --autogenerate -m "description"             │
│ 3. Review generated migration file                              │
│ 4. ./scripts/test_migration.sh                                  │
│ 5. git commit & push                                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ CI PIPELINE                                                     │
├─────────────────────────────────────────────────────────────────┤
│ 1. Run migration tests (integration-tests job)                  │
│ 2. Build Docker images                                          │
│ 3. Security scans                                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ STAGING DEPLOYMENT (Automatic on develop branch)               │
├─────────────────────────────────────────────────────────────────┤
│ 1. Helm pre-upgrade hook triggers migration Job                │
│ 2. Job runs: alembic upgrade head                              │
│ 3. Job succeeds → Backend pods deploy                          │
│ 4. Job fails → Deployment aborted                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ PRODUCTION DEPLOYMENT (Manual approval on main branch)         │
├─────────────────────────────────────────────────────────────────┤
│ 1. Manual approval required                                     │
│ 2. Database backup (manual step)                               │
│ 3. Helm pre-upgrade hook triggers migration Job                │
│ 4. Job runs: alembic upgrade head                              │
│ 5. Job succeeds → Rolling update of backend pods               │
│ 6. Smoke tests verify deployment                               │
│ 7. Automatic rollback on failure                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Contact and Support

For migration-related issues:
- Review this runbook first
- Check CI pipeline logs for errors
- Review Kubernetes Job logs: `kubectl logs job/sovd-webapp-migration`
- Consult with database team for complex data migrations
- Create incident ticket for production migration failures

**Last Updated**: 2025-10-31
**Document Owner**: Backend Team
**Review Cycle**: Quarterly
