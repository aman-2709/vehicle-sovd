# SOVD Command WebApp - Test User Guide

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Ports available: 3000 (frontend), 8000 (backend), 5433 (database), 6380 (redis)

### Starting the Application

```bash
# 1. Navigate to project root
cd /home/aman/dev/personal-projects/sovd

# 2. Start all services
docker compose up -d

# 3. Wait for services to be healthy (~30 seconds)
docker compose ps

# 4. Verify all services are running
# Expected: backend (healthy), frontend (healthy/unhealthy is ok), db (healthy), redis (healthy)
```

### Stopping the Application

```bash
# Stop all services
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v
```

## Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | React web application |
| **Backend API** | http://localhost:8000 | FastAPI REST API |
| **API Documentation** | http://localhost:8000/docs | Interactive Swagger UI |
| **Health Check** | http://localhost:8000/health/ready | Service health status |
| **Metrics** | http://localhost:8000/metrics | Prometheus metrics |
| **Prometheus** | http://localhost:9090 | Metrics monitoring |

## Test Credentials

### User Accounts

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| `admin` | `admin123` | admin | Full access to all features |
| `engineer` | `engineer123` | engineer | Standard user access |

### Test Vehicles

| VIN | Make/Model | Year | Status |
|-----|------------|------|--------|
| `TESTVIN0000000001` | Tesla Model 3 | 2023 | Connected |
| `TESTVIN0000000002` | BMW X5 | 2022 | Disconnected |

## Testing Workflows

### 1. Test API Health Check

```bash
# Check backend health
curl http://localhost:8000/health/ready

# Expected output:
# {
#   "status": "ready",
#   "checks": {
#     "database": "ok",
#     "redis": "ok"
#   }
# }
```

### 2. Test Authentication (API)

**Note**: Currently there's a known bcrypt compatibility issue. Use the following workaround:

```bash
# Attempt login (currently failing due to bcrypt issue)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Expected (when fixed):
# {
#   "access_token": "eyJ...",
#   "refresh_token": "eyJ...",
#   "token_type": "bearer",
#   "user": {
#     "user_id": "...",
#     "username": "admin",
#     "email": "admin@sovd.example.com",
#     "role": "admin"
#   }
# }
```

**Workaround for testing authenticated endpoints**:
```bash
# For now, test authentication protection works
curl http://localhost:8000/api/v1/vehicles

# Expected: 403 Forbidden with authentication error
```

### 3. Test Frontend Application

```bash
# Open in browser
xdg-open http://localhost:3000  # Linux
# or
open http://localhost:3000      # macOS

# Manual testing steps:
# 1. Navigate to http://localhost:3000
# 2. You should see the login page
# 3. Enter credentials: admin / admin123
# 4. (Currently blocked by auth issue - UI will load but login won't work)
```

### 4. Test Database Access

```bash
# Connect to PostgreSQL
PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd

# Inside psql, run:
# List tables
\dt

# View users
SELECT username, role, is_active FROM users;

# View vehicles
SELECT vin, make, model, connection_status FROM vehicles;

# Exit
\q
```

### 5. Test API Documentation

```bash
# Open Swagger UI in browser
xdg-open http://localhost:8000/docs  # Linux
# or
open http://localhost:8000/docs      # macOS

# Interactive testing:
# 1. Navigate to http://localhost:8000/docs
# 2. Expand any endpoint (e.g., GET /api/v1/vehicles)
# 3. Click "Try it out"
# 4. Click "Execute"
# 5. View response (will show 403 if authentication required)
```

### 6. Test SOVD Commands (When Authentication Fixed)

Once authentication is working, you can test SOVD protocol commands:

#### 6.1. List Vehicles
```bash
# Get authentication token first (when fixed)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r '.access_token')

# List all vehicles
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/vehicles

# Expected:
# [
#   {
#     "vehicle_id": "...",
#     "vin": "TESTVIN0000000001",
#     "make": "Tesla",
#     "model": "Model 3",
#     "year": 2023,
#     "connection_status": "connected"
#   },
#   ...
# ]
```

#### 6.2. Submit SOVD Command
```bash
# Submit a Read DTC command
curl -X POST http://localhost:8000/api/v1/commands \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "TESTVIN0000000001",
    "command_type": "read_dtc",
    "params": {
      "ecu_address": "0x10"
    }
  }'

# Expected:
# {
#   "command_id": "...",
#   "status": "pending",
#   "vehicle_id": "TESTVIN0000000001",
#   "command_type": "read_dtc",
#   "created_at": "..."
# }
```

#### 6.3. Check Command Status
```bash
# Get command history
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/commands?vehicle_id=TESTVIN0000000001"

# Get specific command
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/commands/{command_id}
```

#### 6.4. WebSocket Real-Time Updates
```javascript
// In browser console or Node.js:
const token = "YOUR_ACCESS_TOKEN";
const commandId = "YOUR_COMMAND_ID";

const ws = new WebSocket(`ws://localhost:8000/ws/responses/${commandId}?token=${token}`);

ws.onmessage = (event) => {
  console.log('Received:', JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

## Testing with Docker Logs

### View Service Logs

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# View last 50 lines
docker compose logs --tail=50 backend

# Search logs for errors
docker compose logs backend | grep -i error
```

## Running Test Suites

### Backend Tests

```bash
# All backend tests
cd backend
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage report
pytest --cov=app --cov-report=html
# Open coverage report: backend/htmlcov/index.html

# Specific test file
pytest tests/unit/test_auth_service.py -v

# Single test
pytest tests/unit/test_auth_service.py::TestPasswordHashing::test_verify_password_correct -v
```

### Frontend Tests

```bash
cd frontend

# Run all tests
npm run test

# Run with coverage
npm run test:coverage
# Open coverage report: frontend/coverage/index.html

# Run specific test file
npm run test -- LoginPage.test.tsx

# Watch mode (interactive)
npm run test
```

### End-to-End Tests

```bash
# From project root
make e2e

# This will:
# 1. Start all Docker services
# 2. Wait for services to be ready
# 3. Run Playwright E2E tests
# 4. Stop services
# 5. Show test results
```

## Monitoring and Metrics

### Prometheus Metrics

```bash
# Open Prometheus UI
xdg-open http://localhost:9090

# Example queries in Prometheus UI:
# - http_requests_total
# - http_request_duration_seconds
# - db_connection_pool_size
# - redis_commands_total
```

### Health Monitoring

```bash
# Check service health
curl http://localhost:8000/health/live   # Liveness probe
curl http://localhost:8000/health/ready  # Readiness probe

# Monitor continuously
watch -n 2 'curl -s http://localhost:8000/health/ready | jq'
```

## Database Management

### View Database Contents

```bash
# Connect to database
PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd

# Useful queries:
-- View all tables
\dt

-- Count records
SELECT 'users' as table, COUNT(*) FROM users
UNION ALL
SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL
SELECT 'commands', COUNT(*) FROM commands
UNION ALL
SELECT 'responses', COUNT(*) FROM responses;

-- Recent commands
SELECT command_id, command_type, status, created_at
FROM commands
ORDER BY created_at DESC
LIMIT 10;

-- Audit log
SELECT event_type, user_id, details, created_at
FROM audit_logs
ORDER BY created_at DESC
LIMIT 10;
```

### Reset Database

```bash
# Option 1: Drop and recreate (inside psql)
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO sovd_user;

# Option 2: Run init script again
POSTGRES_PASSWORD=sovd_pass POSTGRES_PORT=5433 POSTGRES_USER=sovd_user ./scripts/init_db.sh

# Option 3: Full reset with Docker
docker compose down -v  # Remove volumes
docker compose up -d
# Then run init_db.sh
```

## Troubleshooting

### Services Not Starting

```bash
# Check service status
docker compose ps

# View logs for failed service
docker compose logs [service_name]

# Restart specific service
docker compose restart backend

# Rebuild and restart
docker compose up -d --build backend
```

### Port Conflicts

```bash
# Check if ports are in use
sudo netstat -tlnp | grep -E "3000|8000|5433|6380"

# Change ports in docker-compose.yml if needed
# Example: Change frontend port from 3000 to 3001
#   ports:
#     - "3001:3000"
```

### Database Connection Issues

```bash
# Verify database is accessible
PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd -c "SELECT 1"

# Check backend can connect
docker compose logs backend | grep -i "database"

# Verify DATABASE_URL in backend container
docker compose exec backend env | grep DATABASE_URL
```

### Authentication Issues (Current Known Issue)

**Known Issue**: bcrypt password verification fails due to library compatibility.

**Symptoms**:
- Login returns 500 Internal Server Error
- Backend logs show: "ValueError: password cannot be longer than 72 bytes"

**Status**: Under investigation

**Workaround for testing**:
- Unit tests use mocked authentication (working)
- Integration tests mock the auth layer
- Direct database queries work
- All other endpoints function correctly when authentication is bypassed

### Frontend Not Loading

```bash
# Check frontend logs
docker compose logs frontend

# Verify frontend is serving
curl http://localhost:3000

# Rebuild frontend
docker compose up -d --build frontend

# Check for build errors
docker compose exec frontend npm run build
```

## Performance Testing

### Load Testing with Apache Bench

```bash
# Install Apache Bench
sudo apt-get install apache2-utils  # Ubuntu/Debian

# Test health endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health/ready

# Test API endpoint with authentication (when working)
ab -n 100 -c 10 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/vehicles
```

### Database Performance

```bash
# Inside psql
EXPLAIN ANALYZE SELECT * FROM commands WHERE vehicle_id = 'some-uuid';

# Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

## Security Testing

### Test Authentication Protection

```bash
# Test protected endpoint without token
curl http://localhost:8000/api/v1/vehicles
# Expected: 403 Forbidden

# Test with invalid token
curl -H "Authorization: Bearer invalid_token" \
  http://localhost:8000/api/v1/vehicles
# Expected: 403 Forbidden

# Test rate limiting
for i in {1..20}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "wrong"}';
done
# Should see 429 Too Many Requests after ~10 attempts
```

### Check Security Headers

```bash
curl -I http://localhost:8000/docs

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# Content-Security-Policy: ...
```

## API Testing Examples

### Complete API Test Flow (When Auth Fixed)

```bash
# 1. Login
LOGIN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

# 2. Get vehicles
curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/vehicles | jq

# 3. Submit command
COMMAND_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/commands \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "TESTVIN0000000001",
    "command_type": "read_dtc",
    "params": {"ecu_address": "0x10"}
  }')

COMMAND_ID=$(echo $COMMAND_RESPONSE | jq -r '.command_id')

# 4. Check command status
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/commands/$COMMAND_ID" | jq

# 5. Get command history
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/commands?status=pending" | jq
```

## Cleanup

### Remove All Data

```bash
# Stop and remove containers, volumes, networks
docker compose down -v

# Remove images
docker rmi sovd-backend sovd-frontend

# Remove all unused Docker resources
docker system prune -a --volumes
```

## Next Steps

1. **Fix Authentication**: The bcrypt compatibility issue needs resolution for full functionality
2. **Test WebSocket**: Real-time command responses via WebSocket
3. **Test gRPC**: Vehicle connector integration (currently has test failures)
4. **Load Testing**: Performance under concurrent users
5. **Security Audit**: Comprehensive security testing

## Support

For issues or questions:
- Check logs: `docker compose logs [service]`
- Review backend errors: `docker logs sovd-backend --tail 100`
- Database queries: Connect via psql for data inspection
- API documentation: http://localhost:8000/docs

## Common Commands Cheat Sheet

```bash
# Start everything
docker compose up -d

# Stop everything
docker compose down

# View logs
docker compose logs -f backend

# Check status
docker compose ps

# Restart service
docker compose restart backend

# Rebuild service
docker compose up -d --build backend

# Run tests
cd backend && pytest
cd frontend && npm run test

# Database access
PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd

# Health check
curl http://localhost:8000/health/ready

# View metrics
curl http://localhost:8000/metrics
```
