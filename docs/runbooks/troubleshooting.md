# Troubleshooting Runbook

This runbook provides diagnostic procedures and solutions for common issues encountered in the SOVD Web Application.

## Table of Contents

- [Quick Diagnostic Steps](#quick-diagnostic-steps)
- [Common Issues](#common-issues)
  - [Issue 1: Backend Won't Start](#issue-1-backend-wont-start)
  - [Issue 2: Frontend 401 Unauthorized Errors](#issue-2-frontend-401-unauthorized-errors)
  - [Issue 3: WebSocket Connections Failing](#issue-3-websocket-connections-failing)
  - [Issue 4: Rate Limiting (429 Too Many Requests)](#issue-4-rate-limiting-429-too-many-requests)
  - [Issue 5: Health Check Failures](#issue-5-health-check-failures)
  - [Issue 6: Port Conflicts Preventing Startup](#issue-6-port-conflicts-preventing-startup)
  - [Issue 7: Database Connection Errors](#issue-7-database-connection-errors)
  - [Issue 8: Redis Connection Failures](#issue-8-redis-connection-failures)
- [Advanced Diagnostics](#advanced-diagnostics)
- [Escalation Procedures](#escalation-procedures)

---

## Quick Diagnostic Steps

Before diving into specific issues, run these quick checks:

### 1. Check Service Health

```bash
# Local environment
curl http://localhost:8000/health/ready

# Production/Staging
curl https://<your-domain>/health/ready
```

**Expected Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

### 2. Check All Services Are Running

**Local**:
```bash
docker-compose ps
```

**Kubernetes** (Staging/Production):
```bash
kubectl get pods -n <namespace>
```

All pods should show `Running` status with `1/1` ready.

### 3. Check Recent Logs

**Local**:
```bash
# All services
make logs

# Specific service
docker-compose logs backend --tail=100

# Follow logs in real-time
docker-compose logs -f backend
```

**Kubernetes**:
```bash
# Backend logs
kubectl logs -n <namespace> -l app=backend --tail=100

# Frontend logs
kubectl logs -n <namespace> -l app=frontend --tail=100

# Follow logs in real-time
kubectl logs -n <namespace> -l app=backend -f
```

### 4. Check Monitoring Dashboards

1. **Grafana Operations Dashboard**: Check error rates, latency, and throughput
2. **Prometheus**: Verify all targets are UP (http://localhost:9090/targets)
3. **CloudWatch** (AWS): Check for error spikes

---

## Common Issues

### Issue 1: Backend Won't Start

**Symptoms**:
- Backend container exits immediately after starting
- Error: "relation does not exist" in logs
- Docker Compose shows backend as "Exit 1"

#### Root Cause
The database has not been initialized with the required schema.

#### Diagnosis

Check backend logs:
```bash
docker-compose logs backend | grep -i error
```

Look for errors like:
```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "users" does not exist
```

#### Solution

**Step 1**: Ensure database service is running:
```bash
docker-compose ps db
# Should show "Up" status
```

**Step 2**: Run database initialization:
```bash
docker-compose exec backend /bin/bash -c "cd /app && bash /app/scripts/init_db.sh"
```

**Step 3**: Restart backend:
```bash
docker-compose restart backend
```

**Verification**:
```bash
curl http://localhost:8000/health/ready
# Should return {"status": "healthy", ...}
```

#### If Problem Persists

Check database connection string:
```bash
docker-compose exec backend env | grep DATABASE_URL
# Should be: postgresql://sovd_user:sovd_password@db:5432/sovd_db
```

If incorrect, update `.env` file and restart:
```bash
docker-compose down
docker-compose up -d
```

---

### Issue 2: Frontend 401 Unauthorized Errors

**Symptoms**:
- User can log in but subsequent API calls return 401
- Error in browser console: "Unauthorized"
- Token appears to be present in localStorage

#### Root Cause
JWT token has expired or is invalid.

#### Diagnosis

**Step 1**: Check if token exists in browser localStorage:
```javascript
// In browser console
localStorage.getItem('token')
```

**Step 2**: Decode the JWT token (use jwt.io):
- Check the `exp` (expiration) claim
- Compare with current time (Unix timestamp)

**Step 3**: Check backend logs for authentication errors:
```bash
docker-compose logs backend | grep "Authentication failed"
```

Look for:
```
WARNING: Authentication failed: Token has expired
WARNING: Authentication failed: Invalid token signature
```

#### Solution

**Solution 1: Token Expired (Most Common)**

The token has expired (default: 30 minutes). User needs to log out and log back in:

1. Clear localStorage: `localStorage.clear()`
2. Refresh page
3. Log in again

**Solution 2: JWT Secret Mismatch**

If tokens are consistently invalid, check JWT secret configuration:

```bash
# Check backend JWT configuration
docker-compose exec backend env | grep JWT_SECRET_KEY

# Ensure it matches .env file
cat .env | grep JWT_SECRET_KEY
```

If they don't match, update `.env` and restart:
```bash
docker-compose restart backend
```

**Solution 3: Clock Skew**

If the issue occurs immediately after login, check system time:
```bash
date
# Ensure system time is accurate
```

If time is off, synchronize:
```bash
sudo ntpdate pool.ntp.org
```

#### Verification

1. Log in with test credentials: `admin` / `admin123`
2. Navigate to Vehicles page
3. Confirm vehicles load without 401 errors

---

### Issue 3: WebSocket Connections Failing

**Symptoms**:
- Commands submitted but no real-time updates
- Browser console error: "WebSocket connection failed"
- Error: "Connection refused" or "Unexpected response code: 500"

#### Root Cause
Redis pub/sub not working or WebSocket server not accessible.

#### Diagnosis

**Step 1**: Check Redis is running:
```bash
docker-compose ps redis
# Should show "Up" status
```

**Step 2**: Test Redis connectivity:
```bash
docker-compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
r.ping()
print('Redis connected')
"
```

**Step 3**: Check WebSocket endpoint is accessible:
```bash
# Test WebSocket handshake
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:8000/ws/commands
```

Expected: `101 Switching Protocols` response.

**Step 4**: Check backend logs for WebSocket errors:
```bash
docker-compose logs backend | grep -i websocket
```

#### Solution

**Solution 1: Redis Not Running**

Start Redis:
```bash
docker-compose up -d redis
docker-compose restart backend
```

**Solution 2: Redis Connection Errors**

Check Redis URL configuration:
```bash
docker-compose exec backend env | grep REDIS_URL
# Should be: redis://redis:6379/0
```

If incorrect, update `.env` and restart services.

**Solution 3: WebSocket Connection Blocked**

Check if a proxy or firewall is blocking WebSocket connections:
- Ensure browser supports WebSockets (all modern browsers do)
- Check browser console for specific error messages
- Try direct connection (bypass proxy): http://localhost:8000/ws/commands

**Solution 4: CORS Issues**

Check CORS configuration in backend:
```bash
docker-compose exec backend grep -r "allow_origins" /app
```

Ensure frontend origin is allowed (http://localhost:5173).

#### Verification

1. Open browser developer tools (Network tab)
2. Filter by "WS" (WebSocket)
3. Log in and navigate to Commands page
4. Submit a command
5. Verify WebSocket connection is established (status 101)
6. Verify messages are received in real-time

---

### Issue 4: Rate Limiting (429 Too Many Requests)

**Symptoms**:
- API returns `429 Too Many Requests`
- Error message: "Rate limit exceeded"
- Subsequent requests work after waiting

#### Root Cause
User has exceeded the rate limit for their role.

#### Diagnosis

**Step 1**: Check the error response:
```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "correlation_id": "abc123..."
  }
}
```

**Step 2**: Identify which endpoint is being rate-limited:
- Authentication endpoints: 5 requests/minute
- Command endpoints: 10 requests/minute
- General API: 100 requests/minute

**Step 3**: Check user role:
```bash
# Search logs for user's role
docker-compose logs backend | grep "<correlation_id>"
```

Look for:
```
INFO: User john_doe (role=engineer) hit rate limit on /api/v1/commands
```

#### Solution

**Solution 1: Wait for Rate Limit Window to Reset**

Rate limits are per-minute windows. Wait 60 seconds and retry.

**Verification**:
```bash
# Wait 60 seconds, then retry
sleep 60
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/vehicles
```

**Solution 2: Upgrade User to Admin Role**

Admin users have a much higher rate limit (10,000/min, effectively unlimited).

```bash
# Connect to database
docker-compose exec backend psql $DATABASE_URL

# Update user role
UPDATE users SET role = 'admin' WHERE username = 'john_doe';

# Verify
SELECT username, role FROM users WHERE username = 'john_doe';

# Exit
\q
```

User must log out and log back in for the new role to take effect.

**Solution 3: Optimize Client Code**

If the application is making excessive API calls:
1. Review frontend code for unnecessary requests
2. Implement client-side caching
3. Batch requests where possible
4. Use WebSocket for real-time updates instead of polling

**Solution 4: Increase Rate Limits (Last Resort)**

Edit `backend/app/middleware/rate_limiting_middleware.py`:

```python
# Current limits
auth_limiter = Limiter(key_func=get_remote_address, default_limits=["5 per minute"])
command_limiter = Limiter(key_func=get_remote_address, default_limits=["10 per minute"])

# Increase as needed (not recommended for production)
auth_limiter = Limiter(key_func=get_remote_address, default_limits=["20 per minute"])
command_limiter = Limiter(key_func=get_remote_address, default_limits=["50 per minute"])
```

Restart backend after changes.

#### Current Rate Limits

| Endpoint Type | Rate Limit | Applies To |
|--------------|------------|-----------|
| Authentication (`/api/v1/auth/*`) | 5/minute | All users |
| Commands (`/api/v1/commands/*`) | 10/minute | Engineers |
| Commands (`/api/v1/commands/*`) | 10,000/minute | Admins |
| General API | 100/minute | All users |

---

### Issue 5: Health Check Failures

**Symptoms**:
- Health endpoint returns `503 Service Unavailable`
- Response: `{"status": "unhealthy", "database": "disconnected", ...}`
- Kubernetes reports pod as "Not Ready"

#### Root Cause
Backend cannot connect to database or Redis.

#### Diagnosis

**Step 1**: Check health endpoint:
```bash
curl http://localhost:8000/health/ready
```

Response will indicate which dependency is failing:
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "redis": "connected"
}
```

**Step 2**: Check database service:
```bash
docker-compose ps db
# Should be "Up"

# Test database connection
docker-compose exec db psql -U sovd_user -d sovd_db -c "SELECT 1;"
```

**Step 3**: Check Redis service:
```bash
docker-compose ps redis
# Should be "Up"

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return "PONG"
```

#### Solution

**Solution 1: Database Disconnected**

Restart database service:
```bash
docker-compose restart db
# Wait 10 seconds for database to start
sleep 10
docker-compose restart backend
```

**Solution 2: Redis Disconnected**

Restart Redis service:
```bash
docker-compose restart redis
docker-compose restart backend
```

**Solution 3: Incorrect Connection URLs**

Check environment variables:
```bash
docker-compose exec backend env | grep -E "(DATABASE_URL|REDIS_URL)"
```

Expected:
```
DATABASE_URL=postgresql://sovd_user:sovd_password@db:5432/sovd_db
REDIS_URL=redis://redis:6379/0
```

If incorrect, update `.env` and restart services.

**Solution 4: Database/Redis Out of Memory**

Check resource usage:
```bash
# Database
docker stats db --no-stream

# Redis
docker stats redis --no-stream
```

If memory usage is high (>90%), increase memory limits in `docker-compose.yml`:
```yaml
services:
  db:
    mem_limit: 1g  # Increase from 512m
  redis:
    mem_limit: 512m  # Increase from 256m
```

Restart services after changes.

#### Verification

```bash
curl http://localhost:8000/health/ready
# Should return: {"status": "healthy", "database": "connected", "redis": "connected"}
```

---

### Issue 6: Port Conflicts Preventing Startup

**Symptoms**:
- Error: "Bind for 0.0.0.0:8000 failed: port is already allocated"
- Docker Compose fails to start services
- Specific port (5432, 6379, 8000, 5173) already in use

#### Root Cause
Another process is using the required port.

#### Diagnosis

**Step 1**: Identify which process is using the port:
```bash
# Check port 8000 (backend)
lsof -i :8000

# Check port 5432 (database)
lsof -i :5432

# Check port 6379 (Redis)
lsof -i :6379

# Check port 5173 (frontend)
lsof -i :5173
```

Output shows:
```
COMMAND   PID   USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
postgres  1234  user   5u   IPv4  0x...      0t0  TCP *:5432 (LISTEN)
```

#### Solution

**Solution 1: Stop the Conflicting Process**

```bash
# Kill the process using the port
kill <PID>

# Or force kill if necessary
kill -9 <PID>

# Restart Docker Compose
docker-compose up -d
```

**Solution 2: Change Port Mapping**

If you need to keep the existing process running, change the port in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Change from 8000:8000

  db:
    ports:
      - "5433:5432"  # Change from 5432:5432

  redis:
    ports:
      - "6380:6379"  # Change from 6379:6379

  frontend:
    ports:
      - "5174:5173"  # Change from 5173:5173
```

**Important**: If you change ports, update:
- `.env` file: `DATABASE_URL`, `REDIS_URL`
- `frontend/.env`: `VITE_API_BASE_URL`

**Solution 3: Stop All Docker Containers**

If uncertain which containers are causing conflicts:
```bash
docker stop $(docker ps -aq)
docker-compose up -d
```

#### Verification

```bash
# Check all services are running
docker-compose ps

# Test each service
curl http://localhost:8000/health/ready  # Backend
curl http://localhost:5173  # Frontend
```

---

### Issue 7: Database Connection Errors

**Symptoms**:
- Error: "could not connect to server: Connection refused"
- Error: "FATAL: password authentication failed for user"
- Error: "FATAL: database 'sovd_db' does not exist"

#### Root Cause
Database credentials are incorrect, database service is down, or database doesn't exist.

#### Diagnosis

**Step 1**: Check database service status:
```bash
docker-compose ps db
```

**Step 2**: Check database logs:
```bash
docker-compose logs db | tail -50
```

Look for errors like:
```
FATAL: password authentication failed for user "sovd_user"
```

**Step 3**: Verify database connection string:
```bash
docker-compose exec backend env | grep DATABASE_URL
```

#### Solution

**Solution 1: Database Service Not Running**

```bash
docker-compose up -d db
sleep 10
docker-compose restart backend
```

**Solution 2: Incorrect Credentials**

Check `.env` file:
```bash
cat .env | grep -E "(POSTGRES_USER|POSTGRES_PASSWORD|DATABASE_URL)"
```

Ensure credentials match:
- `POSTGRES_USER=sovd_user`
- `POSTGRES_PASSWORD=sovd_password`
- `DATABASE_URL=postgresql://sovd_user:sovd_password@db:5432/sovd_db`

If incorrect, fix and restart:
```bash
docker-compose down
docker-compose up -d
```

**Solution 3: Database Doesn't Exist**

Create the database:
```bash
docker-compose exec db psql -U sovd_user -c "CREATE DATABASE sovd_db;"
```

Then run initialization script:
```bash
docker-compose exec backend /bin/bash -c "cd /app && bash /app/scripts/init_db.sh"
```

**Solution 4: Database Connection Pool Exhausted**

Check for connection leaks:
```bash
docker-compose exec db psql -U sovd_user -d sovd_db -c "
SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';
"
```

If many idle connections (>50), restart backend to reset pool:
```bash
docker-compose restart backend
```

#### Verification

```bash
# Test database connectivity
docker-compose exec backend python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
conn = engine.connect()
print('Database connected')
conn.close()
"
```

---

### Issue 8: Redis Connection Failures

**Symptoms**:
- Error: "Error connecting to Redis: Connection refused"
- Sessions not persisting (user logged out after refresh)
- WebSocket not receiving updates

#### Root Cause
Redis service is down or connection URL is incorrect.

#### Diagnosis

**Step 1**: Check Redis service:
```bash
docker-compose ps redis
```

**Step 2**: Test Redis connectivity:
```bash
docker-compose exec redis redis-cli ping
# Should return "PONG"
```

**Step 3**: Check Redis URL configuration:
```bash
docker-compose exec backend env | grep REDIS_URL
```

Expected: `redis://redis:6379/0`

#### Solution

**Solution 1: Redis Not Running**

```bash
docker-compose up -d redis
docker-compose restart backend
```

**Solution 2: Incorrect Redis URL**

Update `.env` file:
```env
REDIS_URL=redis://redis:6379/0
```

Restart services:
```bash
docker-compose restart backend
```

**Solution 3: Redis Out of Memory**

Check Redis memory:
```bash
docker-compose exec redis redis-cli INFO memory | grep used_memory_human
```

If usage is high, increase memory limit in `docker-compose.yml`:
```yaml
services:
  redis:
    mem_limit: 512m  # Increase from 256m
```

Or clear Redis cache:
```bash
docker-compose exec redis redis-cli FLUSHALL
```

**Warning**: `FLUSHALL` will log out all users.

**Solution 4: Redis Persistence Issues**

If Redis data is not persisting across restarts, check volume:
```bash
docker volume ls | grep redis
```

Ensure volume exists. If not, recreate:
```bash
docker-compose down
docker volume create sovd_redis_data
docker-compose up -d
```

#### Verification

```bash
# Test Redis connectivity from backend
docker-compose exec backend python -c "
import redis
r = redis.from_url('redis://redis:6379/0')
r.set('test', 'value')
print('Redis set:', r.get('test'))
"
```

---

## Advanced Diagnostics

### Using Correlation IDs for Debugging

When errors occur, the response includes a `correlation_id`. Use this to trace the request through logs:

**Example Error Response**:
```json
{
  "detail": "Internal server error",
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "correlation_id": "abc123-def456-ghi789"
  }
}
```

**Search logs for this correlation ID**:
```bash
docker-compose logs backend | grep "abc123-def456-ghi789"
```

This will show all log entries related to this specific request.

### Checking Prometheus Metrics

Access Prometheus at http://localhost:9090 and run queries:

```promql
# Error rate (last 5 minutes)
rate(commands_executed_total{status="failed"}[5m])

# P95 latency
histogram_quantile(0.95, rate(command_execution_duration_seconds_bucket[5m]))

# Active WebSocket connections
websocket_connections_active

# Active vehicle connections
vehicle_connections_active
```

### Database Query Performance

If the application is slow, check for slow queries:

```bash
docker-compose exec db psql -U sovd_user -d sovd_db

# Show slow queries (>1 second)
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '1 second'
ORDER BY duration DESC;

# Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Network Connectivity Tests

Test connectivity between services:

```bash
# Backend to database
docker-compose exec backend ping db

# Backend to Redis
docker-compose exec backend ping redis

# Frontend to backend (from host)
curl http://localhost:8000/health/live
```

---

## Escalation Procedures

If you cannot resolve an issue using this runbook:

### Level 1: Team Lead
- **Contact**: team-lead@yourdomain.com
- **Slack**: #sovd-support
- **When**: After 30 minutes of troubleshooting

### Level 2: DevOps Engineer
- **Contact**: devops@yourdomain.com
- **PagerDuty**: On-call rotation
- **When**: Production issues, service outages

### Level 3: Engineering Manager
- **Contact**: eng-manager@yourdomain.com
- **When**: Critical outages lasting >1 hour

### Incident Report Template

When escalating, include:

```
Subject: [SOVD] <Brief description>

Severity: [P1-Critical / P2-High / P3-Medium / P4-Low]
Environment: [Local / Staging / Production]
Started: [Timestamp]

Symptoms:
- <What is broken?>
- <What are users experiencing?>

Steps Taken:
1. <What have you tried?>
2. <What was the result?>

Current Status:
- <Is service up/down?>
- <Workaround in place?>

Logs/Screenshots:
- <Attach relevant logs>
- <Include correlation IDs>
```

---

## Additional Resources

- **Deployment Guide**: [deployment.md](deployment.md)
- **Monitoring Guide**: [monitoring.md](monitoring.md)
- **Disaster Recovery**: [disaster_recovery.md](disaster_recovery.md)
- **User Guide**: [../user-guides/engineer_guide.md](../user-guides/engineer_guide.md)
- **Architecture Docs**: `.codemachine/artifacts/architecture/`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Owner**: Platform Engineering Team
