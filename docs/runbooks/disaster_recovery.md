# Disaster Recovery Runbook

This runbook provides procedures for backing up, restoring, and recovering the SOVD Web Application in disaster scenarios.

## Table of Contents

- [Overview](#overview)
- [Recovery Objectives](#recovery-objectives)
- [Backup Procedures](#backup-procedures)
  - [Database Backups](#database-backups)
  - [Redis Backups](#redis-backups)
  - [Application Configuration Backups](#application-configuration-backups)
  - [Audit Log Archival](#audit-log-archival)
- [Restore Procedures](#restore-procedures)
  - [Database Restore](#database-restore)
  - [Redis Restore](#redis-restore)
  - [Full System Restore](#full-system-restore)
- [Disaster Scenarios](#disaster-scenarios)
- [Backup Verification](#backup-verification)
- [Backup Retention Policy](#backup-retention-policy)

---

## Overview

The SOVD Web Application disaster recovery strategy focuses on:
1. **Data Protection**: Regular automated backups of all critical data
2. **Rapid Recovery**: Documented procedures to restore service quickly
3. **Compliance**: Audit log retention for regulatory requirements
4. **Testing**: Regular backup verification and restore drills

**Critical Data Assets**:
- PostgreSQL database (users, vehicles, commands, audit logs)
- Redis cache/session data (less critical, can rebuild)
- Application configuration (secrets, environment variables)
- Audit logs (for compliance)

---

## Recovery Objectives

| Metric | Target | Definition |
|--------|--------|------------|
| **RTO** (Recovery Time Objective) | 15 minutes | Maximum acceptable downtime |
| **RPO** (Recovery Point Objective) | 5 minutes | Maximum acceptable data loss |
| **Backup Frequency** | Daily (automated) | Database snapshots |
| **Point-in-Time Recovery** | 7 days | Can restore to any point in last week |
| **Backup Retention** | 30 days | Keep backups for 1 month |
| **Audit Log Retention** | 90 days | Compliance requirement |

---

## Backup Procedures

### Database Backups

#### Automated Daily Backups (Production)

**AWS RDS Automated Backups**:
- Enabled by default in production
- Daily snapshots at 03:00 UTC
- 30-day retention
- Point-in-time recovery for last 7 days

**Verify automated backups**:
```bash
aws rds describe-db-snapshots \
  --db-instance-identifier sovd-production-db \
  --snapshot-type automated \
  --region us-east-1 \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime,Status]' \
  --output table
```

#### Manual Database Backup (Local/Development)

**Backup Script** (`scripts/backup_database.sh`):

```bash
#!/bin/bash
# SOVD Database Backup Script
# Usage: ./scripts/backup_database.sh [environment]

set -e

ENVIRONMENT=${1:-local}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/database"
mkdir -p "$BACKUP_DIR"

echo "Starting database backup for environment: $ENVIRONMENT"

if [ "$ENVIRONMENT" = "local" ]; then
    # Local Docker environment
    docker-compose exec -T db pg_dump -U sovd_user -d sovd_db --clean --if-exists --verbose \
        > "$BACKUP_DIR/sovd_db_${ENVIRONMENT}_${TIMESTAMP}.sql"

elif [ "$ENVIRONMENT" = "production" ]; then
    # Production RDS
    DB_HOST=$(aws rds describe-db-instances \
        --db-instance-identifier sovd-production-db \
        --query 'DBInstances[0].Endpoint.Address' \
        --output text)

    # Requires database credentials from AWS Secrets Manager
    DB_PASSWORD=$(aws secretsmanager get-secret-value \
        --secret-id production/sovd/database \
        --query 'SecretString' \
        --output text | jq -r '.password')

    PGPASSWORD=$DB_PASSWORD pg_dump -h $DB_HOST -U sovd_user -d sovd_db \
        --clean --if-exists --verbose \
        > "$BACKUP_DIR/sovd_db_${ENVIRONMENT}_${TIMESTAMP}.sql"

else
    echo "Unknown environment: $ENVIRONMENT"
    exit 1
fi

# Compress backup
gzip "$BACKUP_DIR/sovd_db_${ENVIRONMENT}_${TIMESTAMP}.sql"

BACKUP_FILE="$BACKUP_DIR/sovd_db_${ENVIRONMENT}_${TIMESTAMP}.sql.gz"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "Backup completed successfully!"
echo "File: $BACKUP_FILE"
echo "Size: $BACKUP_SIZE"

# Upload to S3 (production only)
if [ "$ENVIRONMENT" = "production" ]; then
    echo "Uploading backup to S3..."
    aws s3 cp "$BACKUP_FILE" \
        s3://sovd-backups/database/$(date +%Y)/$(date +%m)/ \
        --storage-class STANDARD_IA

    echo "Backup uploaded to S3"
fi

# Keep only last 30 days of local backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete

echo "Backup process completed!"
```

**Run manual backup**:
```bash
# Local environment
./scripts/backup_database.sh local

# Production environment
./scripts/backup_database.sh production
```

**Verification**:
```bash
# Check backup file exists
ls -lh backups/database/

# Verify backup integrity (test decompression)
gzip -t backups/database/sovd_db_local_*.sql.gz
echo "Backup file is valid"
```

#### Table-Specific Backups

For specific tables (e.g., audit logs only):

```bash
docker-compose exec -T db pg_dump -U sovd_user -d sovd_db \
    --table=audit_logs \
    --clean --if-exists \
    > backups/audit_logs_$(date +%Y%m%d).sql
```

---

### Redis Backups

Redis data (sessions, cache) is less critical and can be rebuilt. However, for zero-downtime recovery:

#### Redis Backup Script (`scripts/backup_redis.sh`):

```bash
#!/bin/bash
# SOVD Redis Backup Script
# Usage: ./scripts/backup_redis.sh [environment]

set -e

ENVIRONMENT=${1:-local}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/redis"
mkdir -p "$BACKUP_DIR"

echo "Starting Redis backup for environment: $ENVIRONMENT"

if [ "$ENVIRONMENT" = "local" ]; then
    # Trigger Redis save
    docker-compose exec -T redis redis-cli BGSAVE

    # Wait for save to complete
    echo "Waiting for Redis BGSAVE to complete..."
    while [ "$(docker-compose exec -T redis redis-cli LASTSAVE)" = "$(docker-compose exec -T redis redis-cli LASTSAVE)" ]; do
        sleep 1
    done

    # Copy RDB file
    docker-compose cp redis:/data/dump.rdb "$BACKUP_DIR/redis_${ENVIRONMENT}_${TIMESTAMP}.rdb"

elif [ "$ENVIRONMENT" = "production" ]; then
    # Production ElastiCache (automatic backups enabled)
    echo "ElastiCache automatic backups are enabled"
    echo "Manual snapshot can be created via AWS Console or CLI"

    # Create manual snapshot
    aws elasticache create-snapshot \
        --replication-group-id sovd-production-redis \
        --snapshot-name sovd-redis-manual-${TIMESTAMP} \
        --region us-east-1

    echo "ElastiCache snapshot created: sovd-redis-manual-${TIMESTAMP}"
    exit 0
fi

# Compress backup
gzip "$BACKUP_DIR/redis_${ENVIRONMENT}_${TIMESTAMP}.rdb"

BACKUP_FILE="$BACKUP_DIR/redis_${ENVIRONMENT}_${TIMESTAMP}.rdb.gz"
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

echo "Redis backup completed!"
echo "File: $BACKUP_FILE"
echo "Size: $BACKUP_SIZE"

# Keep only last 7 days of Redis backups (sessions expire quickly)
find "$BACKUP_DIR" -name "*.rdb.gz" -mtime +7 -delete

echo "Redis backup process completed!"
```

**Run Redis backup**:
```bash
./scripts/backup_redis.sh local
```

---

### Application Configuration Backups

**Backup environment variables and secrets**:

```bash
#!/bin/bash
# Backup configuration (DO NOT commit to Git)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/config"
mkdir -p "$BACKUP_DIR"

# Local environment
cp .env "$BACKUP_DIR/env_${TIMESTAMP}.bak"

# Production secrets (from AWS Secrets Manager)
aws secretsmanager get-secret-value \
    --secret-id production/sovd/database \
    --query 'SecretString' \
    --output text > "$BACKUP_DIR/secrets_database_${TIMESTAMP}.json"

aws secretsmanager get-secret-value \
    --secret-id production/sovd/jwt \
    --query 'SecretString' \
    --output text > "$BACKUP_DIR/secrets_jwt_${TIMESTAMP}.json"

# Encrypt sensitive backups
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/secrets_database_${TIMESTAMP}.json"
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/secrets_jwt_${TIMESTAMP}.json"

# Remove unencrypted files
rm "$BACKUP_DIR/secrets_*.json"

echo "Configuration backed up to $BACKUP_DIR"
```

---

### Audit Log Archival

Audit logs must be retained for 90 days for compliance.

**Archive Script** (`scripts/archive_audit_logs.sh`):

```bash
#!/bin/bash
# Archive audit logs older than 30 days to S3

set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
ARCHIVE_DIR="./backups/audit_logs"
mkdir -p "$ARCHIVE_DIR"

echo "Archiving audit logs older than 30 days..."

# Export old audit logs
docker-compose exec -T db psql -U sovd_user -d sovd_db -c "
COPY (
    SELECT * FROM audit_logs
    WHERE timestamp < NOW() - INTERVAL '30 days'
) TO STDOUT WITH CSV HEADER
" > "$ARCHIVE_DIR/audit_logs_${TIMESTAMP}.csv"

# Compress
gzip "$ARCHIVE_DIR/audit_logs_${TIMESTAMP}.csv"

ARCHIVE_FILE="$ARCHIVE_DIR/audit_logs_${TIMESTAMP}.csv.gz"
ROW_COUNT=$(zcat "$ARCHIVE_FILE" | wc -l)

echo "Archived $((ROW_COUNT - 1)) audit log entries"
echo "File: $ARCHIVE_FILE"

# Upload to S3 (production)
aws s3 cp "$ARCHIVE_FILE" \
    s3://sovd-backups/audit-logs/$(date +%Y)/$(date +%m)/ \
    --storage-class GLACIER

echo "Audit logs archived to S3 Glacier"

# Delete archived logs from database (optional, only after verification)
# docker-compose exec -T db psql -U sovd_user -d sovd_db -c "
# DELETE FROM audit_logs WHERE timestamp < NOW() - INTERVAL '30 days'
# "

echo "Archive process completed!"
```

**Run audit log archival**:
```bash
./scripts/archive_audit_logs.sh
```

---

## Restore Procedures

### Database Restore

#### Restore from Local Backup

**Step 1**: Stop the application:
```bash
docker-compose down
```

**Step 2**: Start only the database:
```bash
docker-compose up -d db
sleep 10  # Wait for database to be ready
```

**Step 3**: Restore the backup:
```bash
# List available backups
ls -lh backups/database/

# Restore from backup
BACKUP_FILE="backups/database/sovd_db_local_20251030_120000.sql.gz"

gunzip -c "$BACKUP_FILE" | docker-compose exec -T db psql -U sovd_user -d sovd_db
```

**Step 4**: Verify restore:
```bash
docker-compose exec db psql -U sovd_user -d sovd_db -c "
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM vehicles;
SELECT COUNT(*) FROM commands;
SELECT COUNT(*) FROM audit_logs;
"
```

**Step 5**: Restart all services:
```bash
docker-compose up -d
```

**Step 6**: Test application:
```bash
curl http://localhost:8000/health/ready
# Should return {"status": "healthy", ...}
```

#### Restore from AWS RDS Snapshot (Production)

**Step 1**: List available snapshots:
```bash
aws rds describe-db-snapshots \
  --db-instance-identifier sovd-production-db \
  --region us-east-1 \
  --query 'DBSnapshots[*].[DBSnapshotIdentifier,SnapshotCreateTime]' \
  --output table
```

**Step 2**: Restore to new instance (safest approach):
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier sovd-production-db-restored \
  --db-snapshot-identifier <snapshot-id> \
  --db-instance-class db.t3.medium \
  --multi-az \
  --region us-east-1
```

**Step 3**: Wait for instance to become available:
```bash
aws rds wait db-instance-available \
  --db-instance-identifier sovd-production-db-restored \
  --region us-east-1

echo "Database instance is available"
```

**Step 4**: Update Kubernetes secrets:
```bash
# Get new database endpoint
NEW_DB_HOST=$(aws rds describe-db-instances \
  --db-instance-identifier sovd-production-db-restored \
  --query 'DBInstances[0].Endpoint.Address' \
  --output text)

# Update DATABASE_URL secret
kubectl edit secret sovd-database-secret -n production
# Update the connection string with new hostname
```

**Step 5**: Restart backend pods:
```bash
kubectl rollout restart deployment/backend-deployment -n production
kubectl rollout status deployment/backend-deployment -n production
```

**Step 6**: Verify application:
```bash
curl https://sovd.yourdomain.com/health/ready
```

#### Point-in-Time Recovery (AWS RDS)

Restore database to a specific timestamp within the last 7 days:

```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier sovd-production-db \
  --target-db-instance-identifier sovd-production-db-pitr \
  --restore-time 2025-10-30T12:00:00Z \
  --db-instance-class db.t3.medium \
  --multi-az \
  --region us-east-1
```

Follow steps 3-6 from the snapshot restore procedure.

---

### Redis Restore

#### Restore from Local Backup

**Step 1**: Stop Redis:
```bash
docker-compose stop redis
```

**Step 2**: Replace RDB file:
```bash
# Decompress backup
BACKUP_FILE="backups/redis/redis_local_20251030_120000.rdb.gz"
gunzip -c "$BACKUP_FILE" > /tmp/dump.rdb

# Copy to Redis container
docker-compose cp /tmp/dump.rdb redis:/data/dump.rdb

# Clean up
rm /tmp/dump.rdb
```

**Step 3**: Restart Redis:
```bash
docker-compose start redis
```

**Step 4**: Verify restore:
```bash
docker-compose exec redis redis-cli DBSIZE
# Should show number of keys restored
```

#### Restore Redis in Production (ElastiCache)

**Step 1**: Create new cluster from snapshot:
```bash
aws elasticache create-replication-group \
  --replication-group-id sovd-production-redis-restored \
  --replication-group-description "Restored from snapshot" \
  --snapshot-name sovd-redis-manual-20251030 \
  --cache-node-type cache.t3.small \
  --engine redis \
  --region us-east-1
```

**Step 2**: Update Kubernetes secrets with new Redis endpoint.

**Step 3**: Restart backend pods.

**Note**: Redis recovery is rarely necessary. In most cases, rebuilding sessions (users log back in) is acceptable.

---

### Full System Restore

Complete disaster recovery from scratch.

#### Prerequisites
- Latest database backup
- Latest Redis backup (optional)
- Configuration backups (secrets)
- Infrastructure as Code (Terraform/Helm charts)

#### Step 1: Restore Infrastructure (Production)

```bash
# Recreate Kubernetes cluster (if destroyed)
terraform apply -var-file=production.tfvars

# Or use eksctl
eksctl create cluster -f cluster-config.yaml
```

#### Step 2: Deploy Application

```bash
# Deploy Helm chart
helm upgrade --install sovd-webapp ./sovd-helm-chart \
  -f values-production.yaml \
  -n production
```

#### Step 3: Restore Database

Follow the [Database Restore](#database-restore) procedure using the latest backup.

#### Step 4: Restore Redis (Optional)

Follow the [Redis Restore](#redis-restore) procedure if zero-downtime session recovery is required.

#### Step 5: Restore Configuration

```bash
# Decrypt and restore secrets
gpg --decrypt backups/config/secrets_database_20251030.json.gpg | \
  aws secretsmanager put-secret-value \
    --secret-id production/sovd/database \
    --secret-string file:///dev/stdin
```

#### Step 6: Verify Application

Run full smoke test suite:
```bash
export API_BASE_URL=https://sovd.yourdomain.com
pytest tests/smoke/ -v
```

#### Step 7: Notify Stakeholders

Send notification that service is restored:
- Update status page
- Post in Slack (#sovd-incidents)
- Email affected users (if any)

---

## Disaster Scenarios

### Scenario 1: Database Corruption

**Symptoms**: Database queries fail, data inconsistency errors.

**Recovery**:
1. Stop application: `docker-compose down`
2. Restore from latest backup (see [Database Restore](#database-restore))
3. Verify data integrity
4. Restart application

**Expected RTO**: 10 minutes
**Expected RPO**: Last backup (max 24 hours for automated, 0 for point-in-time)

---

### Scenario 2: Accidental Data Deletion

**Symptoms**: User reports missing data (commands, vehicles).

**Recovery**:
1. Identify timestamp of deletion
2. Use point-in-time recovery to restore to just before deletion
3. Export deleted data
4. Import into current database

**Example**:
```bash
# Restore to 1 hour ago
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier sovd-production-db \
  --target-db-instance-identifier sovd-temp-recovery \
  --restore-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)

# Export deleted data
pg_dump -h <temp-instance> -U sovd_user -d sovd_db \
  --table=commands \
  --data-only \
  > deleted_commands.sql

# Import to production
psql -h <production-instance> -U sovd_user -d sovd_db < deleted_commands.sql

# Delete temporary instance
aws rds delete-db-instance --db-instance-identifier sovd-temp-recovery
```

**Expected RTO**: 30 minutes
**Expected RPO**: 0 (point-in-time recovery)

---

### Scenario 3: Complete Region Failure (AWS)

**Symptoms**: Entire AWS region is unavailable.

**Recovery** (requires cross-region replication):
1. Restore database from S3 backup in secondary region
2. Deploy application to secondary region using Helm
3. Update DNS to point to secondary region
4. Notify users of region change

**Expected RTO**: 1 hour (manual process)
**Expected RPO**: Last backup uploaded to S3 (24 hours)

**Note**: Cross-region replication is optional. Implement if RTO <1 hour is required.

---

### Scenario 4: Ransomware Attack

**Symptoms**: Data encrypted, ransom note in database.

**Recovery**:
1. **DO NOT** pay ransom
2. Isolate affected systems (stop all services)
3. Scan for malware/backdoors
4. Restore from backup that predates infection
5. Audit all access logs
6. Reset all credentials
7. Implement additional security measures

**Expected RTO**: 2-4 hours (includes security audit)
**Expected RPO**: Last clean backup

---

## Backup Verification

**Verification Schedule**: Monthly

### Manual Verification Steps

**Step 1**: Select a random backup:
```bash
BACKUP_FILE=$(ls backups/database/*.sql.gz | shuf -n 1)
echo "Testing backup: $BACKUP_FILE"
```

**Step 2**: Create test environment:
```bash
docker run --name test-db -e POSTGRES_PASSWORD=test -d postgres:15
sleep 10
```

**Step 3**: Restore backup:
```bash
gunzip -c "$BACKUP_FILE" | docker exec -i test-db psql -U postgres -d postgres
```

**Step 4**: Verify data:
```bash
docker exec test-db psql -U postgres -d postgres -c "
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM vehicles;
SELECT COUNT(*) FROM commands;
"
```

**Step 5**: Clean up:
```bash
docker stop test-db
docker rm test-db
```

**Step 6**: Document results:
```bash
echo "$(date): Backup verification successful for $BACKUP_FILE" >> backups/verification.log
```

---

## Backup Retention Policy

| Data Type | Backup Frequency | Retention Period | Storage Location |
|-----------|-----------------|------------------|------------------|
| Database (automated) | Daily | 30 days | AWS RDS snapshots |
| Database (manual) | On-demand | 30 days | Local + S3 |
| Redis | Weekly | 7 days | Local + ElastiCache snapshots |
| Audit Logs | Monthly | 90 days | S3 Glacier |
| Configuration | On change | 90 days | Encrypted local + S3 |
| Application Logs | Continuous | 30 days | CloudWatch Logs |

### Storage Costs (Estimated)

- **RDS Automated Backups**: $0.095/GB-month (S3 pricing)
- **S3 Standard-IA**: $0.0125/GB-month
- **S3 Glacier**: $0.004/GB-month
- **ElastiCache Snapshots**: $0.085/GB-month

**Estimated monthly cost for 100GB database**:
- RDS backups: $9.50/month
- S3 archives: $0.40/month
- **Total**: ~$10/month

---

## Backup Automation

### Cron Schedule (Production)

Add to crontab:

```cron
# Database backup (daily at 3 AM UTC)
0 3 * * * /opt/sovd/scripts/backup_database.sh production

# Redis backup (weekly on Sunday at 2 AM UTC)
0 2 * * 0 /opt/sovd/scripts/backup_redis.sh production

# Audit log archival (monthly on 1st at 1 AM UTC)
0 1 1 * * /opt/sovd/scripts/archive_audit_logs.sh

# Backup verification (monthly on 15th at 4 AM UTC)
0 4 15 * * /opt/sovd/scripts/verify_backups.sh
```

### Monitoring Backup Jobs

Check backup job status:
```bash
# Check last backup time
aws rds describe-db-snapshots \
  --db-instance-identifier sovd-production-db \
  --snapshot-type automated \
  --query 'DBSnapshots[0].[DBSnapshotIdentifier,SnapshotCreateTime]' \
  --output table

# Alert if backup is older than 2 days
LAST_BACKUP=$(aws rds describe-db-snapshots \
  --db-instance-identifier sovd-production-db \
  --snapshot-type automated \
  --query 'DBSnapshots[0].SnapshotCreateTime' \
  --output text)

# Add to Prometheus/Grafana alerting
```

---

## Testing Disaster Recovery

**Test Schedule**: Quarterly

### DR Drill Checklist

- [ ] Schedule drill during maintenance window
- [ ] Notify team (no surprises)
- [ ] Document start time
- [ ] Simulate disaster (e.g., delete staging database)
- [ ] Follow restore procedures
- [ ] Time recovery process (compare to RTO)
- [ ] Verify application functionality
- [ ] Document lessons learned
- [ ] Update runbook if needed

### Sample DR Drill Report

```
DR Drill Report - 2025-Q1
Date: 2025-01-15
Scenario: Database corruption in staging
Participants: DevOps team, Backend engineers

Timeline:
- 10:00 AM: Drill started (simulated database corruption)
- 10:02 AM: Identified latest backup
- 10:05 AM: Began restore process
- 10:12 AM: Database restore completed
- 10:15 AM: Application restarted
- 10:17 AM: Functionality verified

Metrics:
- RTO Target: 15 minutes
- RTO Actual: 17 minutes (exceeded by 2 min)
- RPO Target: 5 minutes
- RPO Actual: 1 hour (last backup)

Issues Encountered:
1. Backup file took longer to download from S3 than expected
2. Restore command required --clean flag (not documented)

Action Items:
1. Add --clean flag to restore documentation
2. Consider more frequent backups (every 4 hours instead of daily)
3. Pre-download latest backup to local storage for faster recovery

Status: PASS (with minor improvements needed)
```

---

## Additional Resources

- **Deployment Guide**: [deployment.md](deployment.md)
- **Troubleshooting Guide**: [troubleshooting.md](troubleshooting.md)
- **Monitoring Guide**: [monitoring.md](monitoring.md)
- **AWS RDS Documentation**: https://docs.aws.amazon.com/rds/
- **PostgreSQL Backup Docs**: https://www.postgresql.org/docs/current/backup.html

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Owner**: Platform Engineering Team
**Review Schedule**: Quarterly
